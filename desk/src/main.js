import { createApp, h } from "vue";
import {
	Badge,
	Button,
	Dialog,
	ErrorMessage,
	FeatherIcon,
	FormControl,
	frappeRequest,
	FrappeUI,
	setConfig,
	TextInput,
	toast,
	Tooltip,
} from "frappe-ui";
import { spritePlugin } from "frappe-ui/icons";
import { createPinia } from "pinia";
import CircleAlert from "~icons/lucide/circle-alert";
import App from "./lims/App.vue";
import { initBoot } from "./lims/boot";
import { router } from "./lims/router";
import "./index.css";

const globalComponents = {
	Badge,
	Button,
	Dialog,
	ErrorMessage,
	FeatherIcon,
	FormControl,
	Tooltip,
	TextInput,
};

setConfig("resourceFetcher", frappeRequest);
setConfig("fallbackErrorHandler", (error) => {
	const msg = error.exc_type
		? (error.messages || error.message || []).join(", ")
		: error.message;
	toast.create({
		message: msg,
		icon: h(CircleAlert, { class: "text-ink-red-4" }),
	});
});

initBoot().then(() => {
	const app = createApp(App);
	app.use(FrappeUI);
	app.use(spritePlugin);
	app.use(createPinia());
	app.use(router);
	app.config.globalProperties.__ = (text) => text;
	for (const name in globalComponents) {
		app.component(name, globalComponents[name]);
	}
	app.mount("#app");
});
