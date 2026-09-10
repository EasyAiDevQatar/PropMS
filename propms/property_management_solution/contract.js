// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Contract", {
	setup: function(frm) {
		frm.set_query("propms_unit", function() {
			const filters = {};
			if (frm.doc.propms_property) filters.property = frm.doc.propms_property;
			return { filters };
		});
	},

	propms_lease_agreement: function(frm) {
		if (!frm.doc.propms_lease_agreement) return;
		frappe.db.get_value(
			"Lease Agreement",
			frm.doc.propms_lease_agreement,
			["property", "unit", "customer"],
			function(value) {
				if (value.property && !frm.doc.propms_property) frm.set_value("propms_property", value.property);
				if (value.unit && !frm.doc.propms_unit) frm.set_value("propms_unit", value.unit);
				if (value.customer && !frm.doc.propms_tenant) frm.set_value("propms_tenant", value.customer);
			}
		);
	},

	propms_unit: function(frm) {
		if (!frm.doc.propms_unit) return;
		frappe.db.get_value("Unit Master", frm.doc.propms_unit, "property", function(v) {
			if (v.property && !frm.doc.propms_property) frm.set_value("propms_property", v.property);
		});
	},

	refresh: function(frm) {
		if (frm.doc.propms_lease_agreement) {
			frm.add_custom_button(__("Open Lease Agreement"), function() {
				frappe.set_route("Form", "Lease Agreement", frm.doc.propms_lease_agreement);
			});

			frappe.db.get_value(
				"Lease Agreement",
				frm.doc.propms_lease_agreement,
				["linked_payment_count", "security_deposit", "security_deposit_status", "security_deposit_return_payment_entry", "docstatus"],
				function(la) {
					if (!la) return;

					if (flt(la.linked_payment_count) > 0) {
						frm.add_custom_button(
							__("Payment Entries ({0})", [la.linked_payment_count]),
							function() {
								frappe.set_route("List", "Payment Entry", {
									propms_lease_agreement: frm.doc.propms_lease_agreement,
									docstatus: 1
								});
							}
						);
					}

					if (
						la.docstatus === 1 &&
						flt(la.security_deposit) > 0 &&
						la.security_deposit_status === "Received" &&
						!la.security_deposit_return_payment_entry
					) {
						frm.add_custom_button(__("Return Security Deposit"), function() {
							frappe.call({
								method: "propms.property_management_solution.doctype.lease_agreement.lease_agreement.make_deposit_return_payment_entry",
								args: { lease_agreement: frm.doc.propms_lease_agreement },
								callback: function(r) {
									if (r.message) {
										frappe.show_alert(__("Payment Entry {0} created", [r.message]));
									}
								}
							});
						}, __("Create"));
					}
				}
			);
		}
	}
});
