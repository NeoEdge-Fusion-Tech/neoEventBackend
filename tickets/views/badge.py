from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ..models import EventRegistration
import qrcode
import base64
from io import BytesIO

def generate_badge_html(request, registration_code):
    registration = get_object_or_404(
        EventRegistration.objects.select_related("attendee", "ticket_type", "event"),
        registration_code=registration_code
    )
    
    event = registration.event
    
    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(registration_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    attendee_name = registration.attendee.full_name if registration.attendee else registration.attendee_name
    ticket_type = registration.ticket_type.name if registration.ticket_type else "General Admission"
    event_title = event.title
    
    # Optional: Base64 encode the banner or logo if needed for standalone HTML
    
    if event.badge_template:
        # Use custom event template
        html = event.badge_template
        html = html.replace("{fullname}", attendee_name)
        html = html.replace("{ticket_id}", registration_code)
        html = html.replace("{ticket_type}", ticket_type)
        html = html.replace("{qr_code}", f"data:image/png;base64,{qr_base64}")
    else:
        # Fallback template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Badge - {attendee_name}</title>
            <style>
                body {{
                    font-family: sans-serif;
                    margin: 0; 
                    padding: 20px;
                    text-align: center;
                }}
                .badge {{
                    width: 336px; 
                    height: 480px;
                    margin: 0 auto;
                    border: 2px solid #333;
                    border-radius: 12px;
                    text-align: center;
                    overflow: hidden;
                }}
                .header {{
                    background-color: #111111;
                    color: #ffffff;
                    padding: 20px;
                    font-weight: bold;
                    font-size: 20px;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .name {{
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #222222;
                }}
                .ticket-type {{
                    font-size: 16px;
                    font-weight: bold;
                    color: #e5533c;
                    text-transform: uppercase;
                    margin-bottom: 30px;
                }}
                .qr-code {{
                    width: 150px; 
                    height: 150px;
                    margin: 0 auto;
                }}
                .footer {{
                    margin-top: 10px;
                    padding: 10px;
                    font-size: 12px;
                    color: #666666;
                }}
            </style>
        </head>
        <body>
            <div class="badge">
                <div class="header">{event_title}</div>
                <div class="content">
                    <div class="name">{attendee_name}</div>
                    <div class="ticket-type">{ticket_type}</div>
                    <br>
                    <!-- <img class="qr-code" src="data:image/png;base64,{qr_base64}" /> -->
                </div>
                <div class="footer">
                    ID: {registration_code[:8]}<br>
                    Please wear this badge at all times
                </div>
            </div>
        </body>
        </html>
        """
    
    return HttpResponse(html, content_type="text/html")
