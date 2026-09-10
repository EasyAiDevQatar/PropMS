// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Maintenance Request", {
	setup: function(frm) {
		frm.set_query("unit", function() {
			const filters = {};
			if (frm.doc.property) filters.property = frm.doc.property;
			return { filters };
		});

		frm.set_query("technician", function() {
			return { filters: { status: "Active" } };
		});
	},

	refresh: function(frm) {
		if (
			frm.doc.docstatus === 1 &&
			!frm.doc.journal_entry &&
			flt(frm.doc.total_cost) > 0
		) {
			frm.add_custom_button(__("Create Journal Entry"), function() {
				frappe.call({
					method: "propms.property_management_solution.doctype.maintenance_request.maintenance_request.make_journal_entry",
					args: { maintenance_request: frm.doc.name },
					callback: function(r) {
						if (r.message) {
							frappe.show_alert(__("Journal Entry {0} created", [r.message]));
							frm.reload_doc();
						}
					}
				});
			}, __("Create"));
		}

		if (frm.doc.journal_entry) {
			frm.add_custom_button(__("Open Journal Entry"), function() {
				frappe.set_route("Form", "Journal Entry", frm.doc.journal_entry);
			});
		}
	},

	unit: function(frm) {
		if (!frm.doc.unit) return;
		frappe.db.get_value("Unit Master", frm.doc.unit, "property", function(v) {
			if (v.property && !frm.doc.property) frm.set_value("property", v.property);
		});
	}
});

frappe.ui.form.on("Maintenance Request Item", {
	rate: function(frm, cdt, cdn) { recalc(frm, cdt, cdn); },
	qty: function(frm, cdt, cdn) { recalc(frm, cdt, cdn); }
});

function recalc(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	row.amount = (row.qty || 1) * (row.rate || 0);
	frm.refresh_field("items");
	let total = 0;
	(frm.doc.items || []).forEach(r => total += (r.amount || 0));
	frm.set_value("total_cost", total);
}
