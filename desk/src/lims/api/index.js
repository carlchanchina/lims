import { frappeRequest } from "frappe-ui";

export async function api(method, args = {}) {
	try {
		const res = await frappeRequest({
			method: "POST",
			url: `/api/method/${method}`,
			args,
		});
		return res.message;
	} catch (error) {
		throw error;
	}
}

export const apiMethods = {
	dashboardSummary: () => api("test.api.dashboard.get_summary"),
	dashboardPending: () => api("test.api.dashboard.get_pending"),
	standardsList: (filters = {}) => api("test.api.master.get_standards", { filters }),
	standardGet: (name) => api("test.api.master.get_standard", { name }),
	standardSave: (data) => api("test.api.master.save_standard", { data }),
	standardDelete: (name) => api("test.api.master.delete_standard", { name }),
	equipmentList: (filters = {}) =>
		api("test.api.master.get_equipment_list", { filters }),
	equipmentGet: (name) => api("test.api.master.get_equipment", { name }),
	equipmentSave: (data) => api("test.api.master.save_equipment", { data }),
	equipmentDelete: (name) => api("test.api.master.delete_equipment", { name }),
	catalogList: (filters = {}) => api("test.api.master.get_catalog_list", { filters }),
	catalogGet: (name) => api("test.api.master.get_catalog", { name }),
	catalogSave: (data) => api("test.api.master.save_catalog", { data }),
	catalogDelete: (name) => api("test.api.master.delete_catalog", { name }),
	catalogSetDefault: (name) =>
		api("test.api.master.set_default_catalog", { name }),
	customerSearch: (txt) => api("test.api.reference.customer_search", { txt }),
	itemSearch: (txt) => api("test.api.reference.item_search", { txt }),
	companyOptions: () => api("test.api.reference.company_options"),
	erpnextUrl: (doctype, name) =>
		api("test.api.reference.get_erpnext_url", { doctype, name }),
	requestsList: (filters = {}) => api("test.api.requests.list_requests", { filters }),
	requestGet: (name) => api("test.api.requests.get_request", { name }),
	requestSave: (data) => api("test.api.requests.save_request", { data }),
	requestAction: (name, action) =>
		api("test.api.requests.request_action", { name, action }),
	requestQuotation: (name) =>
		api("test.api.requests.request_action", {
			name,
			action: "generate_quotation",
		}),
	samplesList: (test_request) =>
		api("test.api.samples.list_by_request", { test_request }),
	sampleCreate: (data) => api("test.api.samples.create_sample", { data }),
	sampleUpdate: (data) => api("test.api.samples.update_sample", { data }),
	sampleDelete: (name) => api("test.api.samples.delete_sample", { name }),
	reportsList: (filters = {}) => api("test.api.reports.list_reports", { filters }),
	reportGet: (name) => api("test.api.reports.get_report", { name }),
	reportSave: (data) => api("test.api.reports.save_report", { data }),
};
