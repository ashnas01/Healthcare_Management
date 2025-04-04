# import frappe

# @frappe.whitelist()
# def get_registration_fee(patient_name):
#     """
#     Fetches the Registration Fee from the Pricing Rule Doctype 
#     based on the Patient's Territory.
#     """
#     # Get Patient's Territory
#     patient = frappe.get_doc("Patient", {"patient_name": patient_name})
#     if not patient.territory:
#         return "No Territory Found"

#     # Find Pricing Rule matching the Territory
#     pricing_rule = frappe.get_all(
#         "Pricing Rule",
#         filters={"territory": patient.territory, "apply_on": "Item Code"},
#         fields=["rate"],
#         order_by="modified desc",
#         limit=1
#     )

#     if pricing_rule:
#         return pricing_rule[0].get("rate", "Not Set")
#     return "No Pricing Rule Found"
