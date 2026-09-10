// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lease Agreement", {
	setup: function(frm) {
		frm.set_query("unit", function() {
			const filters = {};
			if (frm.doc.property) {
				filters.property = frm.doc.property;
			}
			return { filters };
		});

		frm.set_query("item", "items", function() {
			return { filters: { disabled: 0 } };
		});
	},

	refresh: function(frm) {
		// Direct save & submit — hide legacy workflow action buttons if present
		frm.page.actions.find(".dropdown-item").each(function() {
			const label = ($(this).text() || "").trim();
			if (label.includes("Mark approved") || label.includes("Review")) {
				$(this).hide();
			}
		});

		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frappe.call({
				method: "propms.property_management_solution.doctype.lease_agreement.lease_agreement.sync_invoice_schedule_payments",
				args: { lease_agreement: frm.doc.name },
				callback: function(r) {
					if (r.message && r.message.updated) {
						frm.reload_doc();
					} else if (r.message && frm.doc.linked_payment_count !== r.message.linked_payment_count) {
						frm.set_value("linked_payment_count", r.message.linked_payment_count);
					}
				}
			});
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Generate Sales Invoice for Selected"), function() {
				const selected = frm.fields_dict.invoice_schedule.grid.get_selected_children();
				if (!selected.length) {
					frappe.msgprint(__("Select one schedule row first."));
					return;
				}
				const row = selected[0];
				if (row.sales_invoice) {
					frappe.msgprint(__("Already invoiced: {0}", [row.sales_invoice]));
					return;
				}
				frappe.call({
					method: "propms.property_management_solution.doctype.lease_agreement.lease_agreement.make_sales_invoice_for_schedule",
					args: {
						lease_agreement: frm.doc.name,
						schedule_row_name: row.name
					},
					callback: function(r) {
						if (r.message) {
							frappe.show_alert(__("Sales Invoice {0} created", [r.message]));
							frm.reload_doc();
						}
					}
				});
			}, __("Create"));
		}

		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.security_deposit) > 0 &&
			(frm.doc.security_deposit_status === "Received" || frm.doc.security_deposit_payment_entry) &&
			!frm.doc.security_deposit_return_payment_entry
		) {
			frm.add_custom_button(__("Return Security Deposit"), function() {
				frappe.call({
					method: "propms.property_management_solution.doctype.lease_agreement.lease_agreement.make_deposit_return_payment_entry",
					args: { lease_agreement: frm.doc.name },
					callback: function(r) {
						if (r.message) {
							frappe.show_alert(__("Payment Entry {0} created", [r.message]));
							frm.reload_doc();
						}
					}
				});
			}, __("Create"));
		}

		if (frm.doc.security_deposit_payment_entry) {
			frm.add_custom_button(__("Open Deposit Payment"), function() {
				frappe.set_route("Form", "Payment Entry", frm.doc.security_deposit_payment_entry);
			});
		}
		if (frm.doc.security_deposit_return_payment_entry) {
			frm.add_custom_button(__("Open Deposit Return"), function() {
				frappe.set_route("Form", "Payment Entry", frm.doc.security_deposit_return_payment_entry);
			});
		}

		if (!frm.is_new() && flt(frm.doc.linked_payment_count) > 0) {
			frm.add_custom_button(
				__("Payment Entries ({0})", [frm.doc.linked_payment_count]),
				function() {
					frappe.set_route("List", "Payment Entry", {
						propms_lease_agreement: frm.doc.name,
						docstatus: 1
					});
				}
			);
		}
	},

	unit: function(frm) {
		if (!frm.doc.unit) return;

		frappe.db.get_value("Unit Master", frm.doc.unit, ["property", "rent_amount"], function(value) {
			if (value.property && !frm.doc.property) {
				frm.set_value("property", value.property);
			}
			if (value.rent_amount && !frm.doc.monthly_rent) {
				frm.set_value("monthly_rent", value.rent_amount);
			}
		});

		if (!(frm.doc.items || []).length) {
			frappe.call({
				method: "propms.property_management_solution.doctype.lease_agreement.lease_agreement.fetch_unit_services",
				args: { unit: frm.doc.unit },
				callback: function(r) {
					if (r.message && r.message.length) {
						frm.clear_table("items");
						r.message.forEach(function(svc) {
							const row = frm.add_child("items");
							Object.assign(row, svc);
						});
						frm.refresh_field("items");
					}
				}
			});
		}
	},

	customer: function(frm) {
		if (!frm.doc.customer) return;
		frappe.db.get_value("Customer", frm.doc.customer, "customer_name", function(v) {
			if (v) frm.set_value("customer_name", v.customer_name);
		});
	},

	buyer: function(frm) {
		if (!frm.doc.buyer) return;
		frappe.db.get_value("Customer", frm.doc.buyer, "customer_name", function(v) {
			if (v) frm.set_value("buyer_name", v.customer_name);
		});
	},

	contract_type: function(frm) {
		if (frm.doc.contract_type === "Sale") {
			frm.set_value("monthly_rent", 0);
			frm.set_value("payment_frequency", "");
			frm.set_value("rent_commission_only", 0);
		} else {
			frm.set_value("buyer", "");
			frm.set_value("buyer_name", "");
		}
	},

	sale_amount: function(frm) {
		recalc_commission(frm);
	},

	commission_percentage: function(frm) {
		recalc_commission(frm);
	},

	monthly_rent: function(frm) {
		recalc_rent_commission(frm);
	},

	rent_commission_only: function(frm) {
		recalc_rent_commission(frm);
	},

	rent_commission_months: function(frm) {
		recalc_rent_commission(frm);
	}
});

function recalc_commission(frm) {
	if (frm.doc.contract_type !== "Sale") return;
	const amt = (frm.doc.sale_amount || 0) * (frm.doc.commission_percentage || 0) / 100;
	frm.set_value("commission_amount", amt);
}

function recalc_rent_commission(frm) {
	if (frm.doc.contract_type !== "Rent" || !frm.doc.rent_commission_only) return;
	const amt = (frm.doc.monthly_rent || 0) * (frm.doc.rent_commission_months || 1);
	frm.set_value("rent_commission_amount", amt);
}

frappe.ui.form.on("Lease Agreement Item", {
	rate: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.amount = (row.qty || 1) * (row.rate || 0);
		frm.refresh_field("items");
	},
	qty: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.amount = (row.qty || 1) * (row.rate || 0);
		frm.refresh_field("items");
	}
});
