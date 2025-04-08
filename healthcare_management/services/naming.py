import frappe
from frappe.model.naming import make_autoname
from datetime import datetime


def generate_uid_series():
    year_suffix = datetime.now().strftime('%y')
    series = f"RDC-PT{year_suffix}-.#####."
    return make_autoname(series)

@frappe.whitelist()
def before_insert(doc, method):
    if not doc.uid:  # Check if UID is not already set
        # Call the function to generate the UID series
        doc.uid = generate_uid_series()  # Generate and assign the UID to the patient document
