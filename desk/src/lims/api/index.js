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
	agreementPriceList: (filters = {}) =>
		api("test.api.master.get_agreement_prices", { filters }),
	agreementPriceGet: (name) =>
		api("test.api.master.get_agreement_price", { name }),
	agreementPriceSave: (data) =>
		api("test.api.master.save_agreement_price", { data }),
	agreementPriceDelete: (name) =>
		api("test.api.master.delete_agreement_price", { name }),
	industryList: () => api("test.api.master.get_industries"),
	industryCreate: (data) => api("test.api.parties.create_industry", { data }),
	customerSearch: (txt) => api("test.api.reference.customer_search", { txt }),
	itemSearch: (txt) => api("test.api.reference.item_search", { txt }),
	itemsList: (txt) => api("test.api.items.list_items", { txt }),
	itemCreate: (data) => api("test.api.items.create_item", { data }),
	itemFormOptions: () => api("test.api.items.get_item_form_options"),
	companyOptions: () => api("test.api.reference.company_options"),
	userOptions: (txt) => api("test.api.reference.user_options", { txt }),
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
	reportDelete: (name) => api("test.api.reports.delete_report", { name }),
	reportItemDefaults: (test_request, test_request_item) =>
		api("test.api.reports.report_item_defaults", {
			test_request,
			test_request_item,
		}),
	usageList: (test_request) =>
		api("test.api.quality.list_equipment_usage", { test_request }),
	usageCreate: (data) => api("test.api.quality.create_equipment_usage", { data }),
	calibrationStates: (assets) =>
		api("test.api.quality.calibration_states", { assets }),
	nonconformanceList: (test_request) =>
		api("test.api.quality.list_nonconformances", { test_request }),
	nonconformanceSave: (data) =>
		api("test.api.quality.save_nonconformance", { data }),
	globalSearch: (txt) => api("test.api.search.global_search", { txt }),
	notifications: () => api("test.api.notifications.list_notifications"),
	assetsList: (txt) => api("test.api.assets.list_assets", { txt }),
	assetCreate: (data) => api("test.api.assets.create_asset", { data }),
	assetFormOptions: () => api("test.api.assets.asset_form_options"),
	customersList: (txt) => api("test.api.parties.list_customers", { txt }),
	customerGet: (name) => api("test.api.parties.get_customer", { name }),
	customerCreate: (data) => api("test.api.parties.create_customer", { data }),
	contactsList: (customer) => api("test.api.parties.list_contacts", { customer }),
	contactsSearch: (txt, customer) =>
		api("test.api.parties.search_contacts", { txt, customer }),
	contactCreate: (data) => api("test.api.parties.create_contact", { data }),
	partyFormOptions: () => api("test.api.parties.party_form_options"),
	quotationSearch: (txt, customer) =>
		api("test.api.orders.search_quotations", { txt, customer }),
	salesOrderSearch: (txt, customer) =>
		api("test.api.orders.search_sales_orders", { txt, customer }),
	quotationLink: (name, quotation) =>
		api("test.api.orders.link_quotation", { name, quotation }),
	salesOrderLink: (name, sales_order) =>
		api("test.api.orders.link_sales_order", { name, sales_order }),
	salesOrderCreate: (name) => api("test.api.orders.create_sales_order", { name }),
	requestFromSalesOrder: (data) =>
		api("test.api.orders.create_request_from_sales_order", { data }),
	plansList: (filters = {}) => api("test.api.plans.list_plans", { filters }),
	planGet: (name) => api("test.api.plans.get_plan", { name }),
	planSave: (data) => api("test.api.plans.save_plan", { data }),
	planGenerate: (test_request) =>
		api("test.api.plans.generate_plan_from_request", { test_request }),
};
