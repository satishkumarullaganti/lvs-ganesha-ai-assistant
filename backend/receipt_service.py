from fpdf import FPDF
import os

RECEIPT_FOLDER = "static/receipts"

os.makedirs(RECEIPT_FOLDER, exist_ok=True)


def generate_receipt_pdf(receipt_id, name, flat_number, amount):

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "LVS Ganesha Festival - Donation Receipt", ln=True, align="C")

    pdf.set_font("Helvetica", "", 12)
    pdf.ln(10)

    pdf.cell(0, 10, f"Receipt ID : {receipt_id}", ln=True)
    pdf.cell(0, 10, f"Name       : {name}", ln=True)
    pdf.cell(0, 10, f"Flat No    : {flat_number}", ln=True)
    pdf.cell(0, 10, f"Amount     : Rs. {amount}", ln=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 8, "Thank you for your generous contribution. May Lord Ganesha bless you and your family.")

    file_path = f"{RECEIPT_FOLDER}/{receipt_id}.pdf"

    pdf.output(file_path)

    return file_path
