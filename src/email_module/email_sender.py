import os
import sys
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from dotenv import load_dotenv

# Import formatter
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from email_module.email_format import format_email_html, format_plain_text
from src.database_store.database_client import DatabaseClient

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("email_sender")


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

def get_email_config() -> dict:
    """Load email configuration from environment variables"""
    return {
        'smtp_host': os.getenv('SMTP_HOST'),
        'smtp_port': int(os.getenv('SMTP_PORT')),
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD'),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_name': os.getenv('SENDER_NAME'),
        'base_url': os.getenv('APP_BASE_URL', 'http://localhost:10000')
    }


# =============================================================================
# EMAIL SENDING FUNCTIONS
# =============================================================================

def create_email_message(
    html_content: str,
    plain_text: str,
    subject: str,
    sender_email: str,
    sender_name: str,
    recipient_email: str
) -> MIMEMultipart:
    """
    Create email message with HTML and plain text alternatives
    
    Args:
        html_content: HTML email content
        plain_text: Plain text fallback
        subject: Email subject line
        sender_email: Sender email address
        sender_name: Sender display name
        recipient_email: Recipient email address
    
    Returns:
        MIMEMultipart message object
    """
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = recipient_email
    
    # Add plain text version (fallback)
    text_part = MIMEText(plain_text, 'plain')
    message.attach(text_part)
    
    # Add HTML version (preferred)
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)
    
    return message


def send_email_smtp(
    html_content: str,
    plain_text: str = None,
    subject: str = None,
    recipients: List[str] = None,
    trigger_time: str = None
) -> bool:
    """
    Send email digest via SMTP
    
    Args:
        html_content: HTML email content
        plain_text: Plain text fallback (optional, will use simple version if None)
        subject: Email subject (optional, auto-generated if None)
        recipients: List of recipient dictionaries (optional, uses .env if None)
    
    Returns:
        True if successful, False otherwise
    """
    # Load configuration
    config = get_email_config()
    
    # Validate configuration
    if not config['username'] or not config['password']:
        logger.error("❌ SMTP credentials not configured in .env")
        return False
    
    if not config['sender_email']:
        logger.error("❌ Sender email not configured in .env")
        return False
    
    # Use provided recipients or fetch from database
    if recipients is None:
        try:
            db = DatabaseClient()
            recipients = db.get_active_subscribers(trigger_time)
        except Exception as e:
            logger.error(f"❌ Failed to fetch subscribers from DB: {e}")
            recipients = []
    
    if not recipients:
        logger.error("❌ No active recipients found for this trigger time.")
        return False
    
    # Generate default subject if not provided
    if subject is None:
        from datetime import datetime
        subject = f"⚡ PowerSyncNerd News Digest - {datetime.now().strftime('%B %d, %Y')}"
    
    # Generate plain text fallback if not provided
    if plain_text is None:
        plain_text = "Please view this email in an HTML-capable email client for the best experience."
    
    logger.info("=" * 60)
    logger.info("📧 SENDING EMAIL DIGEST")
    logger.info("=" * 60)
    logger.info(f"📤 From: {config['sender_name']} <{config['sender_email']}>")
    logger.info(f"📥 To: {len(recipients)} recipients")
    logger.info(f"📋 Subject: {subject}")
    
    # Send to each recipient
    successful_sends = 0
    failed_sends = 0

    try:
        # Connect to SMTP server using SSL (Verified working on port 465)
        logger.info(f"🔌 Connecting to {config['smtp_host']}:{config['smtp_port']} (SSL Mode)...")
        
        with smtplib.SMTP_SSL(config['smtp_host'], config['smtp_port']) as server:
            # Login (SSL doesn't need starttls)
            logger.info("🔐 Authenticating...")
            server.login(config['username'], config['password'])
            logger.info("✅ Authentication successful")
            
            # Send to each recipient dict
            for recipient_data in recipients:
                if isinstance(recipient_data, str):
                    # Fallback for manual string testing
                    recipient_email = recipient_data.strip()
                    recipient_name = "Reader"
                else:
                    recipient_email = recipient_data.get('email', '').strip()
                    recipient_name = recipient_data.get('full_name', 'Reader').strip().split()[0]  # Just First Name
                
                if not recipient_email:
                    continue
                
                # Replace personalized tokens
                unsubscribe_url = f"{config['base_url']}/unsubscribe?email={recipient_email}"
                personalized_html = html_content.replace('%%SUBSCRIBER_NAME%%', recipient_name).replace('%%UNSUBSCRIBE_URL%%', unsubscribe_url)
                personalized_text = plain_text.replace('%%SUBSCRIBER_NAME%%', recipient_name).replace('%%UNSUBSCRIBE_URL%%', unsubscribe_url)
                
                try:
                    logger.info(f"\n📨 Sending to: {recipient_email} (Name: {recipient_name})")
                    
                    # Create message
                    message = create_email_message(
                        html_content=personalized_html,
                        plain_text=personalized_text,
                        subject=subject,
                        sender_email=config['sender_email'],
                        sender_name=config['sender_name'],
                        recipient_email=recipient_email
                    )
                    
                    # Send
                    server.send_message(message)
                    successful_sends += 1
                    logger.info(f"✅ Sent successfully to {recipient_email}")
                    
                except Exception as e:
                    failed_sends += 1
                    logger.error(f"❌ Failed to send to {recipient}: {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 EMAIL SENDING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {successful_sends}")
        logger.info(f"❌ Failed: {failed_sends}")
        logger.info(f"📧 Total: {len(recipients)}")
        
        return successful_sends > 0
        
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD in .env")
        return False
    
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP error: {e}")
        return False
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def send_digest_email(summaries: List[dict], trigger_time: str = None) -> bool:
    """
    Complete workflow: Format summaries and send email
    
    Args:
        summaries: List of article summaries from summarizer
        trigger_time: '8am', '6pm' or None to fetch relevant subscribers
    
    Returns:
        True if successful, False otherwise
    """
    
    
    if not summaries:
        logger.warning("⚠️ No summaries to send")
        return False
    
    logger.info(f"📝 Formatting {len(summaries)} articles for email...")
    
    # Format email
    html_content = format_email_html(summaries)
    plain_text = format_plain_text(summaries)
    
    # Send
    return send_email_smtp(
        html_content=html_content,
        plain_text=plain_text,
        trigger_time=trigger_time
    )


