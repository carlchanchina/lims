<template>
	<div class="p-6">
		<div class="mb-4 flex items-center gap-3">
			<input
				v-model="query"
				placeholder="搜索项目编码/名称/分组"
				class="w-72 rounded-lg border border-outline-gray-2 px-3 py-2"
				@input="load"
			/>
			<span class="text-sm text-ink-gray-5">来自 ERPNext Item</span>
			<InlineCreate
				label="+ 新建检测项目"
				title="新建检测项目(写入 ERPNext Item)"
				:fields="fields"
				:save="saveItem"
				@created="load()"
			/>
		</div>

		<div class="overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-base">
			<table class="w-full text-sm">
				<thead class="bg-surface-gray-1 text-start text-ink-gray-6">
					<tr>
						<th class="px-4 py-2 text-start">项目编码</th>
						<th class="px-4 py-2 text-start">项目名称</th>
						<th class="px-4 py-2 text-start">分组</th>
						<th class="px-4 py-2 text-start">单位</th>
						<th class="px-4 py-2 text-start">类型</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-outline-gray-1">
						<td class="px-4 py-2">{{ row.name }}</td>
						<td class="px-4 py-2">{{ row.item_name }}</td>
						<td class="px-4 py-2">{{ row.item_group }}</td>
						<td class="px-4 py-2">{{ row.stock_uom }}</td>
						<td class="px-4 py-2">
							{{ row.is_fixed_asset ? "固定资产" : row.is_stock_item ? "库存物料" : "服务" }}
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="5" class="px-4 py-8 text-center text-ink-gray-4">
							暂无检测项目,可在右上角新建
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
import { itemFields } from "../masterForms";
import { apiMethods } from "../api";

const rows = ref([]);
const query = ref("");
const options = ref({ item_groups: [], uoms: [], defaults: {} });

const fields = computed(() => itemFields(options.value));

onMounted(async () => {
	await load();
	options.value = (await apiMethods.itemFormOptions()) || options.value;
});

async function load() {
	rows.value = (await apiMethods.itemsList(query.value)) || [];
}

async function saveItem(payload) {
	return await apiMethods.itemCreate(payload);
}
</script>
