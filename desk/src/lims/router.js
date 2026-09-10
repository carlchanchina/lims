import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{ path: "/", redirect: "/lims/dashboard" },
	{ path: "/lims", redirect: "/lims/dashboard" },
	{
		path: "/lims/dashboard",
		component: () => import("./pages/DashboardPage.vue"),
		meta: { title: "仪表盘" },
	},
	{
		path: "/lims/standards",
		component: () => import("./pages/StandardsPage.vue"),
		meta: { title: "测试标准" },
	},
	{
		path: "/lims/equipment",
		component: () => import("./pages/EquipmentPage.vue"),
		meta: { title: "设备" },
	},
	{
		path: "/lims/catalog",
		component: () => import("./pages/CatalogPage.vue"),
		meta: { title: "报价目录" },
	},
	{
		path: "/lims/requests",
		component: () => import("./pages/RequestsPage.vue"),
		meta: { title: "检测请求" },
	},
	{
		path: "/lims/requests/:name",
		component: () => import("./pages/RequestDetailPage.vue"),
		meta: { title: "检测请求详情", back: true, parentTitle: "检测请求" },
	},
	{
		path: "/lims/reports",
		component: () => import("./pages/ReportsPage.vue"),
		meta: { title: "检测报告" },
	},
];

export const router = createRouter({
	history: createWebHistory(),
	routes,
});
