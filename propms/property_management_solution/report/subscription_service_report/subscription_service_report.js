// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Subscription Service Report"] = {
	"filters": [
		{
			"fieldname": "service_type",
			"label": __("Service Type"),
			"fieldtype": "Link",
			"options": "Item",
			"reqd": 1,
			get_query: () => ({
				filters: { item_group: "Services" }
			})
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.year_start()
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "property",
			"label": __("Property"),
			"fieldtype": "Link",
			"options": "Property"
		},
		{
			"fieldname": "unit",
			"label": __("Unit"),
			"fieldtype": "Link",
			"options": "Unit Master",
			"get_query": function() {
				const property = frappe.query_report.get_filter_value("property");
				return property ? { filters: { property: property } } : {};
			}
		},
		{
			"fieldname": "tenant",
			"label": __("Tenant"),
			"fieldtype": "Link",
			"options": "Customer"
		}
	]
};
