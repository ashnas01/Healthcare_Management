import frappe;

def create_batch_from_item(doc,method) :

    if doc.has_batch_no :

        batch = frappe.new_doc("Batch")

        batch.batch_id = doc.custom_batch_id
        batch.item = doc.item_code
        batch.stock_uom = doc.stock_uom
        batch.expiry_date = doc.custom_expiry_date
        batch.description = doc.custom_batch_description

        batch.insert(ignore_permissions=True)
        frappe.db.commit()