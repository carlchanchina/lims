<template>
	<div class="p-6">
		<div class="mb-4 flex items-center justify-end gap-2">
			<Button theme="gray" @click="generateFromRequest">从检测请求生成计划</Button>
		</div>
		<div class="overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-base">
			<table class="w-full text-sm">
				<thead class="bg-surface-gray-1">
					<tr>
						<th class="px-4 py-2 text-start">计划编号</th>
						<th class="px-4 py-2 text-start">检测请求</th>
						<th class="px-4 py-2 text-start">项目</th>
						<th class="px-4 py-2 text-start">计划时间</th>
						<th class="px-4 py-2 text-start">状态</th>
						<th class="px-4 py-2"></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-outline-gray-1">
						<td class="px-4 py-2">{{ row.name }}</td>
						<td class="px-4 py-2">{{ row.test_request }}</td>
						<td class="px-4 py-2">{{ row.project }}</td>
						<td class="px-4 py-2">{{ row.start_date }} ~ {{ row.end_date }}</td>
						<td class="px-4 py-2"><StatusBadge :status="row.status" /></td>
						<td class="px-4 py-2 text-end">
							<Button variant="ghost" @click="editPlan(row)">编辑</Button>
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="6" class="px-4 py-8 text-center text-ink-gray-4">暂无试验计划</td>
					</tr>
				</tbody>
			</table>
		</div>

		<Modal v-if="generate" title="从检测请求生成计划" @close="generate = false">
			<select v-model="selectedRequest" class="w-full rounded-lg border px-3 py-2">
				<option v-for="r in requests" :key="r.name" :value="r.name">{{ r.name }}</option>
			</select>
			<div class="mt-4 flex justify-end">
				<Button theme="gray" @click="doGenerate">生成</Button>
			</div>
		</Modal>

		<Modal v-if="plan" :title="plan.name" @close="plan = null">
			<div class="space-y-2">
				<select v-model="plan.status" class="w-full rounded-lg border px-3 py-2">
					<option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
				</select>
				<input type="date" v-model="plan.start_date" class="w-full rounded-lg border px-3 py-2" />
				<input type="date" v-model="plan.end_date" class="w-full rounded-lg border px-3 py-2" />
				<table class="w-full text-sm">
					<thead>
						<tr>
							<th class="text-start">任务</th>
							<th class="text-start">设备(Asset)</th>
							<th class="text-start">开始</th>
							<th class="text-start">结束</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(task, index) in plan.tasks" :key="index">
							<td><input v-model="task.task_name" class="w-full rounded border px-2 py-1" /></td>
							<td>
								<select v-model="task.equipment" class="w-full rounded border px-2 py-1">
									<option value="">—</option>
									<option v-for="asset in assets" :key="asset.name" :value="asset.name">
										{{ asset.name }} {{ asset.asset_name }}
									</option>
								</select>
							</td>
							<td><input type="datetime-local" v-model="task.start_datetime" class="rounded border px-2 py-1" /></td>
							<td><input type="datetime-local" v-model="task.end_datetime" class="rounded border px-2 py-1" /></td>
						</tr>
					</tbody>
				</table>
			</div>
			<div class="mt-4 flex justify-end">
				<Button theme="gray" @click="savePlan">保存</Button>
			</div>
		</Modal>
	</div>
</template>

<script setup>
import { Button } from "frappe-ui";
import { onMounted, ref } from "vue";
import Modal from "../components/Modal.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { apiMethods } from "../api";

const rows = ref([]);
const requests = ref([]);
const assets = ref([]);
const generate = ref(false);
const selectedRequest = ref("");
const plan = ref(null);
const statuses = ["草稿", "待执行", "执行中", "已完成", "已取消"];

onMounted(async () => {
	await load();
	requests.value = (await apiMethods.requestsList({})) || [];
	assets.value = (await apiMethods.assetsList("")) || [];
});

async function load() {
	rows.value = (await apiMethods.plansList()) || [];
}

function generateFromRequest() {
	selectedRequest.value = requests.value[0]?.name || "";
	generate.value = true;
}

async function doGenerate() {
	if (!selectedRequest.value) return;
	await apiMethods.planGenerate(selectedRequest.value);
	generate.value = false;
	await load();
}

async function editPlan(row) {
	plan.value = await apiMethods.planGet(row.name);
	plan.value.tasks = plan.value.tasks || [];
}

async function savePlan() {
	await apiMethods.planSave(plan.value);
	plan.value = null;
	await load();
}
</script>
