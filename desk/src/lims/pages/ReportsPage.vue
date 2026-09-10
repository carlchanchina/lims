<template>
	<div class="p-6 max-w-6xl">
		<div class="flex items-center justify-end mb-4">
			<button class="px-3 py-2 rounded-lg bg-gray-900 text-white text-sm" @click="openNew()">
				新建报告
			</button>
		</div>

		<div class="bg-white border border-gray-200 rounded-xl overflow-hidden">
			<table class="w-full text-sm">
				<thead class="bg-gray-50 text-left text-gray-600">
					<tr>
						<th class="px-4 py-2">编号</th>
						<th class="px-4 py-2">检测请求</th>
						<th class="px-4 py-2">样品</th>
						<th class="px-4 py-2">日期</th>
						<th class="px-4 py-2">状态</th>
						<th class="px-4 py-2"></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-gray-100">
						<td class="px-4 py-2">{{ row.name }}</td>
						<td class="px-4 py-2">
							<RouterLink class="text-blue-600" :to="`/lims/requests/${row.test_request}`">
								{{ row.test_request }}
							</RouterLink>
						</td>
						<td class="px-4 py-2">{{ row.sample_name || row.sample || "—" }}</td>
						<td class="px-4 py-2">{{ row.report_date }}</td>
						<td class="px-4 py-2"><StatusBadge :status="row.status" /></td>
						<td class="px-4 py-2 text-right">
							<button class="text-blue-600 hover:underline" @click="openEdit(row)">编辑</button>
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="6" class="px-4 py-8 text-center text-gray-400">暂无报告</td>
					</tr>
				</tbody>
			</table>
		</div>

		<Modal v-if="showModal" title="检测报告" @close="showModal = false">
			<div class="space-y-2">
				<div>
					<label class="text-sm text-gray-700">检测请求</label>
					<select v-model="form.test_request" class="w-full border rounded-lg px-3 py-2" @change="onRequestChange">
						<option v-for="r in requests" :key="r.name" :value="r.name">{{ r.name }}</option>
					</select>
				</div>
				<div>
					<label class="text-sm text-gray-700">样品</label>
					<select v-model="form.sample" class="w-full border rounded-lg px-3 py-2">
						<option value="">—</option>
						<option v-for="s in sampleOptions" :key="s.name" :value="s.name">{{ s.sample_name }}</option>
					</select>
				</div>
				<div>
					<label class="text-sm text-gray-700">日期</label>
					<input type="date" v-model="form.report_date" class="w-full border rounded-lg px-3 py-2" />
				</div>
				<div>
					<label class="text-sm text-gray-700">状态</label>
					<select v-model="form.status" class="w-full border rounded-lg px-3 py-2">
						<option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
					</select>
				</div>
				<div>
					<label class="text-sm text-gray-700">检测项目</label>
					<input v-model="form.item" class="w-full border rounded-lg px-3 py-2" placeholder="ERPNext Item 编码" />
				</div>
				<div>
					<label class="text-sm text-gray-700">检测标准</label>
					<select v-model="form.standard" class="w-full border rounded-lg px-3 py-2">
						<option value="">—</option>
						<option v-for="s in standards" :key="s.name" :value="s.name">{{ s.standard_code }}</option>
					</select>
				</div>
				<div>
					<label class="text-sm text-gray-700">设备</label>
					<select v-model="form.equipment" class="w-full border rounded-lg px-3 py-2">
						<option value="">—</option>
						<option v-for="e in equipment" :key="e.name" :value="e.name">{{ e.equipment_name }}</option>
					</select>
				</div>
				<div>
					<label class="text-sm text-gray-700">检测人</label>
					<input v-model="form.tested_by" class="w-full border rounded-lg px-3 py-2" placeholder="User email" />
				</div>
				<div>
					<label class="text-sm text-gray-700">检测结论</label>
					<textarea v-model="form.conclusion" rows="4" class="w-full border rounded-lg px-3 py-2"></textarea>
				</div>
				<div>
					<label class="text-sm text-gray-700">备注</label>
					<textarea v-model="form.remarks" rows="2" class="w-full border rounded-lg px-3 py-2"></textarea>
				</div>
			</div>
			<div class="flex justify-end gap-2 mt-4">
				<button class="px-3 py-2 rounded-lg border" @click="showModal = false">取消</button>
				<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="save">保存</button>
			</div>
		</Modal>
	</div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import Modal from "../components/Modal.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { apiMethods } from "../api";

const rows = ref([]);
const route = useRoute();
const showModal = ref(false);
const form = reactive({});
const requests = ref([]);
const sampleOptions = ref([]);
const standards = ref([]);
const equipment = ref([]);
const statuses = ["待检测", "检测中", "已出具", "已作废"];

onMounted(async () => {
	await load();
	requests.value = (await apiMethods.requestsList({})) || [];
	standards.value = (await apiMethods.standardsList({})) || [];
	equipment.value = (await apiMethods.equipmentList({})) || [];

	const presetRequest = sessionStorage.getItem("lims_new_report_request");
	if (presetRequest) {
		sessionStorage.removeItem("lims_new_report_request");
		openNew(presetRequest);
		return;
	}
	if (route.query.report) {
		const report = await apiMethods.reportGet(route.query.report);
		await openEdit(report);
	}
});

async function load() {
	rows.value = (await apiMethods.reportsList({})) || [];
}

async function openNew(presetRequest = "") {
	Object.keys(form).forEach((k) => delete form[k]);
	form.report_date = new Date().toISOString().slice(0, 10);
	form.status = "待检测";
	form.test_request = presetRequest;
	showModal.value = true;
	if (presetRequest) await onRequestChange();
}

async function openEdit(row) {
	Object.assign(form, row);
	showModal.value = true;
	await onRequestChange();
}

async function onRequestChange() {
	sampleOptions.value = form.test_request
		? (await apiMethods.samplesList(form.test_request)) || []
		: [];
}

async function save() {
	await apiMethods.reportSave({ ...form });
	showModal.value = false;
	await load();
}
</script>
