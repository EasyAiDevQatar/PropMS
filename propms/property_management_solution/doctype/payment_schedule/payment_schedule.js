// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Schedule", {
	setup: function(frm) {
		frm.set_query("unit", function() {
			if (!frm.doc.contract) {
				return {};
			}

			return {
				query: "propms.property_management_solution.doctype.payment_schedule.payment_schedule.get_units_for_contract",
				filters: {
					contract: frm.doc.contract,
				},
			};
		});
	},

	refresh: function(frm) {
		if (!frm.doc.__islocal && !frm.doc.sales_invoice && frm.doc.status !== "Paid") {
			frm.add_custom_button(__("Generate Sales Invoice"), function() {
				frappe.call({
					method: "propms.property_management_solution.doctype.payment_schedule.payment_schedule.make_sales_invoice",
					args: {
						payment_schedule: frm.doc.name,
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

	contract: function(frm) {
		if (!frm.doc.contract) {
			return;
		}

		frappe.db.get_value("Lease Agreement", frm.doc.contract, ["customer", "unit"], function(value) {
			if (value.customer) {
				frm.set_value("customer", value.customer);
			}
			if (value.unit) {
				frm.set_value("unit", value.unit);
			}
		});
	},

	charge: function(frm) {
		if (!frm.doc.charge || frm.doc.amount) {
			return;
		}

		frappe.db.get_value("Charges Setup", frm.doc.charge, "default_amount", function(value) {
			if (value.default_amount) {
				frm.set_value("amount", value.default_amount);
			}
		});
	},
});
