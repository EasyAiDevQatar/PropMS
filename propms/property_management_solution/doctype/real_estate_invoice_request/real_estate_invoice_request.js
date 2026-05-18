// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Real Estate Invoice Request", {
	refresh: function(frm) {
		if (!frm.doc.__islocal && frm.doc.status !== "Cancelled" && !frm.doc.sales_invoice) {
			frm.add_custom_button(__("Generate Sales Invoice"), function() {
				frappe.call({
					method: "propms.property_management_solution.doctype.real_estate_invoice_request.real_estate_invoice_request.generate_sales_invoice",
					args: {
						invoice_request: frm.doc.name,
					},
					callback: function(r) {
						if (r.message) {
							frappe.set_route("Form", "Sales Invoice", r.message);
						}
					},
				});
			});
		}
	},
});
