# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "propms"
app_title = "Property Management Solution"
app_publisher = "Aakvatech"
app_description = "Property Management Solution"
app_icon = "octicon octicon-home"
app_color = "grey"
app_email = "info@aakvatech.com"
app_license = "MIT"

page_js = {
    "pos": "property_management_solution/point_of_sale.js",
    "point-of-sale": "property_management_solution/point_of_sale.js",
}

doctype_js = {
    "Sales Invoice": "property_management_solution/sales_invoice.js",
    "Journal Entry Account": "property_management_solution/journal_entry_account.js",
    "Issue": "property_management_solution/issue.js",
    "Company": "property_management_solution/company.js",
    "Contract": "property_management_solution/contract.js",
    "Property Viewing": "property_management_solution/doctype/property_viewing/property_viewing.js",
}

after_install = [
    "propms.utils.create_custom_fields.execute",
    "propms.utils.create_property_setter.execute",
    "propms.setup_defaults.execute",
]

after_migrate = [
    "propms.utils.create_custom_fields.execute",
    "propms.utils.create_property_setter.execute",
    "propms.setup_defaults.execute",
    "propms.property_management_solution.sync_workspace.sync_property_lifecycle_dashboard",
]

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                (
                    "Company-default_maintenance_tax_template",
                    "Company-default_tax_account_head",
                    "Company-default_tax_template",
                    "Company-property_management_settings",
                    "Company-security_account_code",
                    "Contract-propms_lease_agreement",
                    "Contract-propms_property",
                    "Contract-propms_section_break",
                    "Contract-propms_tenant",
                    "Contract-propms_unit",
                    "Issue Materials Detail-mateiral_request",
                    "Issue-col_brk_001",
                    "Issue-column_break_14",
                    "Issue-column_break_4",
                    "Issue-customer_feedback",
                    "Issue-defect_found",
                    "Issue-material_request",
                    "Issue-materials_billed",
                    "Issue-materials_required",
                    "Issue-person_in_charge_name",
                    "Issue-person_in_charge",
                    "Issue-property_name",
                    "Issue-section_break_15",
                    "Issue-sub_contractor_contact",
                    "Issue-sub_contractor_name",
                    "Item-reading_required",
                    "Material Request Item-material_request",
                    "Material Request-sales_invoice",
                    "Payment Entry-propms_lease_agreement",
                    "Payment Entry-propms_property",
                    "Payment Entry-propms_unit",
                    "Purchase Invoice-propms_maintenance_request",
                    "Purchase Invoice-propms_property",
                    "Purchase Invoice-propms_unit",
                    "Sales Invoice-propms_lease_agreement",
                    "Sales Invoice-propms_property",
                    "Sales Invoice-propms_unit",
                    "Quotation-cost_center",
                    "Sales Invoice-job_card",
                    "Sales Invoice-lease_information",
                    "Sales Invoice-lease_item",
                    "Sales Invoice-lease",
                ),
            ]
        ],
    },
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                (
                    "Contact-department-fieldtype",
                    "Contact-department-options",
                    "Daily Checklist-default_print_format",
                    "Issue-company-fetch_from",
                    "Issue-email_account-report_hide",
                    "Issue-issue_type-in_standard_filter",
                    "Issue-issue_type-reqd",
                    "Issue-opening_date-in_list_view",
                    "Issue-priority-in_standard_filter",
                    "Issue-quick_entry",
                    "Issue-raised_by-in_list_view",
                    "Issue-raised_by-report_hide",
                    "Issue-section_break_19-collapsible",
                    "Issue-section_break_7-collapsible",
                    "Issue-status-options",
                    "Journal Entry Account-account-columns",
                    "Journal Entry Account-cost_center-columns",
                    "Key Set Detail-key_set-in_standard_filter",
                    "Key Set Detail-returned-in_standard_filter",
                    "Key Set Detail-taken_by-in_standard_filter",
                    "Lease-customer-in_list_view",
                    "Lease-customer-in_standard_filter",
                    "Lease-end_date-in_list_view",
                    "Lease-lease_customer-in_standard_filter",
                    "Lease-property_owner-in_list_view",
                    "Lease-property_owner-in_standard_filter",
                    "Lease-property_user-in_standard_filter",
                    "Lease-property-in_standard_filter",
                    "Lease-security_status-in_standard_filter",
                    "Lease-security_status-options",
                    "Lease-start_date-in_list_view",
                    "Lease-wtax_paid_by-in_standard_filter",
                    "Material Request-material_request_type-options",
                    "Property-identification_section-bold",
                    "Property-section_break_13-bold",
                    "Property-section_break_22-bold",
                    "Property-section_break_4-bold",
                    "Property-status-options",
                    "Unit Type-search_fields",
                ),
            ]
        ],
    },
]


doc_events = {
    "Issue": {
        "validate": [
            "propms.issue_hook.validate",
        ],
    },
    "Material Request": {
        "validate": "propms.auto_custom.makeSalesInvoice",
        "on_update": "propms.auto_custom.makeSalesInvoice",
        "on_change": "propms.auto_custom.makeSalesInvoice",
    },
    "Sales Order": {
        "validate": "propms.auto_custom.validateSalesInvoiceItemDuplication"
    },
    "Key Set Detail": {"on_change": "propms.auto_custom.changeStatusKeyset"},
    "Meter Reading": {"on_submit": "propms.auto_custom.make_invoice_meter_reading"},
    "Contract": {
        "on_update": "propms.auto_custom.contract_status_changed",
        "on_cancel": "propms.auto_custom.contract_status_changed",
    },
    "Payment Entry": {
        "validate": "propms.property_management_solution.billing_hooks.sync_lease_links_on_payment_entry",
        "on_submit": "propms.property_management_solution.billing_hooks.update_lease_on_payment_entry_submit",
        "on_cancel": "propms.property_management_solution.billing_hooks.update_lease_on_payment_entry_cancel",
    },
}


# Lease Agreement maintains an invoice schedule. Sales Invoices are now
# generated on demand from the Lease Agreement form (Create > Generate
# Sales Invoice for Selected) - we no longer auto-create them daily.
scheduler_events = {
    "daily": [
        "propms.auto_custom.statusChangeBeforeLeaseExpire",
        "propms.auto_custom.statusChangeAfterLeaseExpire",
    ],
}
