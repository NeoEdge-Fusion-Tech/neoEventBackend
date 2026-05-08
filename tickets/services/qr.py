import qrcode

from io import BytesIO

from django.core.files import File

from PIL import Image


def generate_registration_qr(registration):

    qr_data = str(registration.registration_code)

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
    )

    qr.add_data(qr_data)

    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()

    img.save(buffer, format="PNG")

    file_name = f"{registration.registration_code}.png"

    registration.qr_code.save(
        file_name,
        File(buffer),
        save=False,
    )

    buffer.close()