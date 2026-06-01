// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */
var months = "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember";

frappe.query_reports["Mis-Income Break Up"] = {
	"filters": [
		{
			"fieldname": "from",
			"label": __("From Month"),
			"fieldtype": "Select",
			"options": months,
			"default": "January"
		},
		{
			"fieldname": "to",
			"label": __("To Month"),
			"fieldtype": "Select",
			"options": months,
			"default": "December"
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date (override)"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date (override)"),
			"fieldtype": "Date"
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
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (row[0].rowIndex === 5 || value === "RENTAL INCOME" || value === "MAINTENANCE INCOME" || value === "Maintenance Total") {
			value = '<b style="font-weight:bold">' + value + '</b>';
		}
		return value;
	}
};
