frappe.query_reports["Self Consumption in Maintenance Job Card"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "property",
            "label": __("Property"),
            "fieldtype": "Link",
            "options": "Property"
        },
        {
            "fieldname": "tenant",
            "label": __("Tenant"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ]
}