def test_email_connection() -> bool:
    """
    Test SMTP connection and authentication
    
    Returns:
        True if connection successful, False otherwise
    """
    config = get_email_config()
    
    logger.info("🧪 Testing SMTP connection...")
    logger.info(f"   Host: {config['smtp_host']}")
    logger.info(f"   Port: {config['smtp_port']}")
    logger.info(f"   Username: {config['username']}")
    
    try:
        with smtplib.SMTP_SSL(config['smtp_host'], config['smtp_port'], timeout=10) as server:
            server.login(config['username'], config['password'])
            
        logger.info("✅ SMTP connection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ SMTP connection failed: {e}")
        return False


# =============================================================================
# MAIN EXECUTION (FOR TESTING)
# =============================================================================

def main():
    """Test email sender with sample data"""
    print("\n📧 PowerSyncNerd Email Sender Test")
    print("=" * 60)
    
    # Test connection first
    if not test_email_connection():
        print("\n❌ Connection test failed. Check your .env configuration.")
        return
    
    print("\n✅ Connection test passed!")
    
    # Create test email
    print("\n📨 Sending test email...")
    
    # Sample summaries
    test_summaries = [
        {
            'title': 'Test Article: PowerSyncNerd Email System',
            'summary': 'This is a test email from PowerSyncNerd to verify that the email sending system is working correctly.',
            'impact': 'HIGH',
            'source': 'PowerSyncNerd System',
            'author': 'System Test',
            'published_date': 'Today',
            'url': 'https://powersyncnerd.onrender.com'
        }
    ]
    
    # Send test digest
    success = send_digest_email(test_summaries)
    
    if success:
        print("\n✅ Test email sent successfully!")
        print("📥 Check your inbox for the test email.")
    else:
        print("\n❌ Failed to send test email.")
        print("📋 Check the logs above for error details.")


if __name__ == "__main__":
    main()