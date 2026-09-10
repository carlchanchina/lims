import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import frappeUI from "frappe-ui/vite";

function limsBootTemplate() {
	return {
		name: "lims-boot-template",
		transformIndexHtml(html, context) {
			if (context.server) return html;
			return html.replace(
				"</body>",
				`<script>window.__boot = {% if lims_boot %}{{ lims_boot | safe }}{% else %}null{% endif %};</script>\n</body>`
			);
		},
	};
}

export default defineConfig({
	plugins: [
		frappeUI({
			frappeProxy: true,
			lucideIcons: true,
			buildConfig: {
				outDir: "../test/public/lims",
				emptyOutDir: true,
				indexHtmlPath: "../test/www/lims/index.html",
			},
		}),
		vue(),
		limsBootTemplate(),
	],
	server: {
		port: 5173,
	},
});
