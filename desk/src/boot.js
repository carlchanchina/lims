import { frappeRequest } from "frappe-ui";

export async function initBoot() {
	if (window.__boot) return window.__boot;
	const res = await frappeRequest({
		method: "POST",
		url: "/api/method/test.www.lims.index.get_context_for_dev",
	});
	window.__boot = res.message;
	return window.__boot;
}

export function getBoot() {
	return window.__boot || {};
}
