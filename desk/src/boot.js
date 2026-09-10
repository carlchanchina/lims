import { frappeRequest } from "frappe-ui";

export async function initBoot() {
	if (window.__boot) return window.__boot;
	if (window.session_user) {
		window.__boot = {
			site_name: window.site_name,
			csrf_token: window.csrf_token,
			session_user: window.session_user,
			roles: window.roles || [],
			date_format: window.date_format,
			time_format: window.time_format,
			default_route: window.default_route || "/lims/dashboard",
			can_manage: window.can_manage,
		};
		return window.__boot;
	}
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
