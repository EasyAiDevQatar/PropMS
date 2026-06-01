// Copyright (c) 2018, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Property', {
	refresh: function(frm) {
		if (frm.doc.disabled) {
			frm.dashboard.set_headline_alert(__("This property is disabled - it is not currently managed."));
		}
	},
	setup: function(frm) {
		frm.set_query("cost_center", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				},
			};
		});

		frm.set_query("parent_property", {is_group: 1});

		frm.set_query("property_owner", function() {
			return { filters: { disabled: 0 } };
		});
		frm.set_query("unit_owner", function() {
			return { filters: { disabled: 0 } };
		});
	},
	company: function(frm) {
		frm.set_value("cost_center", "");
	},
	disabled: function(frm) {
		if (!frm.doc.disabled) return;

		frappe.call({
			method: "propms.property_management_solution.doctype.property.property.get_active_leases",
			args: { property_name: frm.doc.name },
			callback: function(r) {
				const active = (r.message || []);
				if (!active.length) return;

				const list_html = active.map(l => `<li><a href="/app/lease-agreement/${l.name}">${l.name}</a> - ${l.status}</li>`).join("");
				frappe.confirm(
					__("This property has {0} active/draft Lease Agreement(s):", [active.length]) +
						`<ul>${list_html}</ul>` +
						__("Disabling means we no longer manage it. Cancel these leases first?"),
					function() {
						frappe.set_route("List", "Lease Agreement", { property: frm.doc.name });
					},
					function() {
						frm.set_value("disabled", 0);
						frappe.show_alert(__("Disable cancelled."));
					}
				);
			}
		});
	}
});

frappe.ui.form.on('Property Meter Reading', {
    meter_number: function(frm,cdt,cdn) {
		var property_doc = locals[cur_frm.doc.doctype][cur_frm.doc.name];
		var meter_doc = locals[cdt][cdn];
		if (meter_doc.meter_number != "") {
			$.each(property_doc.property_meter_reading, function(i, d) {
				if(d.name!=meter_doc.name && meter_doc.meter_type==d.meter_type && d.status=="Active")	{
					var msg="Another Active Meter of type "+meter_doc.meter_type+" Is Already allocated. Please de-activate it before adding a new meter of same type."
					frappe.model.set_value(cdt,cdn,"meter_number",'')
					frappe.throw(msg)
				}
			})
		}
	},
	status: function(frm,cdt,cdn) {
		var property_doc = locals[cur_frm.doc.doctype][cur_frm.doc.name];
		var meter_doc = locals[cdt][cdn];
		if (meter_doc.meter_number != "") {
			$.each(property_doc.property_meter_reading, function(i, d) {
				if(d.name!=meter_doc.name && meter_doc.meter_type==d.meter_type && d.status=="Active")	{
					var msg="Another Active Meter of type "+meter_doc.meter_type+" Is Already allocated. Please de-activate it before adding a new meter of same type."
					frappe.model.set_value(cdt,cdn,"status",'')
					frappe.throw(msg)
				}
			})
		}
	}
})
