<template>
	<div class="p-6 max-w-6xl">
		<div class="flex items-center justify-between mb-4">
			<h1 class="text-xl font-semibold text-gray-900">{{ title }}</h1>
			<button
				class="px-3 py-2 rounded-lg bg-gray-900 text-white text-sm"
				@click="openNew()"
			>
				新建 {{ singular }}
			</button>
		</div>

		<div class="bg-white border border-gray-200 rounded-xl overflow-hidden">
			<table class="w-full text-sm">
				<thead class="bg-gray-50 text-left text-gray-600">
					<tr>
						<th v-for="col in columns" :key="col" class="px-4 py-2 font-medium">
							{{ labelOf(col) }}
						</th>
						<th class="px-4 py-2"></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-gray-100">
						<td v-for="col in columns" :key="col" class="px-4 py-2">
							<span v-if="col === 'enabled'" class="text-gray-600">{{
								row.enabled ? "启用" : "停用"
							}}</span>
							<StatusBadge v-else-if="col === 'status'" :status="row.status" />
							<span v-else>{{ row[col] }}</span>
						</td>
						<td class="px-4 py-2 text-right">
							<button class="text-blue-600 hover:underline mr-3" @click="openEdit(row)">
								编辑
							</button>
							<button
								v-if="actionLabel && action"
								class="text-gray-600 hover:underline mr-3"
								@click="runAction(row)"
							>
								{{ actionLabel }}
							</button>
							<button v-if="canDelete" class="text-red-600 hover:underline" @click="remove(row)">
								删除
							</button>
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td :colspan="columns.length + 1" class="px-4 py-8 text-center text-gray-400">
							暂无数据
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div
			v-if="editing"
			class="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50"
			@click.self="editing = null"
		>
			<div class="bg-white rounded-xl w-full max-w-lg p-5">
				<h2 class="text-lg font-semibold mb-4">{{ editing.name ? "编辑" : "新建" }} {{ singular }}</h2>
				<div class="space-y-3">
					<div v-for="field in fields" :key="field.fieldname">
						<label class="block text-sm text-gray-700 mb-1">{{ field.label }}</label>
						<input
							v-if="field.type === 'datalist'"
							:list="'dl-' + field.fieldname"
							v-model="editing[field.fieldname]"
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
						/>
						<input
							v-if="
								field.type !== 'datalist' &&
								field.type !== 'select' &&
								field.type !== 'textarea' &&
								field.type !== 'checkbox'
							"
							v-model="editing[field.fieldname]"
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
						/>
						<datalist v-if="field.type === 'datalist'" :id="'dl-' + field.fieldname">
							<option
								v-for="option in field.options"
								:key="option.value"
								:value="option.value"
							>
								{{ option.label }}
							</option>
						</datalist>
						<select
							v-else-if="field.type === 'select'"
							v-model="editing[field.fieldname]"
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
						>
							<option
								v-for="option in field.options"
								:key="optionObject(option) ? option.value : option"
								:value="optionObject(option) ? option.value : option"
							>
								{{ optionObject(option) ? option.label : option }}
							</option>
						</select>
						<textarea
							v-else-if="field.type === 'textarea'"
							v-model="editing[field.fieldname]"
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
						></textarea>
						<label v-else class="flex items-center gap-2 text-sm">
							<input type="checkbox" v-model="editing[field.fieldname]" />
							{{ field.help || "启用" }}
						</label>
					</div>
				</div>
				<div class="flex justify-end gap-2 mt-5">
					<button class="px-3 py-2 rounded-lg border" @click="editing = null">取消</button>
					<button class="px-3 py-2 rounded-lg bg-gray-900 text-white" @click="save()">
						保存
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import StatusBadge from "./StatusBadge.vue";

const props = defineProps({
	title: String,
	singular: String,
	columns: { type: Array, default: () => [] },
	fields: { type: Array, default: () => [] },
	canDelete: { type: Boolean, default: true },
	load: { type: Function, required: true },
	save: { type: Function, required: true },
	remove: { type: Function, required: true },
	newRow: { type: Function, required: true },
	actionLabel: { type: String, default: "" },
	action: { type: Function, default: null },
});

const rows = ref([]);
const editing = ref(null);

onMounted(refresh);

async function refresh() {
	rows.value = (await props.load()) || [];
}

function openNew() {
	editing.value = props.newRow();
}

function openEdit(row) {
	editing.value = { ...row };
}

function labelOf(fieldname) {
	const field = props.fields.find((f) => f.fieldname === fieldname);
	return field ? field.label : fieldname;
}

function optionObject(option) {
	return typeof option === "object" && option !== null;
}

async function save() {
	await props.save(editing.value);
	editing.value = null;
	await refresh();
}

async function remove(row) {
	if (!window.confirm(`确定删除 ${row.name}?`)) return;
	await props.remove(row.name);
	await refresh();
}

async function runAction(row) {
	if (!props.action) return;
	await props.action(row.name);
	await refresh();
}
</script>
