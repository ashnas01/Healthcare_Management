from datetime import datetime, timedelta
import frappe
from frappe import _
from frappe.utils import nowdate, flt,cint, getdate
from frappe.model.document import Document

@frappe.whitelist()
def create_sales_invoice(patient, patient_name, doctor=None, items=None, mode_of_payment=None, encounter_token=None):
    """
    Creates a Sales Invoice for a Patient with optimizations and auto-generates Payment Entry + Patient Encounter.
    """
    try:
        # Validate inputs upfront
        validate_mandatory(patient, items)
        
        # Convert items to list if string
        items = safe_json_parse(items)
        
        # Batch validate items before processing
        validate_items_existence(items)
        
        # Get customer with validation
        customer = get_validated_customer(patient)
        update_patient_registration_details(patient)
        
        
        # Create and process Sales Invoice
        invoice = create_and_submit_invoice(patient, patient_name, customer, doctor, items)
        
        # Process payment if required
        payment_entry = process_payment(invoice, mode_of_payment) if mode_of_payment else None
        
        # Create patient encounter
        encounter = create_patient_encounter(patient, doctor, invoice.company, encounter_token)
        
        return build_response(invoice, encounter)

    except Exception as e:
        handle_errors(e)

# ----------
# Helper Functions
# ----------
def validate_mandatory(patient, items):
    """Pre-flight validations"""
    if not patient:
        frappe.throw(_("Patient is mandatory"))
    
    if not items or (isinstance(items, list) and len(items) == 0):
        frappe.throw(_("At least one item is required"))

def safe_json_parse(items):
    """Safely parse JSON string input"""
    if isinstance(items, str):
        try:
            return frappe.parse_json(items)
        except:
            frappe.throw(_("Invalid items format"))
    return items

def validate_items_existence(items):
    """Batch validate items in single query"""
    item_codes = {item.get("item_code") for item in items}
    existing_items = {d.name for d in frappe.get_all("Item", filters={"name": ["in", item_codes]}, fields=["name"])}
    
    if missing := item_codes - existing_items:
        frappe.throw(_("Invalid items: {0}").format(", ".join(missing)))

def get_validated_customer(patient):
    """Get and validate customer"""
    customer = frappe.get_cached_value("Patient", patient, "customer")
    
    if not customer:
        frappe.throw(_("No Customer linked to Patient {0}").format(patient))
    
    if frappe.get_cached_value("Customer", customer, "disabled"):
        frappe.throw(_("Customer {0} is disabled").format(customer))
    
    return customer

def create_and_submit_invoice(patient, patient_name, customer, doctor, items):
    """Create and submit Sales Invoice with optimized validations"""
    invoice = frappe.new_doc("Sales Invoice")
    invoice.update({
        "customer": customer,
        "patient": patient,
        "patient_name": patient_name,
        "ref_practitioner": doctor,
        "due_date": nowdate(),
        "items": [validate_and_prepare_item(row) for row in items]
    })
    
    invoice.insert(ignore_permissions=True)
    invoice.submit()
    frappe.msgprint(_("Invoice {0} created").format(invoice.name), alert=True)
    return invoice
def update_patient_registration_details(patient):
    """Update patient's registration status and consultation renewal date"""
    patient_doc = frappe.get_doc("Patient", patient)
    changed = False

    # Update registration status if not already registered
    if cint(patient_doc.custom_is_registered) == 0:
        patient_doc.custom_is_registered = 1
        changed = True

    # Always update renewal date to current date
    renewal_date = nowdate()
    if patient_doc.custom_consultation_renewal_date != renewal_date:
        patient_doc.custom_consultation_renewal_date = renewal_date
        changed = True
        
    if patient_doc.custom_consultation_valid_date != renewal_date:
        current_date_obj = datetime.strptime(renewal_date, '%Y-%m-%d')
        patient_doc.custom_consultation_valid_date = current_date_obj + timedelta(days=6)
        changed = True

    if changed:
        patient_doc.save(ignore_permissions=True)
        frappe.msgprint(_("Patient registration details updated"), alert=True)

