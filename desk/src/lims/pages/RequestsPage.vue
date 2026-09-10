<template>
	<div class="p-6 max-w-6xl">
		<div class="flex items-center justify-between mb-4">
			<h1 class="text-xl font-semibold">检测请求</h1>
			<button
				class="px-3 py-2 rounded-lg bg-gray-900 text-white text-sm"
				@click="openNew = true"
			>
				新建检测请求
			</button>
		</div>

		<div class="mb-3">
			<select v-model="statusFilter" class="border border-gray-300 rounded-lg px-3 py-2" @change="load()">
				<option value="">全部状态</option>
				<option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
			</select>
		</div>

		<div class="bg-white border border-gray-200 rounded-xl overflow-hidden">
			<table class="w-full text-sm">
				<thead class="bg-gray-50 text-left text-gray-600">
					<tr>
						<th class="px-4 py-2">编号</th>
						<th class="px-4 py-2">客户</th>
						<th class="px-4 py-2">日期</th>
						<th class="px-4 py-2">状态</th>
						<th class="px-4 py-2">样品/报告</th>
						<th class="px-4 py-2">报价</th>
						<th class="px-4 py-2">定单</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="row in rows"
						:key="row.name"
						class="border-t border-gray-100 cursor-pointer hover:bg-gray-50"
						@click="open(row)"
					>
						<td class="px-4 py-2 text-blue-600">{{ row.name }}</td>
						<td class="px-4 py-2">{{ row.customer_name || row.customer }}</td>
						<td class="px-4 py-2">{{ row.transaction_date }}</td>
						<td class="px-4 py-2"><StatusBadge :status="row.status" /></td>
						<td class="px-4 py-2">{{ row.sample_count }} / {{ row.report_count }}</td>
						<td class="px-4 py-2">{{ row.quotation || "—" }}</td>
						<td class="px-4 py-2">{{ row.sales_order || "—" }}</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="7" class="px-4 py-8 text-center text-gray-400">暂无检测请求</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div
			v-if="openNew"
			class="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50"
			@click.self="openNew = false"
		>
			<div class="bg-white rounded-xl w-full max-w-lg p-5">
				<h2 class="text-lg font-semibold mb-4">新建检测请求</h2>
				<div class="space-y-3">
					<div>
						<label class="text-sm">客户</label>
						<input
							v-model="form.customer"
							list="customer-options"
							class="w-full border rounded-lg px-3 py-2 mt-1"
							@input="searchCustomers"
						/>
						<datalist id="customer-options">
							<option v-for="c in customers" :key="c.value" :value="c.value">{{ c.label }}</option>
						</datalist>
					</div>
					<div>
						<label class="text-sm">公司</label>
						<select v-model="form.company" class="w-full border rounded-lg px-3 py-2 mt-1">
							<option v-for="c in companies" :key="c.value" :value="c.value">{{ c.label }}</option>
						</select>
					</div>
					<div>
						<label class="text-sm">日期</label>
						<input type="date" v-model="form.transaction_date" class="w-full border rounded-lg px-3 py-2 mt-1" />
					</div>
				</div>
				<div class="flex justify-end gap-2 mt-5">
					<button class="px-3 py-2 rounded-lg border" @click="openNew = false">取消</button>
					<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" :disabled="saving" @click="create()">
						创建
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import StatusBadge from "../components/StatusBadge.vue";
import { apiMethods } from "../api";

const router = useRouter();
const rows = ref([]);
const statusFilter = ref("");
const statuses = ["草稿", "已报价", "待检测", "检测中", "已完成", "已取消"];
const openNew = ref(false);
const saving = ref(false);
const customers = ref([]);
const companies = ref([]);
const form = reactive({
	customer: "",
	company: "",
	transaction_date: new Date().toISOString().slice(0, 10),
});

onMounted(async () => {
	await load();
	companies.value = (await apiMethods.companyOptions()) || [];
	customers.value = (await apiMethods.customerSearch("")) || [];
});

async function load() {
	const filters = statusFilter.value ? { status: statusFilter.value } : {};
	rows.value = (await apiMethods.requestsList(filters)) || [];
}

async function searchCustomers(event) {
	customers.value = (await apiMethods.customerSearch(event.target.value)) || [];
}

function open(row) {
	router.push(`/lims/requests/${row.name}`);
}

async function create() {
	saving.value = true;
	try {
		const res = await apiMethods.requestSave({ ...form });
		openNew.value = false;
		router.push(`/lims/requests/${res.name}`);
	} finally {
		saving.value = false;
	}
}
</script>
