<template>
	<div v-if="request.name" class="p-6 max-w-6xl">
		<div class="flex items-start justify-between">
			<div>
				<h1 class="text-xl font-semibold">{{ request.name }}</h1>
				<p class="text-sm text-gray-500">
					{{ request.customer_name || request.customer }} · {{ request.transaction_date }}
				</p>
			</div>
			<StatusBadge :status="request.status" />
		</div>

		<div class="grid grid-cols-4 gap-3 mt-4 mb-4">
			<div class="bg-white border rounded-lg p-3">
				<div class="text-xs text-gray-500">报价单</div>
				<a v-if="request.quotation" :href="quotationUrl" target="_blank" class="text-blue-600">{{ request.quotation }}</a>
				<span v-else class="text-sm text-gray-400">—</span>
			</div>
			<div class="bg-white border rounded-lg p-3">
				<div class="text-xs text-gray-500">销售定单</div>
				<input
					v-if="request.status === '已报价' || request.status === '待检测'"
					v-model="salesOrderInput"
					class="w-full text-sm border rounded px-2 py-1"
					placeholder="填写定单号"
					@change="saveSalesOrder"
				/>
				<a v-else-if="request.sales_order" :href="salesOrderUrl" target="_blank" class="text-blue-600 text-sm">{{ request.sales_order }}</a>
				<span v-else class="text-sm text-gray-400">—</span>
			</div>
			<div class="bg-white border rounded-lg p-3">
				<div class="text-xs text-gray-500">样品数</div>
				<div class="text-lg">{{ samples.length }}</div>
			</div>
			<div class="bg-white border rounded-lg p-3">
				<div class="text-xs text-gray-500">报告数</div>
				<div class="text-lg">{{ request.report_count || 0 }}</div>
			</div>
		</div>

		<div class="flex gap-2 mb-6">
			<button
				v-if="request.status === '草稿' && !request.quotation && items.length"
				class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm"
				@click="runAction('generate_quotation')"
			>
				生成报价
			</button>
			<button
				v-if="request.status === '已报价'"
				class="px-3 py-2 rounded-lg bg-gray-900 text-white text-sm"
				:disabled="!request.sales_order"
				@click="runAction('mark_ready')"
			>
				标记待检测
			</button>
			<button
				v-if="request.status === '待检测'"
				class="px-3 py-2 rounded-lg bg-gray-900 text-white text-sm"
				@click="runAction('start')"
			>
				开始检测
			</button>
			<button
				v-if="request.status === '检测中'"
				class="px-3 py-2 rounded-lg bg-emerald-600 text-white text-sm"
				@click="runAction('complete')"
			>
				完成
			</button>
			<button
				v-if="request.status === '草稿' || request.status === '已报价'"
				class="px-3 py-2 rounded-lg border text-red-600 text-sm"
				@click="runAction('cancel')"
			>
				取消
			</button>
			<button
				v-if="request.name"
				class="px-3 py-2 rounded-lg border text-gray-700 text-sm"
				@click="openReport = true"
			>
				新建报告
			</button>
		</div>

		<section class="bg-white border border-gray-200 rounded-xl p-4 mb-4">
			<div class="flex items-center justify-between mb-3">
				<h2 class="font-medium">样品</h2>
				<button
					v-if="editable"
					class="text-blue-600 text-sm"
					@click="sampleEditor = {}; showSampleDialog = true"
				>
					+ 新建样品
				</button>
			</div>
			<table v-if="samples.length" class="w-full text-sm">
				<thead>
					<tr class="text-left text-gray-500">
						<th class="py-1">名称</th>
						<th>数量</th>
						<th>状态</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="s in samples" :key="s.name" class="border-t">
						<td class="py-2">{{ s.sample_name }}</td>
						<td>{{ s.qty }} {{ s.uom }}</td>
						<td><StatusBadge :status="s.status" /></td>
						<td class="text-right">
							<button v-if="editable" class="text-blue-600 mr-2" @click="editSample(s)">编辑</button>
							<button v-if="editable" class="text-red-600" @click="removeSample(s)">删除</button>
						</td>
					</tr>
				</tbody>
			</table>
			<p v-else class="text-sm text-gray-400">暂无样品</p>
		</section>

		<section class="bg-white border border-gray-200 rounded-xl p-4">
			<div class="flex items-center justify-between mb-3">
				<h2 class="font-medium">测试项</h2>
				<button v-if="editable" class="text-blue-600 text-sm" @click="showItemDialog = true">
					+ 添加测试项
				</button>
			</div>
			<table v-if="items.length" class="w-full text-sm">
				<thead>
					<tr class="text-left text-gray-500">
						<th>样品</th>
						<th>检测项目</th>
						<th>标准</th>
						<th>设备(Asset)</th>
						<th>时长/循环</th>
						<th>数量</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, index) in items" :key="index" class="border-t">
						<td class="py-2">{{ sampleName(row.sample) }}</td>
						<td>{{ row.item }}</td>
						<td>{{ row.standard }}</td>
						<td>{{ row.equipment || "—" }}</td>
						<td>{{ row.hours || "—" }}h / {{ row.cycles || "—" }}</td>
						<td>{{ row.qty }} {{ row.uom }}</td>
						<td class="text-right">
							<button v-if="editable" class="text-red-600" @click="removeItem(index)">移除</button>
						</td>
					</tr>
				</tbody>
			</table>
			<p v-else class="text-sm text-gray-400">暂无测试项</p>
			<button
				v-if="editable && itemDirty"
				class="mt-3 px-3 py-2 rounded-lg bg-gray-900 text-white text-sm"
				@click="saveItems"
			>
				保存测试项
			</button>
		</section>

		<Modal
			v-if="showSampleDialog"
			title="样品"
			@close="showSampleDialog = false"
		>
			<input v-model="sampleEditor.sample_name" placeholder="样品名称" class="w-full border rounded-lg px-3 py-2 mb-2" />
			<input v-model="sampleEditor.qty" type="number" placeholder="数量" class="w-full border rounded-lg px-3 py-2 mb-2" />
			<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="saveSample">
				保存
			</button>
		</Modal>

		<Modal v-if="showItemDialog" title="添加测试项" @close="showItemDialog = false">
			<select v-model="itemDraft.sample" class="w-full border rounded-lg px-3 py-2 mb-2">
				<option v-for="s in samples" :key="s.name" :value="s.name">{{ s.sample_name }}</option>
			</select>
			<input
				v-model="itemDraft.item"
				list="item-options"
				placeholder="检测项目"
				class="w-full border rounded-lg px-3 py-2 mb-2"
				@input="searchItems"
			/>
			<datalist id="item-options">
				<option v-for="o in itemOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
			</datalist>
			<select v-model="itemDraft.standard" class="w-full border rounded-lg px-3 py-2 mb-2">
				<option v-for="s in standards" :key="s.name" :value="s.name">{{ s.standard_code }}</option>
			</select>
			<select v-model="itemDraft.equipment" class="w-full border rounded-lg px-3 py-2 mb-2">
				<option value="">设备(Asset) —</option>
				<option v-for="asset in assets" :key="asset.name" :value="asset.name">
					{{ asset.name }} {{ asset.asset_name }}
				</option>
			</select>
			<div class="mb-2 flex gap-2">
				<input v-model="itemDraft.hours" type="number" placeholder="试验时长(h)" class="w-1/2 border rounded-lg px-3 py-2" />
				<input v-model="itemDraft.cycles" type="number" placeholder="循环次数" class="w-1/2 border rounded-lg px-3 py-2" />
			</div>
			<input v-model="itemDraft.qty" type="number" placeholder="数量" class="w-full border rounded-lg px-3 py-2 mb-2" />
			<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="addItem">添加</button>
		</Modal>

		<Modal v-if="openReport" title="新建报告" @close="openReport = false">
			<p class="text-sm mb-3">将创建关联到 {{ request.name }} 的 Test Report。</p>
			<button
				class="px-3 py-2 rounded-lg bg-gray-900 text-white"
				@click="goToNewReport"
			>
				继续
			</button>
		</Modal>
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import Modal from "../components/Modal.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { apiMethods } from "../api";

