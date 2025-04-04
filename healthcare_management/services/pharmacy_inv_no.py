import frappe
from datetime import datetime

def before_insert(doc, method):
    if not doc.pharmacy_invoice_number:  # Only generate if it's empty
        # Get the date from the 'posting_date' field
        if doc.date_and_time:
            date_obj = datetime.strptime(doc.date_and_time, "%Y-%m-%d")
        else:
            date_obj = datetime.today()  # Fallback to system date if empty

        year_suffix = date_obj.strftime('%y')  # Example: '24' for 2024
        month = date_obj.strftime('%m')  # Example: '03' for March

        # Get the last invoice number from the same month & year
        last_entry = frappe.get_all(
            "Pharmacy Billing",
            filters=[["pharmacy_invoice_number", "like", f"PH-INV-{month}-{year_suffix}-%"]],
            fields=["pharmacy_invoice_number"],
            order_by="creation desc",
            limit=1
        )

        # Extract last sequence number or start from 0
        last_number = 0
        if last_entry and last_entry[0].get("pharmacy_invoice_number"):
            try:
                last_number = int(last_entry[0]["pharmacy_invoice_number"].split("-")[-1])  # Extract last 5-digit number
            except (ValueError, IndexError):
                last_number = 0  # If there's an issue, start from 0

        # Generate next sequence number (##### format)
        next_number = str(last_number + 1).zfill(5)  # Ensures 5-digit format (00001, 00002, etc.)

        # Set the generated Pharmacy Bill Number
        doc.pharmacy_invoice_number = f"PH-INV-{month}-{year_suffix}-{next_number}"
