from fpdf import FPDF
from datetime import date
import os

RECEIPT_FOLDER = "static/receipts"

# These two image files must exist at these paths.
# They're cropped from the official LVS letterhead:
# - HEADER_IMAGE: logo, association name/address, Ganesha graphic
# - FOOTER_IMAGE: KV Umashankar + Binu Prasad signatures only
ASSETS_FOLDER = "static/receipt_assets"
HEADER_IMAGE = os.path.join(ASSETS_FOLDER, "receipt_header_top.png")
FOOTER_IMAGE = os.path.join(ASSETS_FOLDER, "receipt_footer.png")

BANNER_TEXT = "Ganesh Utsav 2026 Celebrations"

os.makedirs(RECEIPT_FOLDER, exist_ok=True)


def generate_receipt_pdf(receipt_id, name, flat_number, amount, utr_number=None, proof_uploaded=False, status="pending", block=None):

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    page_width = pdf.w
    page_height = pdf.h

    # ==========================================
    # Double Border (matches the LVS letterhead
    # style: light blue outer, peach/cream inner)
    # ==========================================

    pdf.set_draw_color(168, 199, 230)  # light blue
    pdf.set_line_width(1.2)
    pdf.rect(5, 5, page_width - 10, page_height - 10)

    pdf.set_draw_color(250, 224, 196)  # peach/cream
    pdf.set_line_width(0.6)
    pdf.rect(9, 9, page_width - 18, page_height - 18)

    content_x = 20
    content_width = page_width - 40

    # ==========================================
    # Header Image (logo, association name,
    # address, Ganesha graphic)
    # ==========================================

    header_y = 15

    if os.path.exists(HEADER_IMAGE):

        # Preserve the header image's own aspect ratio
        header_aspect_ratio = 138 / 890  # original crop height/width
        header_height = content_width * header_aspect_ratio

        pdf.image(
            HEADER_IMAGE,
            x=content_x,
            y=header_y,
            w=content_width,
            h=header_height
        )

    else:

        header_height = 0

        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(content_x, header_y)
        pdf.cell(
            content_width, 12,
            "LVS EXCELLENCY RESIDENTS' WELFARE ASSOCIATION",
            align="C"
        )
        header_height = 12

    # ==========================================
    # Orange Banner (drawn as real text, not an
    # image, so the year can be updated easily
    # in future without re-editing an image file)
    # ==========================================

    banner_y = header_y + header_height + 4
    banner_height = 10

    pdf.set_fill_color(255, 140, 0)  # orange
    pdf.rect(content_x, banner_y, content_width, banner_height, style="F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(content_x, banner_y + 1)
    pdf.cell(content_width, banner_height - 2, BANNER_TEXT, align="C")

    # ==========================================
    # "Donation Receipt" Title
    # ==========================================

    title_y = banner_y + banner_height + 6

    pdf.set_text_color(30, 60, 110)  # dark blue
    pdf.set_font("Times", "BI", 28)
    pdf.set_xy(content_x, title_y)
    pdf.cell(content_width, 13, "Donation Receipt", align="C")

    # Divider line under the title
    divider_y = title_y + 13

    pdf.set_draw_color(120, 120, 120)
    pdf.set_line_width(0.3)
    pdf.line(
        content_x + content_width * 0.2, divider_y,
        content_x + content_width * 0.8, divider_y
    )

    # ==========================================
    # Pending Verification Badge
    # (shown until a volunteer confirms the UTR
    # against the bank statement)
    # ==========================================

    if status != "verified":

        badge_y = divider_y + 3
        badge_text = "PROVISIONAL RECEIPT - PAYMENT PENDING VERIFICATION"

        pdf.set_text_color(120, 120, 120)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(content_x, badge_y)
        pdf.cell(content_width, 6, badge_text, align="C")

    # ==========================================
    # Receipt Details
    # ==========================================

    details_y = divider_y + (14 if status != "verified" else 8)

    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 13)

    today_str = date.today().strftime("%d-%b-%Y")

    if utr_number:
        payment_ref_label = "UPI Ref / UTR No."
        payment_ref_value = utr_number
    elif proof_uploaded:
        payment_ref_label = "Payment Proof"
        payment_ref_value = "Screenshot Uploaded"
    else:
        payment_ref_label = "Payment Proof"
        payment_ref_value = "Not provided"

    details = [
        ("Receipt ID", receipt_id),
        ("Date", today_str),
        ("Name", name),
        ("Block", block) if block else None,
        ("Flat Number", flat_number),
        ("Amount", f"Rs. {amount}"),
        (payment_ref_label, payment_ref_value),
    ]

    # Drop the Block row entirely for older receipts/callers
    # that don't pass a block (keeps this backward-compatible).
    details = [row for row in details if row is not None]

    label_x = content_x + content_width * 0.28
    value_x = content_x + content_width * 0.45
    row_height = 8

    current_y = details_y

    for label, value in details:

        pdf.set_font("Helvetica", "B", 13)
        pdf.set_xy(label_x, current_y)
        pdf.cell(value_x - label_x, row_height, f"{label} :")

        pdf.set_font("Helvetica", "", 13)
        pdf.set_xy(value_x, current_y)
        pdf.cell(content_width * 0.35, row_height, str(value))

        current_y += row_height

    # ==========================================
    # Thank You Note
    # ==========================================

    thanks_y = current_y + 8

    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "I", 12)
    pdf.set_xy(content_x, thanks_y)
    pdf.multi_cell(
        content_width, 7,
        "Thank you for your generous contribution. "
        "May Lord Ganesha bless you and your family.",
        align="C"
    )

    # ==========================================
    # Footer Image (KV Umashankar + Binu Prasad
    # signatures only)
    # ==========================================

    if os.path.exists(FOOTER_IMAGE):

        footer_aspect_ratio = 70 / 595  # original crop height/width
        footer_width = content_width * 0.65
        footer_height = footer_width * footer_aspect_ratio

        footer_y = page_height - 9 - footer_height - 8
        footer_x = content_x + (content_width - footer_width) / 2

        pdf.image(
            FOOTER_IMAGE,
            x=footer_x,
            y=footer_y,
            w=footer_width,
            h=footer_height
        )

    else:

        # -----------------------------------------
        # Text fallback signature block, used when
        # receipt_footer.png is missing so the
        # signatures never silently disappear.
        # -----------------------------------------

        signatories = [
            ("K.V. Umashankar", "President"),
            ("Binu Prasad", "Secretary"),
        ]

        sig_width = content_width * 0.32
        sig_y = page_height - 9 - 26

        left_x = content_x + content_width * 0.12
        right_x = content_x + content_width - content_width * 0.12 - sig_width

        sig_positions = [left_x, right_x]

        for (name, title), sig_x in zip(signatories, sig_positions):

            line_y = sig_y

            pdf.set_draw_color(120, 120, 120)
            pdf.set_line_width(0.3)
            pdf.line(sig_x, line_y, sig_x + sig_width, line_y)

            pdf.set_text_color(30, 30, 30)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_xy(sig_x, line_y + 2)
            pdf.cell(sig_width, 6, name, align="C")

            pdf.set_text_color(90, 90, 90)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_xy(sig_x, line_y + 8)
            pdf.cell(sig_width, 6, title, align="C")

    file_path = f"{RECEIPT_FOLDER}/{receipt_id}.pdf"

    pdf.output(file_path)

    return file_path