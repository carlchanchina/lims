<template>
	<div class="p-6">
		<div class="mb-4 flex flex-wrap items-center gap-3">
			<input
				v-model="query"
				placeholder="搜索报价单号/客户"
				class="w-72 rounded-lg border border-outline-gray-2 px-3 py-2"
				@input="load"
			/>
			<span class="text-sm text-ink-gray-5">报价单是 ERPNext 单据,这里只读列表;新建请从委托请求「生成报价」或在 ERPNext 新建</span>
			<a
				href="/app/quotation/new"
				target="_blank"
				class="ml-auto rounded-lg bg-ink-gray-9 px-3 py-2 text-sm text-white"
			>+ 在 ERPNext 新建报价</a>
		</div>
		<div class="overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-base">
			<table class="w-full text-sm">
				<thead class="bg-surface-gray-1">
					<tr>
						<th class="px-4 py-2 text-start">报价单号</th>
						<th class="px-4 py-2 text-start">客户</th>
						<th class="px-4 py-2 text-start">日期</th>
						<th class="px-4 py-2 text-end">金额</th>
						<th class="px-4 py-2 text-start">状态</th>
						<th class="px-4 py-2 text-start">LIMS 委托</th>
						<th class="px-4 py-2"></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-outline-gray-1">
						<td class="px-4 py-2 font-medium text-ink-gray-9">{{ row.name }}</td>
						<td class="px-4 py-2">{{ row.customer }}</td>
						<td class="px-4 py-2">{{ row.transaction_date }}</td>
						<td class="px-4 py-2 text-end">
							{{ fmt(row.grand_total) }} {{ row.currency }}
						</td>
						<td class="px-4 py-2">
							<span :class="statusClass(row)">{{ statusLabel(row) }}</span>
						</td>
						<td class="px-4 py-2">
							<RouterLink
								v-if="row.lims_test_request"
								:to="`/lims/requests/${row.lims_test_request}`"
								class="text-sm text-ink-gray-7 underline"
							>{{ row.lims_test_request }}</RouterLink>
							<span v-else class="text-ink-gray-4">—</span>
						</td>
						<td class="px-4 py-2 text-end">
							<a :href="`/app/quotation/${row.name}`" target="_blank" class="text-sm text-ink-gray-7 underline">在 ERPNext 打开</a>
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="7" class="px-4 py-8 text-center text-ink-gray-4">暂无报价单</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiMethods } from "../api";

const rows = ref([]);
const query = ref("");

onMounted(load);

async function load() {
	rows.value = (await apiMethods.quotationList(query.value)) || [];
}

function fmt(value) {
	if (value == null) return "0";
	return Number(value).toLocaleString(undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
}

function statusLabel(row) {
	if (row.docstatus === 2) return "已作废";
	if (row.docstatus === 1) return "已提交";
	return "草稿";
}

function statusClass(row) {
	if (row.docstatus === 2) return "rounded px-1.5 py-0.5 text-xs text-ink-gray-4";
	if (row.docstatus === 1) return "rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700";
	return "rounded bg-yellow-100 px-1.5 py-0.5 text-xs text-yellow-700";
}
</script>
