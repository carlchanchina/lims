<template>
	<div class="p-6 max-w-6xl">
		<div class="grid grid-cols-3 md:grid-cols-6 gap-3 mb-6">
			<div v-for="item in statusItems" :key="item.status" class="bg-white border border-gray-200 rounded-xl p-4">
				<div class="text-2xl font-semibold">{{ summary[item.status] || 0 }}</div>
				<div class="text-sm text-gray-500">{{ item.label }}</div>
			</div>
		</div>
		<div class="flex gap-3 mb-6">
			<RouterLink
				class="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm"
				to="/lims/requests"
			>
				新建检测请求
			</RouterLink>
			<RouterLink
				class="px-4 py-2 rounded-lg border text-gray-700 text-sm"
				to="/lims/reports"
			>
				新建报告
			</RouterLink>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<section class="bg-white border border-gray-200 rounded-xl p-4">
				<h2 class="font-medium mb-2">检测中请求</h2>
				<ul v-if="pending.in_progress?.length" class="space-y-2">
					<li v-for="row in pending.in_progress" :key="row.name">
						<RouterLink class="text-blue-600 hover:underline" :to="`/lims/requests/${row.name}`">
							{{ row.name }}
						</RouterLink>
					</li>
				</ul>
				<p v-else class="text-sm text-gray-400">无</p>
			</section>
			<section class="bg-white border border-gray-200 rounded-xl p-4">
				<h2 class="font-medium mb-2">未出报告请求</h2>
				<ul v-if="pending.pending_reports?.length" class="space-y-2">
					<li v-for="row in pending.pending_reports" :key="row.name">
						<RouterLink class="text-blue-600 hover:underline" :to="`/lims/requests/${row.name}`">
							{{ row.name }}
						</RouterLink>
					</li>
				</ul>
				<p v-else class="text-sm text-gray-400">无</p>
			</section>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { apiMethods } from "../api";

const summary = ref({});
const pending = ref({ in_progress: [], pending_reports: [] });
const statusItems = [
	{ status: "草稿", label: "草稿" },
	{ status: "已报价", label: "已报价" },
	{ status: "待检测", label: "待检测" },
	{ status: "检测中", label: "检测中" },
	{ status: "已完成", label: "已完成" },
	{ status: "已取消", label: "已取消" },
];

onMounted(async () => {
	summary.value = (await apiMethods.dashboardSummary()) || {};
	pending.value = (await apiMethods.dashboardPending()) || pending.value;
});
</script>
