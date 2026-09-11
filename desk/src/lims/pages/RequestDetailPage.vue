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
				<template v-else>
					<input
						v-model="quotationQuery"
						list="quotation-options"
						class="w-full text-sm border rounded px-2 py-1"
						placeholder="关联已有报价单"
						@input="searchQuotations"
					/>
					<datalist id="quotation-options">
						<option v-for="q in quotations" :key="q.value" :value="q.value">{{ q.label }}</option>
					</datalist>
					<button
						v-if="quotationQuery"
						class="mt-1 text-xs text-blue-600 hover:underline"
						@click="linkQuotation"
					>
						关联这张报价单
					</button>
				</template>
			</div>
			<div class="bg-white border rounded-lg p-3">
				<div class="text-xs text-gray-500">销售定单</div>
				<a v-if="request.sales_order" :href="salesOrderUrl" target="_blank" class="text-blue-600 text-sm">{{ request.sales_order }}</a>
				<template v-else>
					<input
						v-model="salesOrderQuery"
						list="sales-order-options"
						class="w-full text-sm border rounded px-2 py-1"
						placeholder="关联已有订单"
						@input="searchSalesOrders"
					/>
					<datalist id="sales-order-options">
						<option v-for="o in salesOrders" :key="o.value" :value="o.value">{{ o.label }}</option>
					</datalist>
					<button
						v-if="salesOrderQuery"
						class="mt-1 text-xs text-blue-600 hover:underline"
						@click="linkSalesOrder"
					>
						关联这张订单
					</button>
					<button
						v-else-if="request.quotation"
						class="mt-1 text-xs text-blue-600 hover:underline"
						@click="createSalesOrder"
					>
						从报价单生成订单
					</button>
				</template>
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

		<p
			v-if="error"
			class="mb-4 whitespace-pre-line rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600"
		>
			{{ error }}
		</p>

		<section class="mb-4 rounded-xl border border-gray-200 bg-white p-4">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-medium">委托信息</h2>
				<button v-if="editable" class="text-sm text-blue-600 hover:underline" @click="saveInfo">
					保存
				</button>
			</div>
			<div class="grid grid-cols-3 gap-3 text-sm">
				<div>
					<div class="text-xs text-gray-500">客户参考号</div>
					<input v-if="editable" v-model="info.customer_reference" class="w-full rounded border px-2 py-1" />
					<div v-else>{{ request.customer_reference || "—" }}</div>
				</div>
				<div>
					<div class="text-xs text-gray-500">要求完成日期</div>
					<input v-if="editable" type="date" v-model="info.required_by" class="w-full rounded border px-2 py-1" />
					<div v-else>{{ request.required_by || "—" }}</div>
				</div>
				<div>
					<div class="text-xs text-gray-500">委托方式</div>
					<select v-if="editable" v-model="info.entrustment_mode" class="w-full rounded border px-2 py-1">
						<option v-for="m in entrustmentModes" :key="m" :value="m">{{ m }}</option>
					</select>
					<div v-else>{{ request.entrustment_mode || "—" }}</div>
				</div>
				<div>
					<div class="text-xs text-gray-500">试验后样品处置</div>
					<select v-if="editable" v-model="info.sample_disposal" class="w-full rounded border px-2 py-1">
						<option v-for="d in disposalOptions" :key="d" :value="d">{{ d }}</option>
					</select>
					<div v-else>{{ request.sample_disposal || "—" }}</div>
				</div>
				<div class="col-span-2">
					<div class="text-xs text-gray-500">委托备注</div>
					<textarea v-if="editable" v-model="info.remarks" rows="2" class="w-full rounded border px-2 py-1"></textarea>
					<div v-else class="whitespace-pre-line">{{ request.remarks || "—" }}</div>
				</div>
			</div>
			<div class="mt-3 text-xs text-gray-500">
				报价:{{ request.quotation_status || "—" }} · 订单:{{ request.sales_order_status || "—" }} · 报告:{{ request.report_status || "未出报告" }}
			</div>
		</section>

		<section v-if="request.quotations?.length" class="mb-4 rounded-xl border border-gray-200 bg-white p-4">
			<h2 class="mb-2 font-medium">报价历史</h2>
			<table class="w-full text-sm">
				<thead class="text-left text-gray-500">
					<tr>
						<th class="py-1">报价单</th>
						<th>日期</th>
						<th>金额</th>
						<th>状态</th>
						<th>当前</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in request.quotations" :key="row.name" class="border-t">
						<td class="py-1">
							<a class="text-blue-600" :href="`/app/quotation/${row.quotation}`" target="_blank">
								{{ row.quotation }}
							</a>
						</td>
						<td>{{ row.quotation_date || "—" }}</td>
						<td>{{ row.grand_total || "—" }}</td>
						<td>{{ row.status || "—" }}</td>
						<td>{{ row.is_current ? "✔" : "" }}</td>
					</tr>
				</tbody>
			</table>
		</section>

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
			<div class="mb-2 flex gap-2">
				<input v-model="sampleEditor.client_sample_code" placeholder="客户样品编号" class="w-1/2 border rounded-lg px-3 py-2" />
				<input v-model="sampleEditor.batch_no" placeholder="批号/序列号" class="w-1/2 border rounded-lg px-3 py-2" />
			</div>
			<div class="mb-2 flex gap-2">
				<input v-model="sampleEditor.specification" placeholder="规格/型号" class="w-1/2 border rounded-lg px-3 py-2" />
				<input v-model="sampleEditor.qty" type="number" placeholder="数量" class="w-1/4 border rounded-lg px-3 py-2" />
				<input v-model="sampleEditor.uom" placeholder="单位" class="w-1/4 border rounded-lg px-3 py-2" />
			</div>
			<textarea v-model="sampleEditor.appearance" placeholder="外观描述" rows="2" class="mb-2 w-full border rounded-lg px-3 py-2"></textarea>
			<div class="mb-2 flex gap-2">
				<input v-model="sampleEditor.received_date" type="date" class="w-1/3 border rounded-lg px-3 py-2" />
				<input v-model="sampleEditor.received_by" list="user-options" placeholder="收样人" class="w-1/3 border rounded-lg px-3 py-2" />
				<input v-model="sampleEditor.retention_until" type="date" class="w-1/3 border rounded-lg px-3 py-2" />
			</div>
			<div class="mb-2 flex gap-2">
				<select v-model="sampleEditor.status" class="w-1/2 border rounded-lg px-3 py-2">
					<option v-for="s in sampleStatuses" :key="s" :value="s">{{ s }}</option>
				</select>
				<select v-model="sampleEditor.disposal" class="w-1/2 border rounded-lg px-3 py-2">
					<option v-for="d in disposalOptions" :key="d" :value="d">{{ d }}</option>
				</select>
			</div>
			<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="saveSample">
				保存
			</button>
		</Modal>

		<section class="mt-4 rounded-xl border border-gray-200 bg-white p-4">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-medium">设备使用记录</h2>
				<button v-if="editable" class="text-sm text-blue-600 hover:underline" @click="usageDraft = { test_request: request.name }; showUsageDialog = true">
					+ 登记使用
				</button>
			</div>
			<table v-if="usages.length" class="w-full text-sm">
				<thead class="text-left text-gray-500">
					<tr>
						<th class="py-1">设备</th>
						<th>使用人</th>
						<th>开始</th>
						<th>结束</th>
						<th>备注</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in usages" :key="row.name" class="border-t">
						<td class="py-1">{{ row.asset }}</td>
						<td>{{ row.used_by || "—" }}</td>
						<td>{{ row.from_datetime }}</td>
						<td>{{ row.to_datetime || "—" }}</td>
						<td>{{ row.remarks || "—" }}</td>
					</tr>
				</tbody>
			</table>
			<p v-else class="text-sm text-gray-400">暂无设备使用记录</p>
		</section>

		<section class="mt-4 rounded-xl border border-gray-200 bg-white p-4">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-medium">异常 / 不符合</h2>
				<button v-if="editable" class="text-sm text-blue-600 hover:underline" @click="ncDraft = { test_request: request.name, source: '检测过程', severity: '一般' }; showNcDialog = true">
					+ 登记异常
				</button>
			</div>
			<table v-if="nonconformances.length" class="w-full text-sm">
				<thead class="text-left text-gray-500">
					<tr>
						<th class="py-1">编号</th>
						<th>来源</th>
						<th>严重程度</th>
						<th>问题</th>
						<th>处理措施</th>
						<th>状态</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in nonconformances" :key="row.name" class="border-t">
						<td class="py-1">{{ row.name }}</td>
						<td>{{ row.source }}</td>
						<td>{{ row.severity }}</td>
						<td class="max-w-xs truncate">{{ row.description }}</td>
						<td class="max-w-xs truncate">{{ row.action || "—" }}</td>
						<td>{{ row.status }}</td>
						<td class="text-right">
							<button v-if="row.status !== '已关闭'" class="text-blue-600 hover:underline" @click="closeNonconformance(row)">
								关闭
							</button>
						</td>
					</tr>
				</tbody>
			</table>
			<p v-else class="text-sm text-gray-400">暂无异常记录</p>
		</section>

		<Modal v-if="showUsageDialog" title="登记设备使用" @close="showUsageDialog = false">
			<select v-model="usageDraft.asset" class="mb-2 w-full border rounded-lg px-3 py-2">
				<option value="">选择设备</option>
				<option v-for="asset in assets" :key="asset.name" :value="asset.name">
					{{ asset.name }} {{ asset.asset_name }}
				</option>
			</select>
			<input v-model="usageDraft.used_by" list="user-options" placeholder="使用人" class="mb-2 w-full border rounded-lg px-3 py-2" />
			<input v-model="usageDraft.from_datetime" type="datetime-local" class="mb-2 w-full border rounded-lg px-3 py-2" />
			<input v-model="usageDraft.to_datetime" type="datetime-local" class="mb-2 w-full border rounded-lg px-3 py-2" />
			<textarea v-model="usageDraft.remarks" placeholder="备注" rows="2" class="mb-2 w-full border rounded-lg px-3 py-2"></textarea>
			<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="saveUsage">保存</button>
		</Modal>

		<Modal v-if="showNcDialog" title="登记异常" @close="showNcDialog = false">
			<div class="mb-2 flex gap-2">
				<select v-model="ncDraft.source" class="w-1/2 border rounded-lg px-3 py-2">
					<option v-for="s in ncSources" :key="s" :value="s">{{ s }}</option>
				</select>
				<select v-model="ncDraft.severity" class="w-1/2 border rounded-lg px-3 py-2">
					<option v-for="s in ncSeverities" :key="s" :value="s">{{ s }}</option>
				</select>
			</div>
			<textarea v-model="ncDraft.description" placeholder="问题描述" rows="3" class="mb-2 w-full border rounded-lg px-3 py-2"></textarea>
			<textarea v-model="ncDraft.action" placeholder="处理措施" rows="3" class="mb-2 w-full border rounded-lg px-3 py-2"></textarea>
			<input v-model="ncDraft.owner_user" list="user-options" placeholder="责任人" class="mb-2 w-full border rounded-lg px-3 py-2" />
			<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="saveNonconformance">保存</button>
		</Modal>

		<datalist id="user-options">
			<option v-for="u in users" :key="u.value" :value="u.value">{{ u.label }}</option>
		</datalist>

		<Modal v-if="showItemDialog" title="添加测试项" @close="showItemDialog = false">
			<select v-model="itemDraft.sample" class="w-full border rounded-lg px-3 py-2 mb-2">
				<option v-for="s in samples" :key="s.name" :value="s.name">{{ s.sample_name }}</option>
			</select>
			<div class="mb-2">
				<div class="flex items-center justify-between">
					<span class="text-sm text-gray-600">检测项目</span>
					<InlineCreate
						label="+ 新建检测项目"
						title="新建检测项目(写入 ERPNext Item)"
						:fields="itemFormFields"
						:save="saveItem"
						@created="onItemCreated"
					/>
				</div>
				<input
					v-model="itemDraft.item"
					list="item-options"
					placeholder="检测项目"
					class="w-full border rounded-lg px-3 py-2"
					@input="searchItems"
				/>
				<datalist id="item-options">
					<option v-for="o in itemOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
				</datalist>
			</div>
			<select v-model="itemDraft.standard" class="w-full border rounded-lg px-3 py-2 mb-2">
				<option v-for="s in standards" :key="s.name" :value="s.name">{{ s.standard_code }}</option>
			</select>
			<div class="mb-2">
				<div class="flex items-center justify-between">
					<span class="text-sm text-gray-600">设备(Asset)</span>
					<InlineCreate
						label="+ 新建设备"
						title="新建设备(写入 ERPNext Asset)"
						:fields="assetFields"
						:save="saveAsset"
						@created="onAssetCreated"
					/>
				</div>
				<select v-model="itemDraft.equipment" class="w-full border rounded-lg px-3 py-2">
					<option value="">设备(Asset) —</option>
					<option v-for="asset in assets" :key="asset.name" :value="asset.name">
						{{ asset.name }} {{ asset.asset_name }}
					</option>
				</select>
			</div>
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
import InlineCreate from "../components/InlineCreate.vue";
import Modal from "../components/Modal.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { extractFrappeError } from "../errors";
import { assetFields as buildAssetFields, itemFields } from "../masterForms";
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
const assetOptions = ref({ items: [], locations: [], custodians: [], companies: [], defaults: {} });
const itemFormOptions = ref({ item_groups: [], uoms: [], defaults: {} });
const quotations = ref([]);
const salesOrders = ref([]);
const quotationQuery = ref("");
const salesOrderQuery = ref("");
const usages = ref([]);
const nonconformances = ref([]);
const users = ref([]);
const showUsageDialog = ref(false);
const showNcDialog = ref(false);
const usageDraft = reactive({});
const ncDraft = reactive({});
const info = reactive({});
const entrustmentModes = ["送检", "现场", "抽样", "其他"];
const disposalOptions = ["待定", "退还", "留样", "销毁"];
const sampleStatuses = ["待收样", "已收样", "检测中", "已检测", "已退样"];
const ncSources = ["检测过程", "报告审核", "客户反馈", "设备异常", "其他"];
const ncSeverities = ["轻微", "一般", "严重"];
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
const error = ref("");

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

