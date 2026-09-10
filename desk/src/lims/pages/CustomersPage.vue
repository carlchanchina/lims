<template>
	<div class="p-6">
		<div class="mb-4 flex items-center gap-3">
			<input
				v-model="query"
				placeholder="搜索客户编号/名称"
				class="w-72 rounded-lg border border-outline-gray-2 px-3 py-2"
				@input="load"
			/>
			<span class="text-sm text-ink-gray-5">由 ERPNext Customer / Contact 自动同步</span>
		</div>
		<div class="overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-base">
			<table class="w-full text-sm">
				<thead class="bg-surface-gray-1">
					<tr>
						<th class="px-4 py-2 text-start">客户编号</th>
						<th class="px-4 py-2 text-start">客户名称</th>
						<th class="px-4 py-2 text-start">状态</th>
						<th class="px-4 py-2 text-start">默认价目表</th>
						<th class="px-4 py-2"></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.name" class="border-t border-outline-gray-1">
						<td class="px-4 py-2">{{ row.customer }}</td>
						<td class="px-4 py-2">{{ row.customer_name }}</td>
						<td class="px-4 py-2">
							<StatusBadge :status="row.status" />
						</td>
						<td class="px-4 py-2">{{ row.default_price_list }}</td>
						<td class="px-4 py-2 text-end">
							<Button variant="ghost" @click="openCustomer(row)">联系人</Button>
						</td>
					</tr>
					<tr v-if="!rows.length">
						<td colspan="5" class="px-4 py-8 text-center text-ink-gray-4">暂无客户</td>
					</tr>
				</tbody>
			</table>
		</div>

		<Modal v-if="active" :title="active.customer_name || active.customer" @close="active = null">
			<div v-if="contacts.length" class="divide-y divide-outline-gray-1">
				<div v-for="contact in contacts" :key="contact.name" class="py-3">
					<div class="font-medium text-ink-gray-9">{{ contact.full_name }}</div>
					<div class="text-sm text-ink-gray-6">
						{{ contact.designation }} · {{ contact.email_id }} · {{ contact.mobile_no }}
					</div>
				</div>
			</div>
			<p v-else class="py-4 text-center text-ink-gray-5">暂无联系人</p>
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
const query = ref("");
const active = ref(null);
const contacts = ref([]);

onMounted(load);

async function load() {
	rows.value = (await apiMethods.customersList(query.value)) || [];
}

async function openCustomer(row) {
	active.value = row;
	contacts.value = (await apiMethods.contactsList(row.name)) || [];
}
</script>
