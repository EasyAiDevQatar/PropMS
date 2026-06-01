// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Expiring Leases"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), 3)
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
		if (column.fieldname === "days_until_expiry" && data && data.days_until_expiry !== undefined) {
			const d = data.days_until_expiry;
			let color = "green";
			if (d < 0) color = "red";
			else if (d <= 30) color = "darkorange";
			else if (d <= 60) color = "orange";
			value = `<span style="color:${color}; font-weight:600">${d}</span>`;
		}
		return value;
	}
};
