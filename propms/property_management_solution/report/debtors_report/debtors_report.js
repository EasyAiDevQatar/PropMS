// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Debtors Report"] = {
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
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.id == "usd") {
			value = "<span style='float:right;'>" + value + "</span>";
		}
		if (column.id == "tzs") {
			value = "<span style='float:right;'>" + value + "</span>";
		}

		if (data && data["invoice_no"] == "TOTAL") {
			value = "<span style='font-weight:bold;'>" + value + "</span>";
			if (column.id == "due_date") value = "";
			if (column.id == "cost_center") value = "";
			if (column.id == "items") value = "";
			if (column.id == "from_date") value = "";
			if (column.id == "to_date") value = "";
		}

		return value;
	}
};