onMounted(async () => {
	await load();
	const [assetOpts, itemOpts, userList] = await Promise.all([
		apiMethods.assetFormOptions(),
		apiMethods.itemFormOptions(),
		apiMethods.userOptions(""),
	]);
	assetOptions.value = assetOpts || assetOptions.value;
	itemFormOptions.value = itemOpts || itemFormOptions.value;
	users.value = userList || [];
});

async function load() {
	const name = route.params.name;
	request.value = await apiMethods.requestGet(name);
	samples.value = request.value.samples || [];
	items.value = request.value.items || [];
	standards.value = (await apiMethods.standardsList({})) || [];
	assets.value = (await apiMethods.assetsList("")) || [];
	itemOptions.value = (await apiMethods.itemSearch("")) || [];
	usages.value = (await apiMethods.usageList(name)) || [];
	nonconformances.value = (await apiMethods.nonconformanceList(name)) || [];
	for (const key of [
		"customer_reference",
		"required_by",
		"entrustment_mode",
		"sample_disposal",
		"remarks",
	]) {
		info[key] = request.value[key] || "";
	}
}

async function saveInfo() {
	await withError(() =>
		apiMethods.requestSave({ name: request.value.name, ...info })
	);
}

function toFrappeDatetime(value) {
	if (!value) return null;
	return value.replace("T", " ") + (value.length === 16 ? ":00" : "");
}

