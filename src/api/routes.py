import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database_store.database_client import DatabaseClient

router = APIRouter()

# Locate templates relative to this file
templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    """Serve the subscription UI"""
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"success": None, "message": None}
    )

@router.post("/subscribe", response_class=HTMLResponse)
async def subscribe(
    request: Request, 
    email: str = Form(...), 
    preferred_time: str = Form(...),
    full_name: str = Form(...),
    occupation: str = Form(...),
    industry: Optional[str] = Form(None),
    reason: Optional[str] = Form(None)
):
    """Handle form submission and save to the database securely"""
    db = DatabaseClient()
    success = db.add_subscriber(
        email=email, 
        preferred_time=preferred_time,
        full_name=full_name,
        occupation=occupation,
        industry=industry,
        reason=reason
    )
    
    if success:
        message = f"Successfully subscribed! You will receive the PowerSyncNerd at {preferred_time}."
    else:
        message = "Failed to subscribe. Please try again or verify your email."
        
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"success": success, "message": message}
    )

@router.get("/health")
async def health_check():
    """Render port monitoring endpoint"""
    return {"status": "ok", "service": "powersyncnerd-api"}

@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(request: Request, email: Optional[str] = None):
    """Serve a basic unsubscribe confirmation page"""
    return templates.TemplateResponse(
        request=request,
        name="unsubscribe.html",
        context={"request": request, "email": email, "success": None}
    )

@router.post("/unsubscribe", response_class=HTMLResponse)
async def handle_unsubscribe(
    request: Request, 
    email: str = Form(...),
    unsub_reason: Optional[str] = Form(None)
):
    """Handle the actual deactivation request with optional feedback"""
    logger = logging.getLogger("powersyncnerd_unsubscribe")
    db = DatabaseClient()
    success = db.unsubscribe(email)
    
    if success and unsub_reason:
        logger.info(f"😢 Unsubscribe Feedback from {email}: {unsub_reason}")
    
    message = "You have been successfully unsubscribed." if success else "We couldn't find that email address."
    return templates.TemplateResponse(
        request=request,
        name="unsubscribe.html",
        context={"request": request, "email": email, "success": success, "message": message}
    )

@router.post("/trigger-digest")
async def trigger_digest(time: str, secret: str, background_tasks: BackgroundTasks):
    """Secure endpoint triggered remotely by cron-job.org or GitHub Actions"""
    logger = logging.getLogger("powersyncnerd_webhook")
    EXPECTED_SECRET = os.getenv("CRON_SECRET_TOKEN", "powersyncnerd_secure_123")
    
    if secret != EXPECTED_SECRET:
        logger.warning("Attempted unauthorized pipeline trigger!")
        raise HTTPException(status_code=403, detail="Unauthorized cron secret")
    
    if time not in ['8am', '6pm']:
        raise HTTPException(status_code=400, detail="Invalid trigger time. Expected '8am' or '6pm'")
        
    logger.info(f"🚀 Authorized webhook received! Triggering background pipeline for {time}")
    
    # Imported dynamically to avoid circular imports if any, and execute fully in the background
    from main import run_digest_pipeline
    background_tasks.add_task(run_digest_pipeline, trigger_time=time)
    
    return {"status": "accepted", "message": f"Pipeline processing started for {time}"}
