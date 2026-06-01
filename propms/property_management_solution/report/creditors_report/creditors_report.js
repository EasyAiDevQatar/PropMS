// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Creditors Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -12)
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "property",
			label: __("Property"),
			fieldtype: "Link",
			options: "Property"
		},
		{
			fieldname: "unit",
			label: __("Unit"),
			fieldtype: "Link",
			options: "Unit Master",
			get_query: function() {
				const property = frappe.query_report.get_filter_value("property");
				return property ? { filters: { property: property } } : {};
			}
		},
		{
			fieldname: "tenant",
			label: __("Tenant"),
			fieldtype: "Link",
			options: "Customer"
		}
	]
};
