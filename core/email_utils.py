import os
import base64
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

def send_html_email(subject, template_name, context, recipient_list, fail_silently=False):
    """
    Send HTML email with embedded logo
    """
    try:
        # Get the logo path
        logo_path = os.path.join(settings.BASE_DIR, 'safecall', 'static', 'LOGOS', 'gpttlogo.png')
        if not os.path.exists(logo_path):
            # Try alternative locations
            alt_paths = [
                os.path.join(settings.BASE_DIR, 'safecall', 'staticfiles', 'LOGOS', 'gpttlogo.png'),
                os.path.join(settings.BASE_DIR, 'static', 'LOGOS', 'gpttlogo.png'),
                os.path.join(settings.BASE_DIR, 'staticfiles', 'LOGOS', 'gpttlogo.png')
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
        
        # If logo exists, compress and embed it
        if os.path.exists(logo_path):
            try:
                # Try to import PIL for image compression
                from PIL import Image
                from io import BytesIO
                
                # Process the image for background use - make it larger and lighter
                img = Image.open(logo_path)
                # Make it larger for background use
                img = img.resize((200, 200), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
                
                # Convert to RGB if it's RGBA
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Make the image lighter for background use
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.5)  # Make it 50% brighter
                
                # Lower opacity by adding a white overlay
                overlay = Image.new('RGB', img.size, (255, 255, 255))
                img = Image.blend(img, overlay, 0.3)  # 70% original, 30% white
                
                buffer = BytesIO()
                img.save(buffer, format="PNG", optimize=True)
                logo_data = buffer.getvalue()
                
                # Encode the logo
                logo_base64 = base64.b64encode(logo_data).decode()
                
                # Add to context as data URI
                context['logo_image'] = f'data:image/png;base64,{logo_base64}'
            except (ImportError, Exception) as e:
                # If PIL fails, use direct file reading but still try to keep size small
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode()
                context['logo_image'] = f'data:image/png;base64,{logo_base64}'
        else:
            # Use placeholder if logo not found
            context['logo_image'] = 'https://via.placeholder.com/60x60?text=SC'
        
        # Render email templates
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        # Use simple send_mail for better compatibility
        return send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=fail_silently
        )
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        if not fail_silently:
            raise

def send_donation_invoice(donor_name, donor_email, amount, order_id, transaction_id, payment_method, status, transaction_fee=None, receipt_url=None):
    """
    Send a donation invoice email to the donor.
    
    Args:
        donor_name (str): The name of the donor
        donor_email (str): The email address of the donor
        amount (float): The donation amount
        order_id (str): The Razorpay order ID
        transaction_id (str): The Razorpay payment ID
        payment_method (str): The payment method used
        status (str): 'Success' or 'Failed'
        transaction_fee (float, optional): Any transaction fee applied
        receipt_url (str, optional): URL to view the receipt online
    """
    try:
        # Set the subject based on status
        if status.lower() == 'success':
            subject = f"Thank You for Your Donation to SafeCall - Receipt #{order_id}"
        else:
            subject = f"SafeCall Donation Payment {status} - #{order_id}"
        
        # Calculate total amount
        total_amount = amount
        if transaction_fee:
            total_amount += transaction_fee
        
        # Prepare context for email template
        context = {
            'donor_name': donor_name,
            'amount': amount,
            'order_id': order_id,
            'transaction_id': transaction_id,
            'transaction_date': datetime.now().strftime('%B %d, %Y'),
            'payment_method': payment_method,
            'status': status,
            'transaction_fee': transaction_fee,
            'total_amount': total_amount,
            'receipt_url': receipt_url or '#'
        }
        
        # Send the email
        template_name = 'core/emails/donation_invoice.html'
        return send_html_email(
            subject=subject,
            template_name=template_name,
            context=context,
            recipient_list=[donor_email],
            fail_silently=False
        )
    except Exception as e:
        print(f"Error sending donation invoice email: {str(e)}")
        return False
