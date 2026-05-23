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
    
    attendee_name = f"{registration.attendee.first_name} {registration.attendee.last_name}".strip() if registration.attendee else registration.guest_full_name
    ticket_type = registration.ticket_type.name if registration.ticket_type else "General Admission"
    event_title = event.title
    
    # Optional: Base64 encode the banner or logo if needed for standalone HTML
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Badge - {attendee_name}</title>
        <style>
            @page {{ size: 4in 6in; margin: 0; }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                margin: 0; padding: 0;
                display: flex; justify-content: center; align-items: center;
                height: 100vh; background: #f0f0f0;
            }}
            .badge {{
                width: 3.5in; height: 5.5in;
                background: white;
                border: 2px solid #333;
                border-radius: 12px;
                display: flex; flex-direction: column;
                overflow: hidden;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: #111;
                color: white;
                padding: 20px;
                text-align: center;
                font-weight: bold;
                font-size: 1.2rem;
            }}
            .content {{
                flex: 1;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                padding: 20px; text-align: center;
            }}
            .name {{
                font-size: 2rem;
                font-weight: 900;
                margin-bottom: 10px;
                color: #222;
            }}
            .ticket-type {{
                font-size: 1.1rem;
                font-weight: bold;
                color: #e5533c;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 30px;
            }}
            .qr-code {{
                width: 150px; height: 150px;
            }}
            .footer {{
                background: #eee;
                padding: 10px;
                text-align: center;
                font-size: 0.8rem;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="badge">
            <div class="header">{event_title}</div>
            <div class="content">
                <div class="name">{attendee_name}</div>
                <div class="ticket-type">{ticket_type}</div>
                <img class="qr-code" src="data:image/png;base64,{qr_base64}" alt="QR Code" />
            </div>
            <div class="footer">
                ID: {registration_code[:8]}<br>
                Please wear this badge at all times
            </div>
        </div>
        <script>
            // Automatically trigger print dialogue for thermal printers
            window.onload = function() {{ window.print(); }}
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html, content_type="text/html")
