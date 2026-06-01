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
		}
	}
});
