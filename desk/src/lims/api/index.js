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
	dashboardSummary: () => api("lims.api.dashboard.get_summary"),
	dashboardPending: () => api("lims.api.dashboard.get_pending"),
	standardsList: (filters = {}) => api("lims.api.master.get_standards", { filters }),
	standardGet: (name) => api("lims.api.master.get_standard", { name }),
	standardSave: (data) => api("lims.api.master.save_standard", { data }),
	standardDelete: (name) => api("lims.api.master.delete_standard", { name }),
	agreementPriceList: (filters = {}) =>
		api("lims.api.master.get_agreement_prices", { filters }),
	agreementPriceGet: (name) =>
		api("lims.api.master.get_agreement_price", { name }),
	agreementPriceSave: (data) =>
		api("lims.api.master.save_agreement_price", { data }),
	agreementPriceDelete: (name) =>
		api("lims.api.master.delete_agreement_price", { name }),
	industryList: () => api("lims.api.master.get_industries"),
	industryCreate: (data) => api("lims.api.parties.create_industry", { data }),
	customerSearch: (txt) => api("lims.api.reference.customer_search", { txt }),
	itemSearch: (txt) => api("lims.api.reference.item_search", { txt }),
	itemsList: (txt) => api("lims.api.items.list_items", { txt }),
	itemCreate: (data) => api("lims.api.items.create_item", { data }),
	itemFormOptions: () => api("lims.api.items.get_item_form_options"),
	companyOptions: () => api("lims.api.reference.company_options"),
	userOptions: (txt) => api("lims.api.reference.user_options", { txt }),
	erpnextUrl: (doctype, name) =>
		api("lims.api.reference.get_erpnext_url", { doctype, name }),
	requestsList: (filters = {}) => api("lims.api.requests.list_requests", { filters }),
	requestGet: (name) => api("lims.api.requests.get_request", { name }),
	requestSave: (data) => api("lims.api.requests.save_request", { data }),
	requestAction: (name, action) =>
		api("lims.api.requests.request_action", { name, action }),
	requestQuotation: (name) =>
		api("lims.api.requests.request_action", {
			name,
			action: "generate_quotation",
		}),
	samplesList: (test_request) =>
		api("lims.api.samples.list_by_request", { test_request }),
	sampleCreate: (data) => api("lims.api.samples.create_sample", { data }),
	sampleUpdate: (data) => api("lims.api.samples.update_sample", { data }),
	sampleDelete: (name) => api("lims.api.samples.delete_sample", { name }),
	reportsList: (filters = {}) => api("lims.api.reports.list_reports", { filters }),
	reportGet: (name) => api("lims.api.reports.get_report", { name }),
	reportSave: (data) => api("lims.api.reports.save_report", { data }),
	reportDelete: (name) => api("lims.api.reports.delete_report", { name }),
	reportItemDefaults: (test_request, test_request_item) =>
		api("lims.api.reports.report_item_defaults", {
			test_request,
			test_request_item,
		}),
	usageList: (test_request) =>
		api("lims.api.quality.list_equipment_usage", { test_request }),
	usageCreate: (data) => api("lims.api.quality.create_equipment_usage", { data }),
	calibrationStates: (assets) =>
		api("lims.api.quality.calibration_states", { assets }),
	nonconformanceList: (test_request) =>
		api("lims.api.quality.list_nonconformances", { test_request }),
	nonconformanceSave: (data) =>
		api("lims.api.quality.save_nonconformance", { data }),
	globalSearch: (txt) => api("lims.api.search.global_search", { txt }),
	notifications: () => api("lims.api.notifications.list_notifications"),
	assetsList: (txt) => api("lims.api.assets.list_assets", { txt }),
	assetCreate: (data) => api("lims.api.assets.create_asset", { data }),
	assetFormOptions: () => api("lims.api.assets.asset_form_options"),
	customersList: (txt) => api("lims.api.parties.list_customers", { txt }),
	customerGet: (name) => api("lims.api.parties.get_customer", { name }),
	customerCreate: (data) => api("lims.api.parties.create_customer", { data }),
	contactsList: (customer) => api("lims.api.parties.list_contacts", { customer }),
	contactsSearch: (txt, customer) =>
		api("lims.api.parties.search_contacts", { txt, customer }),
	contactCreate: (data) => api("lims.api.parties.create_contact", { data }),
	partyFormOptions: () => api("lims.api.parties.party_form_options"),
	quotationSearch: (txt, customer) =>
		api("lims.api.orders.search_quotations", { txt, customer }),
	salesOrderSearch: (txt, customer) =>
		api("lims.api.orders.search_sales_orders", { txt, customer }),
	quotationLink: (name, quotation) =>
		api("lims.api.orders.link_quotation", { name, quotation }),
	salesOrderLink: (name, sales_order) =>
		api("lims.api.orders.link_sales_order", { name, sales_order }),
	salesOrderCreate: (name) => api("lims.api.orders.create_sales_order", { name }),
	requestFromSalesOrder: (data) =>
		api("lims.api.orders.create_request_from_sales_order", { data }),
	plansList: (filters = {}) => api("lims.api.plans.list_plans", { filters }),
	planGet: (name) => api("lims.api.plans.get_plan", { name }),
	planSave: (data) => api("lims.api.plans.save_plan", { data }),
	planGenerate: (test_request) =>
		api("lims.api.plans.generate_plan_from_request", { test_request }),
};
