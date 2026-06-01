// Shared filter definitions for property management reports.
// Other reports can call propms_standard_filters() to get the standard
// (From Date, To Date, Property, Unit, Tenant) filter set.

window.propms_standard_filters = function(opts) {
	opts = opts || {};
	const filters = [
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
	];
	if (opts.extra) {
		filters.push.apply(filters, opts.extra);
	}
	return filters;
};
