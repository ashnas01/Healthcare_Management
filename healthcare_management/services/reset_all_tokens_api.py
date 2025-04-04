import frappe
import frappe.utils

def reset_all_tokens():
    """
    Resets the last token for all doctors at midnight.
    """
    doctors = frappe.get_all("Healthcare Practitioner", filters={}, fields=["practitioner_name", "token_history"])

    for doctor in doctors:
        if doctor.token_history.token_series:
            new_token = f"{doctor.token_history.token_series}0"
            doc = frappe.get_doc("Healthcare Practitioner", doctor.practitioner_name)

            # Insert a new row in the child table for reset
            # doc.append("token_history", {
            #     "date": frappe.utils.today(),
            #     "token_series": doctor.token_series,
            #     "last_token": new_token
            # })
            doc.token_history.date = frappe.utils.today()
            doc.token_history.last_token = {new_token}

            doc.save(ignore_permissions=True)
            frappe.db.commit()
