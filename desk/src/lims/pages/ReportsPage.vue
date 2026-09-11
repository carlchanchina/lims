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
						<th class="px-4 py-2">报告项</th>
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
						<td class="px-4 py-2">{{ row.sample || "整单" }}</td>
						<td class="px-4 py-2">{{ row.report_date }}</td>
						<td class="px-4 py-2">{{ row.item_count }}</td>
						<td class="px-4 py-2"><StatusBadge :status="row.status" /></td>
						<td class="px-4 py-2 text-right">
							<button class="text-blue-600 hover:underline" @click="openEdit(row)">编辑</button>
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="7" class="px-4 py-8 text-center text-gray-400">暂无报告</td>
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
				<div class="flex gap-2">
					<div class="w-1/2">
						<label class="text-sm text-gray-700">样品</label>
						<select v-model="form.sample" class="w-full border rounded-lg px-3 py-2">
							<option value="">整单</option>
							<option v-for="s in sampleOptions" :key="s.name" :value="s.name">{{ s.sample_name }}</option>
						</select>
					</div>
					<div class="w-1/2">
						<label class="text-sm text-gray-700">报告日期</label>
						<input type="date" v-model="form.report_date" class="w-full border rounded-lg px-3 py-2" />
					</div>
				</div>
				<div class="flex gap-2">
					<div class="w-1/2">
						<label class="text-sm text-gray-700">状态</label>
						<select v-model="form.status" class="w-full border rounded-lg px-3 py-2">
							<option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
						</select>
					</div>
					<div class="w-1/2">
						<label class="text-sm text-gray-700">签发日期</label>
						<input type="date" v-model="form.issued_on" class="w-full border rounded-lg px-3 py-2" />
					</div>
				</div>

				<div class="rounded-lg border border-gray-200">
					<div class="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-3 py-2">
						<span class="text-sm font-medium">报告项</span>
						<button class="text-sm text-blue-600 hover:underline" @click="addItemRow()">+ 添加报告项</button>
					</div>
					<div v-for="(row, index) in form.items" :key="index" class="border-b border-gray-100 p-3 last:border-b-0">
						<div class="mb-2 flex items-center gap-2">
							<select
								v-model="row.test_request_item"
								class="flex-1 border rounded px-2 py-1 text-sm"
								@change="applyItemDefaults(index)"
							>
								<option value="">选择试验项目行</option>
								<option v-for="item in requestItems" :key="item.name" :value="item.name">
									{{ item.item_name || item.item }}
								</option>
							</select>
							<button class="text-sm text-red-600" @click="form.items.splice(index, 1)">移除</button>
						</div>
						<div class="grid grid-cols-2 gap-2">
							<input v-model="row.item" placeholder="检测项目(Item)" class="border rounded px-2 py-1 text-sm" />
							<input v-model="row.standard" placeholder="检测标准" class="border rounded px-2 py-1 text-sm" />
							<input v-model="row.standard_clause" placeholder="标准条款" class="border rounded px-2 py-1 text-sm" />
							<input v-model="row.sample" placeholder="样品" class="border rounded px-2 py-1 text-sm" />
							<input v-model="row.equipment" placeholder="设备(Asset)" class="border rounded px-2 py-1 text-sm" />
							<select v-model="row.verdict" class="border rounded px-2 py-1 text-sm">
								<option v-for="v in verdicts" :key="v" :value="v">{{ v }}</option>
							</select>
						</div>
						<textarea
							v-model="row.requirement"
							placeholder="技术要求 / 判定依据"
							class="mt-2 w-full border rounded px-2 py-1 text-sm"
							rows="2"
						></textarea>
						<textarea
							v-model="row.result"
							placeholder="实测结果 / 试验现象"
							class="mt-2 w-full border rounded px-2 py-1 text-sm"
							rows="2"
						></textarea>
					</div>
					<p v-if="!form.items?.length" class="p-3 text-center text-sm text-gray-400">还没有报告项</p>
				</div>

				<div class="flex gap-2">
					<div class="w-1/2">
						<label class="text-sm text-gray-700">检测人</label>
						<input v-model="form.tested_by" list="user-options" class="w-full border rounded-lg px-3 py-2" />
					</div>
					<div class="w-1/2">
						<label class="text-sm text-gray-700">审核人</label>
						<input v-model="form.reviewed_by" list="user-options" class="w-full border rounded-lg px-3 py-2" />
					</div>
				</div>
				<div class="flex gap-2">
					<div class="w-1/2">
						<label class="text-sm text-gray-700">批准人</label>
						<input v-model="form.approved_by" list="user-options" class="w-full border rounded-lg px-3 py-2" />
					</div>
				</div>
				<datalist id="user-options">
					<option v-for="u in users" :key="u.value" :value="u.value">{{ u.label }}</option>
				</datalist>

				<div>
					<label class="text-sm text-gray-700">检测结论</label>
					<textarea v-model="form.conclusion" rows="3" class="w-full border rounded-lg px-3 py-2"></textarea>
				</div>
				<div>
					<label class="text-sm text-gray-700">备注</label>
					<textarea v-model="form.remarks" rows="2" class="w-full border rounded-lg px-3 py-2"></textarea>
				</div>
			</div>

			<p v-if="error" class="mt-3 whitespace-pre-line text-sm text-red-600">{{ error }}</p>

			<div class="mt-4 flex justify-end gap-2">
				<button class="rounded-lg border px-3 py-2" @click="showModal = false">取消</button>
				<button class="rounded-lg bg-gray-900 px-3 py-2 text-white" :disabled="saving" @click="save()">
					保存
				</button>
			</div>
		</Modal>
	</div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import Modal from "../components/Modal.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { extractFrappeError } from "../errors";