const route = useRoute();
const router = useRouter();
const request = ref({});
const samples = ref([]);
const items = ref([]);
const itemDirty = ref(false);
const itemOptions = ref([]);
const standards = ref([]);
const assets = ref([]);
const showSampleDialog = ref(false);
const showItemDialog = ref(false);
const openReport = ref(false);
const sampleEditor = reactive({});
const itemDraft = reactive({
	sample: "",
	item: "",
	standard: "",
	equipment: "",
	hours: null,
	cycles: null,
	qty: 1,
});
const salesOrderInput = ref("");

const editable = computed(() => request.value.status === "草稿");
const quotationUrl = computed(() =>
	request.value.quotation
		? `/app/quotation/${request.value.quotation}`
		: ""
);
const salesOrderUrl = computed(() =>
	request.value.sales_order
		? `/app/sales-order/${request.value.sales_order}`
		: ""
);

onMounted(load);

async function load() {
	const name = route.params.name;
	request.value = await apiMethods.requestGet(name);
	samples.value = request.value.samples || [];
	items.value = request.value.items || [];
	salesOrderInput.value = request.value.sales_order || "";
	standards.value = (await apiMethods.standardsList({})) || [];
	assets.value = (await apiMethods.assetsList("")) || [];
	itemOptions.value = (await apiMethods.itemSearch("")) || [];
}

async function saveSalesOrder() {
	await apiMethods.requestSave({
		name: request.value.name,
		sales_order: salesOrderInput.value,
	});
	await load();
}

async function runAction(action) {
	await apiMethods.requestAction(request.value.name, action);
	await load();
}

function sampleName(name) {
	return samples.value.find((s) => s.name === name)?.sample_name || name;
}

function editSample(sample) {
	Object.assign(sampleEditor, sample);
	showSampleDialog.value = true;
}

async function saveSample() {
	if (sampleEditor.name) {
		await apiMethods.sampleUpdate(sampleEditor);
	} else {
		await apiMethods.sampleCreate({
			...sampleEditor,
			test_request: request.value.name,
			status: "待收样",
			qty: sampleEditor.qty || 1,
		});
	}
	showSampleDialog.value = false;
	Object.keys(sampleEditor).forEach((k) => delete sampleEditor[k]);
	await load();
}

async function removeSample(sample) {
	if (!window.confirm(`删除样品 ${sample.sample_name}?`)) return;
	await apiMethods.sampleDelete(sample.name);
	await load();
}

function addItem() {
	items.value.push({ ...itemDraft });
	Object.assign(itemDraft, {
		sample: "",
		item: "",
		standard: "",
		equipment: "",
		hours: null,
		cycles: null,
		qty: 1,
	});
	itemDirty.value = true;
	showItemDialog.value = false;
}

function removeItem(index) {
	items.value.splice(index, 1);
	itemDirty.value = true;
}

async function saveItems() {
	await apiMethods.requestSave({ name: request.value.name, items: items.value });
	itemDirty.value = false;
	await load();
}

async function searchItems(event) {
	itemOptions.value = (await apiMethods.itemSearch(event.target.value)) || [];
}

function goToNewReport() {
	openReport.value = false;
	sessionStorage.setItem("lims_new_report_request", request.value.name);
	router.push("/lims/reports");
}
</script>
