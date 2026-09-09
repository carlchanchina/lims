<template>
	<aside class="w-60 shrink-0 border-r border-gray-200 bg-white flex flex-col">
		<div class="px-5 py-4 border-b border-gray-100">
			<div class="font-semibold text-gray-900">环境试验 LIMS</div>
			<div class="text-xs text-gray-500">{{ boot.session_user }}</div>
		</div>
		<nav class="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
			<RouterLink
				v-for="item in items"
				:key="item.to"
				:to="item.to"
				class="block px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
				:class="{ 'bg-gray-900 text-white hover:bg-gray-900': isActive(item.to) }"
			>
				{{ item.label }}
			</RouterLink>
		</nav>
		<div class="p-3 text-sm">
			<a class="block px-3 py-2 text-gray-500 hover:text-gray-900" href="/api/method/logout">
				退出登录
			</a>
		</div>
	</aside>
</template>

<script setup>
import { RouterLink, useRoute } from "vue-router";
import { getBoot } from "../boot";

const route = useRoute();
const boot = getBoot();
const items = [
	{ label: "仪表盘", to: "/lims/dashboard" },
	{ label: "检测请求", to: "/lims/requests" },
	{ label: "检测报告", to: "/lims/reports" },
	{ label: "测试标准", to: "/lims/standards" },
	{ label: "设备", to: "/lims/equipment" },
	{ label: "报价目录", to: "/lims/catalog" },
];

function isActive(to) {
	return route.path.startsWith(to);
}
</script>
