import frappe

def create_address_from_patient(doc, method):
    """
    After a Patient is inserted, create a new Address document using the custom address fields.
    The dynamic link is added as a child record in the dynamic_links table.
    """

    if doc.custom_address_line:
        address = frappe.new_doc("Address")

        address.address_title = doc.patient_name
        
        address.address_line1 = doc.custom_address_line
        address.city = doc.custom_city
        address.state = doc.custom_state
        address.country = doc.custom_country  
        address.pincode = doc.custom_pincode
        address.append("links", {
            "link_doctype": "Patient",
            "link_name": doc.patient_name  
        })
        
        address.insert(ignore_permissions=True)
        frappe.db.commit()  