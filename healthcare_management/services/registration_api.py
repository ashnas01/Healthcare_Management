# import frappe
# from frappe import _

# @frappe.whitelist()
# def get_registration_fee_item(patient, territory):
#     from frappe import new_doc

#     # Fetch Patient document
#     patient_doc = frappe.get_doc('Patient', patient)
#     customer = patient_doc.customer  # Ensure 'customer' is the fieldname in Patient

#     # Create new Sales Invoice
#     si = new_doc('Sales Invoice')
#     si.patient = patient
#     si.customer = customer
#     si.territory = territory

#     # Add Registration Fee item
#     si.append('items', {
#         'item_code': 'Registration Fee',
#         'qty': 1  # Set default quantity
#     })

#     # Check if patient has a linked healthcare practitioner
#     if patient_doc.custom_healthcare_practitioner:
#         # Fetch the linked Healthcare Practitioner document
#         hp_doc = frappe.get_doc('Healthcare Practitioner', patient_doc.custom_healthcare_practitioner)
        
#         # Only add the consulting charge if both the charge item and charge are set
#         if hp_doc.op_consulting_charge_item and hp_doc.op_consulting_charge:
#             si.append('items', {
#                 'item_code': hp_doc.op_consulting_charge_item,
#                 'qty': 1,
#                 'rate': hp_doc.op_consulting_charge
#             })

#     # Apply default pricing and validations
#     si.set_missing_values()  # Applies price list and item defaults
#     si.calculate_taxes_and_totals()  # Applies pricing rules

#     # Save and return the new Sales Invoice
#     si.insert(ignore_permissions=True)
#     si.submit()
#     # si.db.commit()
#     return si.name