def validate_and_prepare_item(item):
    """Validate individual item and prepare for insertion"""
    if (qty := flt(item.get("qty", 1))) <= 0:
        frappe.throw(_("Invalid quantity for item {0}").format(item.get("item_code")))
    
    if (rate := flt(item.get("rate", 0))) < 0:
        frappe.throw(_("Negative rate for item {0}").format(item.get("item_code")))
    
    return {
        "item_code": item.get("item_code"),
        "qty": qty,
        "rate": rate
    }

def process_payment(invoice, mode_of_payment):
    """Handle payment processing"""
    try:
        validate_mode_of_payment(mode_of_payment, invoice.company)
        return create_payment_entry(invoice, mode_of_payment)
    except Exception as e:
        log_and_notify_payment_error(invoice.name, e)
        return None

def validate_mode_of_payment(mode, company):
    """Validate mode of payment configuration"""
    if not frappe.db.exists("Mode of Payment", {"name": mode}):
        frappe.throw(_("Invalid Mode of Payment: {0}").format(mode))
    
    if not frappe.get_cached_value("Mode of Payment Account", 
        {"parent": mode, "company": company}, "default_account"):
        frappe.throw(_("Mode of Payment {0} not configured for company {1}").format(mode, company))

def create_payment_entry(invoice, mode_of_payment):
    """Create payment entry using existing invoice doc"""
    if invoice.outstanding_amount <= 0:
        return None

    pe = frappe.new_doc("Payment Entry")
    pe.update({
        "posting_date": nowdate(),
        "payment_type": "Receive",
        "mode_of_payment": mode_of_payment,
        "paid_from": invoice.debit_to,
        "paid_to": get_payment_account(mode_of_payment, invoice.company),
        "party_type": "Customer",
        "party": invoice.customer,
        "paid_amount": invoice.outstanding_amount,
        "received_amount": invoice.outstanding_amount,
        "references": [{
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
            "allocated_amount": invoice.outstanding_amount
        }]
    })
    
    pe.insert(ignore_permissions=True)
    pe.submit()
    frappe.msgprint(_("Payment {0} created").format(pe.name), alert=True)
    return pe

def get_payment_account(mode, company):
    """Cached lookup for payment account"""
    return frappe.get_cached_value("Mode of Payment Account", 
        {"parent": mode, "company": company}, "default_account")

def create_patient_encounter(patient, doctor, company, encounter_token):
    """Optimized patient encounter creation"""
    if not doctor:  # Skip if no doctor specified
        return None

    encounter = frappe.new_doc("Patient Encounter")
    encounter.update({
        "patient": patient,
        "practitioner": doctor,
        "encounter_date": nowdate(),
        "company": company,
        "encounter_type": "Outpatient",
        "custom_encounter_token": encounter_token
    })
    
    encounter.insert(ignore_permissions=True)
    encounter.submit()
    return encounter.name

def build_response(invoice, encounter):
    """Standardized response format"""
    return {
        "sales_invoice": invoice.name,
        "patient_encounter": encounter,
        "total_amount": invoice.grand_total,
        "outstanding_amount": invoice.outstanding_amount
    }

def log_and_notify_payment_error(invoice_name, error):
    """Centralized error handling for payments"""
    frappe.log_error(
        title=_("Payment Processing Failed"),
        message=f"Invoice: {invoice_name}\nError: {str(error)}"
    )
    frappe.msgprint(
        _("Payment failed for Invoice {0}. See logs for details.").format(invoice_name),
        alert=True
    )

def handle_errors(error):
    """Global error handler"""
    frappe.log_error(
        title=_("Sales Pipeline Error"),
        message=f"Error: {str(error)}"
    )
    frappe.throw(_("Process failed. Please check error logs for details."))
