import frappe
import frappe.utils

@frappe.whitelist()
def reset_doctor_token(doctor):
    """
    Resets the doctor's token by inserting a new row with Last Token = "X-0".
    """
    doc = frappe.get_doc("Healthcare Practitioner", {"practitioner_name":doctor})
    # if not doc.token_history.token_series:
    #     frappe.throw("Token series not set for this doctor.")
    last_entry = doc.token_history[-1] if doc.token_history else None
    token_series = last_entry.token_series if last_entry else frappe.throw("No token series assigned.")

    # Reset the token
    new_token = f"{token_series}0"
    last_entry.date = frappe.utils.today()
    last_entry.last_token = f"{last_entry.token_series}0"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return f"Token reset successful: {new_token}"
