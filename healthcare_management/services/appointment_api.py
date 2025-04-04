import frappe
from datetime import datetime

@frappe.whitelist()
def manage_token(practitioner_name):
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Fetch Healthcare Practitioner record
    practitioner = frappe.get_doc("Healthcare Practitioner", practitioner_name)

    if not practitioner or not practitioner.token_history:
        frappe.throw("No token configuration found for this practitioner.")

    # Get today's token entry
    token_entry = next((t for t in practitioner.token_history if t.date == today_date), None)

    if not token_entry:
        # If no entry exists for today, create a new one with token series "A-"
        new_token_series = practitioner.token_history[-1].token_series
        new_token_number = 1
        new_token = f"{new_token_series}{new_token_number}"

        practitioner.append("token_history", {
            "date": today_date,
            "token_series": new_token_series, 
            "last_token": new_token
        })
    else:
        # Increment last token
        series = token_entry.token_series
        last_token_number = int(token_entry.last_token) + 1
        new_token = f"{series}{last_token_number}"
        token_entry.last_token = last_token_number  # Update last token in database

    # Save changes
    practitioner.save(ignore_permissions=True)
    frappe.db.commit()

    return new_token