// Copyright (c) 2026, Aakvatech and contributors

frappe.query_reports["Maintenance Cost By Unit"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
		},
		{
			fieldname: "property",
			label: __("Property"),
			fieldtype: "Link",
			options: "Property",
		},
		{
			fieldname: "unit",
			label: __("Unit"),
			fieldtype: "Link",
			options: "Unit Master",
			get_query: () => {
				const property = frappe.query_report.get_filter_value("property");
				return property ? { filters: { property } } : {};
			},
		},
	],
};
