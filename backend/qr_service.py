import qrcode
import os

QR_FOLDER = "static/qrcodes"

os.makedirs(QR_FOLDER, exist_ok=True)


def generate_qr_code(qr_content: str, file_name: str) -> str:

    img = qrcode.make(qr_content)

    file_path = f"{QR_FOLDER}/{file_name}.png"

    img.save(file_path)

    return file_path