import { FrappeUI, setConfig, frappeRequest } from "frappe-ui";
import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import "./index.css";
import { router } from "./router";
import { initBoot } from "./boot";

setConfig("resourceFetcher", frappeRequest);

initBoot().then(() => {
	const app = createApp(App);
	app.use(FrappeUI);
	app.use(createPinia());
	app.use(router);
	app.mount("#app");
});