async function saveUsage() {
	await withError(() =>
		apiMethods.usageCreate({
			...usageDraft,
			from_datetime: toFrappeDatetime(usageDraft.from_datetime),
			to_datetime: toFrappeDatetime(usageDraft.to_datetime),
		})
	);
	showUsageDialog.value = false;
}

async function saveNonconformance() {
	await withError(() => apiMethods.nonconformanceSave({ ...ncDraft }));
	showNcDialog.value = false;
}

async function closeNonconformance(row) {
	await withError(() =>
		apiMethods.nonconformanceSave({ name: row.name, status: "已关闭" })
	);
}

const assetFields = computed(() => buildAssetFields(assetOptions.value));

const itemFormFields = computed(() => itemFields(itemFormOptions.value));

async function saveAsset(payload) {
	return await apiMethods.assetCreate(payload);
}

async function onAssetCreated(option) {
	assets.value = [...assets.value, { name: option.value, asset_name: option.label }];
	itemDraft.equipment = option.value;
}

async function saveItem(payload) {
	return await apiMethods.itemCreate(payload);
}

async function onItemCreated(option) {
	itemOptions.value = [...itemOptions.value, option];
	itemDraft.item = option.value;
}

async function searchQuotations(event) {
	quotations.value = (await apiMethods.quotationSearch(event.target.value)) || [];
}

async function searchSalesOrders(event) {
	salesOrders.value = (await apiMethods.salesOrderSearch(event.target.value)) || [];
}

async function withError(action) {
	error.value = "";
	try {
		await action();
		await load();
	} catch (caught) {
		error.value = extractFrappeError(caught);
	}
}

async function linkQuotation() {
	await withError(() =>
		apiMethods.quotationLink(request.value.name, quotationQuery.value)
	);
	quotationQuery.value = "";
}

async function linkSalesOrder() {
	await withError(() =>
		apiMethods.salesOrderLink(request.value.name, salesOrderQuery.value)
	);
	salesOrderQuery.value = "";
}

async function createSalesOrder() {
	await withError(() => apiMethods.salesOrderCreate(request.value.name));
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
