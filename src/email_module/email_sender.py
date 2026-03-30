import os
import sys
import logging
import resend
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add relative imports to path if needed
sys.path.append(os.path.join(os.getcwd()))

from src.email_module.email_format import format_email_html, format_plain_text

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger("email_sender")

def get_email_config() -> dict:
    """Load email configuration from environment variables"""
    return {
        'resend_api_key': os.getenv('RESEND_API_KEY'),
        'sender_email': os.getenv('SENDER_EMAIL', 'onboarding@resend.dev'),
        'sender_name': os.getenv('SENDER_NAME', 'PowerSync Nerd'),
        'base_url': os.getenv('APP_BASE_URL', 'http://localhost:10000')
    }

def send_digest_email(
    summaries: List[Dict], 
    trigger_time: str = '8am'
) -> bool:
    """
    Main entry point for main.py. 
    Formats summaries and sends them via Resend API.
    """
    if not summaries:
        logger.warning("📪 No summaries to send.")
        return True

    # Generate template HTML and Plain Text
    html_template = format_email_html(summaries)
    plain_template = format_plain_text(summaries)
    
    # Use the existing logic to send to recipients
    return send_email_smtp(
        html_content=html_template,
        plain_text=plain_template,
        subject=f"⚡ PowerSyncNerd News Digest - {len(summaries)} Articles",
        trigger_time=trigger_time
    )

def send_email_smtp(
    html_content: str, 
    plain_text: str = "", 
    subject: str = "PowerSyncNerd News Digest",
    recipients: List[Any] = None,
    trigger_time: str = '8am'
) -> bool:
    """
    Lower-level sender using Resend API (HTTP Port 443).
    Bypasses cloud blocks and handles personalization.
    """
    config = get_email_config()
    resend_key = config.get('resend_api_key')
    
    if not resend_key:
        logger.error("❌ RESEND_API_KEY missing from .env")
        return False

    # Initialize Resend
    resend.api_key = resend_key
    
    # If no recipients provided, fetch from DB
    if recipients is None:
        try:
            from src.database_store.database_client import DatabaseClient
            db = DatabaseClient()
            recipients = db.get_active_subscribers(trigger_time)
            logger.info(f"📋 Found {len(recipients)} active subscribers for {trigger_time}")
        except Exception as e:
            logger.error(f"❌ Could not fetch subscribers from DB: {e}")
            return False

    if not recipients:
        logger.warning("📪 No recipients to send to.")
        return True

    # 🛡️ SANDBOX GUARD: If using Resend onboarding, ONLY send to YOU (to avoid API errors)
    is_sandbox = config.get('sender_email') == 'onboarding@resend.dev'
    if is_sandbox:
        logger.info("🛡️ Sandbox Guard Active: Restricting delivery to your verified account only.")

    success_count = 0
    
    for recipient_data in recipients:
        try:
            if isinstance(recipient_data, str):
                recipient_email = recipient_data.strip()
                recipient_name = "Reader"
            else:
                # Handle dictionary from DB
                recipient_email = recipient_data.get('email', '').strip()
                recipient_name = recipient_data.get('full_name', 'Reader').strip().split()[0] # Just first name

            if not recipient_email:
                continue
            
            # If in sandbox, reject anything that isn't YOUR verified gmail
            if is_sandbox and recipient_email != "powersyncnerd@gmail.com":
                logger.warning(f"⏩ Skipping {recipient_email} (Sandbox Limit: Can only send to yourself)")
                continue

            # Personalize
            unsubscribe_url = f"{config['base_url']}/unsubscribe?email={recipient_email}"
            personalized_html = html_content.replace('%%SUBSCRIBER_NAME%%', recipient_name).replace('%%UNSUBSCRIBE_URL%%', unsubscribe_url)
            personalized_plain = plain_text.replace('%%SUBSCRIBER_NAME%%', recipient_name).replace('%%UNSUBSCRIBE_URL%%', unsubscribe_url)
            
            logger.info(f"📨 Sending to: {recipient_email}...")

            # API Call
            params: resend.Emails.SendEmailParameters = {
                "from": f"{config['sender_name']} <{config['sender_email']}>",
                "to": [recipient_email],
                "subject": subject,
                "html": personalized_html,
                "text": personalized_plain,
            }

            response = resend.Emails.send(params)
            logger.info(f"✅ Sent ID: {response.get('id')}")
            success_count += 1

        except Exception as e:
            logger.error(f"❌ Resend Error for {recipient_email}: {e}")

    logger.info(f"📊 Results: {success_count}/{len(recipients)} emails sent.")
    return success_count > 0

def test_email_connection():
    """Diagnostic for Resend"""
    config = get_email_config()
    print(f"\n🔍 Checking Resend Setup...")
    if not config['resend_api_key']:
        print("❌ ERROR: RESEND_API_KEY missing")
        return False
    print("✅ Configuration ready. Run test_resend.py to verify delivery.")
    return True