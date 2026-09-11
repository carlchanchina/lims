<template>
	<div class="p-6">
		<div class="mb-4 flex items-center gap-3">
			<input
				v-model="query"
				placeholder="搜索设备编号/名称/位置"
				class="w-72 rounded-lg border border-outline-gray-2 px-3 py-2"
				@input="load"
			/>
			<span class="text-sm text-ink-gray-5">来自 ERPNext Asset</span>
			<InlineCreate
				label="+ 新建设备"
				title="新建设备(写入 ERPNext Asset)"
				:fields="assetFields"
				:save="saveAsset"
				@created="load()"
			/>
		</div>
		<div class="overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-base">
			<table class="w-full text-sm">
				<thead class="bg-surface-gray-1 text-start text-ink-gray-6">
					<tr>
						<th class="px-4 py-2 text-start">设备编号</th>
						<th class="px-4 py-2 text-start">名称</th>
						<th class="px-4 py-2 text-start">资产类别</th>
						<th class="px-4 py-2 text-start">位置</th>
						<th class="px-4 py-2 text-start">保管人</th>
						<th class="px-4 py-2 text-start">状态</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-outline-gray-1">
						<td class="px-4 py-2">{{ row.name }}</td>
						<td class="px-4 py-2">{{ row.asset_name || row.item_code }}</td>
						<td class="px-4 py-2">{{ row.asset_category }}</td>
						<td class="px-4 py-2">{{ row.location }}</td>
						<td class="px-4 py-2">{{ row.custodian }}</td>
						<td class="px-4 py-2">{{ row.status }}</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="6" class="px-4 py-8 text-center text-ink-gray-4">
							暂无设备,请先在 ERPNext 建立 Asset
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import InlineCreate from "../components/InlineCreate.vue";
import { assetFields as buildAssetFields } from "../masterForms";
import { apiMethods } from "../api";

const rows = ref([]);
const query = ref("");
const options = ref({ items: [], locations: [], custodians: [], companies: [], defaults: {} });

onMounted(load);
onMounted(async () => {
	options.value = (await apiMethods.assetFormOptions()) || options.value;
});

const assetFields = computed(() => buildAssetFields(options.value));

async function saveAsset(payload) {
	return await apiMethods.assetCreate(payload);
}

async function load() {
	rows.value = (await apiMethods.assetsList(query.value)) || [];
}
</script>