import { apiMethods } from "../api";

const rows = ref([]);
const route = useRoute();
const showModal = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({ items: [] });
const requests = ref([]);
const sampleOptions = ref([]);
const requestItems = ref([]);
const users = ref([]);
const statuses = ["待检测", "检测中", "已出具", "已作废"];
const verdicts = ["待判定", "合格", "不合格", "不适用"];

onMounted(async () => {
	await load();
	requests.value = (await apiMethods.requestsList({})) || [];
	users.value = (await apiMethods.userOptions()) || [];

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
	const { items, ...rest } = form;
	Object.keys(rest).forEach((key) => delete form[key]);
	form.items = [];
	form.report_date = new Date().toISOString().slice(0, 10);
	form.status = "待检测";
	form.test_request = presetRequest;
	showModal.value = true;
	if (presetRequest) await onRequestChange();
}

async function openEdit(row) {
	const report = row.items ? row : await apiMethods.reportGet(row.name);
	Object.keys(form).forEach((key) => delete form[key]);
	Object.assign(form, report);
	form.items = (report.items || []).map((item) => ({ ...item }));
	showModal.value = true;
	await onRequestChange();
}

async function onRequestChange() {
	sampleOptions.value = form.test_request
		? (await apiMethods.samplesList(form.test_request)) || []
		: [];
	const request = form.test_request
		? await apiMethods.requestGet(form.test_request)
		: null;
	requestItems.value = request?.items || [];
}

async function addItemRow() {
	form.items.push({ test_request_item: "", verdict: "待判定" });
}

async function applyItemDefaults(index) {
	const row = form.items[index];
	if (!row.test_request_item) return;
	const defaults = await apiMethods.reportItemDefaults(
		form.test_request,
		row.test_request_item
	);
	Object.assign(row, defaults, { test_request_item: row.test_request_item });
}

async function save() {
	error.value = "";
	saving.value = true;
	try {
		await apiMethods.reportSave({ ...form });
		showModal.value = false;
		await load();
	} catch (caught) {
		error.value = extractFrappeError(caught, "保存失败");
	} finally {
		saving.value = false;
	}
}
</script>
