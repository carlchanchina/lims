import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{ path: "/", redirect: "/lims/dashboard" },
	{ path: "/lims", redirect: "/lims/dashboard" },
	{ path: "/lims/dashboard", component: () => import("./pages/DashboardPage.vue") },
	{ path: "/lims/standards", component: () => import("./pages/StandardsPage.vue") },
	{ path: "/lims/equipment", component: () => import("./pages/EquipmentPage.vue") },
	{ path: "/lims/catalog", component: () => import("./pages/CatalogPage.vue") },
	{ path: "/lims/requests", component: () => import("./pages/RequestsPage.vue") },
	{
		path: "/lims/requests/:name",
		component: () => import("./pages/RequestDetailPage.vue"),
	},
	{ path: "/lims/reports", component: () => import("./pages/ReportsPage.vue") },
];

export const router = createRouter({
	history: createWebHistory(),
	routes,
});
