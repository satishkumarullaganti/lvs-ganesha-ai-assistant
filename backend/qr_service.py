import qrcode
import os

QR_FOLDER = "static/qrcodes"

os.makedirs(QR_FOLDER, exist_ok=True)


def generate_qr_code(coupon_id: str) -> str:

    qr_content = f"Annaprasada Coupon: {coupon_id}"

    img = qrcode.make(qr_content)

    file_path = f"{QR_FOLDER}/{coupon_id}.png"

    img.save(file_path)

    return file_path
