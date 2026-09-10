// Copyright (c) 2016, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Property Status"] = {
	"filters": [
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
			"options": "Property Unit",
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
		},
		{
			"fieldname": "property_type",
			"label": __("Property Type"),
			"fieldtype": "Link",
			"options": "Property Type"
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "days_until_free" && data && data.days_until_free !== undefined && data.days_until_free !== null) {
			const d = data.days_until_free;
			let color = "green";
			if (d === 0) color = "green";
			else if (d <= 30) color = "darkorange";
			else if (d <= 90) color = "orange";
			value = `<span style="color:${color}; font-weight:600">${d}</span>`;
		}
		return value;
	}
};
