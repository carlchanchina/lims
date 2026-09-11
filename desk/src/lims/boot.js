import { frappeRequest } from "frappe-ui";

export async function initBoot() {
	if (window.__boot) {
		window.csrf_token = window.__boot.csrf_token;
		window.session_user = window.__boot.session_user;
		return window.__boot;
	}
	const res = await frappeRequest({
		method: "GET",
		url: "/api/method/lims.www.lims.index.get_boot_data",
	});
	window.__boot = res.message;
	window.csrf_token = res.message.csrf_token;
	window.session_user = res.message.session_user;
	return window.__boot;
}

export function getBoot() {
	return window.__boot || {};
}
