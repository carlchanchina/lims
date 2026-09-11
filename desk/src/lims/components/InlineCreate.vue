<template>
	<div class="inline-flex">
		<button
			type="button"
			class="whitespace-nowrap text-sm text-blue-600 hover:underline"
			@click="open"
		>
			{{ label }}
		</button>

		<Modal v-if="visible" :title="title" @close="close">
			<div class="space-y-3">
				<div v-for="field in fields" :key="field.fieldname">
					<label class="mb-1 block text-sm text-gray-700">
						{{ field.label }}
						<span v-if="field.required" class="text-red-500">*</span>
					</label>

					<select
						v-if="field.type === 'select'"
						v-model="draft[field.fieldname]"
						class="w-full rounded-lg border border-gray-300 px-3 py-2"
					>
						<option value="">{{ field.placeholder || "请选择" }}</option>
						<option
							v-for="option in field.options || []"
							:key="valueOf(option)"
							:value="valueOf(option)"
						>
							{{ labelOf(option) }}
						</option>
					</select>

					<textarea
						v-else-if="field.type === 'textarea'"
						v-model="draft[field.fieldname]"
						:placeholder="field.placeholder"
						class="w-full rounded-lg border border-gray-300 px-3 py-2"
					></textarea>

					<input
						v-else
						v-model="draft[field.fieldname]"
						:type="inputType(field)"
						:placeholder="field.placeholder"
						class="w-full rounded-lg border border-gray-300 px-3 py-2"
					/>
					<p v-if="field.hint" class="mt-1 text-xs text-gray-500">{{ field.hint }}</p>
					<p v-if="noOptions(field)" class="mt-1 text-xs text-amber-600">
						暂时没有可选项,请先在 ERPNext 里建立 {{ field.label }} 对应的主数据。
					</p>
				</div>

				<p v-if="error" class="whitespace-pre-line text-sm text-red-600">{{ error }}</p>

				<div class="flex justify-end gap-2 pt-1">
					<button class="rounded-lg border px-3 py-2" @click="close">取消</button>
					<button
						class="rounded-lg bg-gray-900 px-3 py-2 text-white disabled:opacity-50"
						:disabled="saving"
						@click="submit"
					>
						{{ saving ? "保存中…" : "保存" }}
					</button>
				</div>
			</div>
		</Modal>
	</div>
</template>

<script setup>
import { reactive, ref } from "vue";
import Modal from "./Modal.vue";
import { extractFrappeError } from "../errors";

const props = defineProps({
	label: { type: String, default: "+ 新建" },
	title: { type: String, default: "新建" },
	fields: { type: Array, default: () => [] },
	prefill: { type: Object, default: () => ({}) },
	save: { type: Function, required: true },
});

const emit = defineEmits(["created"]);

const visible = ref(false);
const saving = ref(false);
const error = ref("");
const draft = reactive({});

function open() {
	error.value = "";
	Object.keys(draft).forEach((key) => delete draft[key]);
	for (const field of props.fields) {
		draft[field.fieldname] =
			props.prefill[field.fieldname] ?? field.default ?? "";
	}
	visible.value = true;
}

function close() {
	visible.value = false;
}

function inputType(field) {
	if (field.type === "number") return "number";
	if (field.type === "date") return "date";
	return "text";
}

function noOptions(field) {
	return field.required && field.type === "select" && !(field.options || []).length;
}

function valueOf(option) {
	return typeof option === "object" && option !== null ? option.value : option;
}

function labelOf(option) {
	if (typeof option === "object" && option !== null) {
		return option.label ?? option.value;
	}
	return option;
}

async function submit() {
	error.value = "";
	saving.value = true;
	try {
		const payload = { ...draft };
		for (const field of props.fields) {
			if (field.type === "number" && payload[field.fieldname] !== "") {
				payload[field.fieldname] = Number(payload[field.fieldname]);
			}
		}
		const created = await props.save(payload);
		visible.value = false;
		if (created) emit("created", created);
	} catch (caught) {
		error.value = extractFrappeError(caught, "保存失败");
	} finally {
		saving.value = false;
	}
}
</script>
