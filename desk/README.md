# 环境试验 LIMS 前端(helpdesk 同款结构)

本目录是 frappe/helpdesk 前端(`desk/`)的整体拷贝,保留其 Vue3 + Vite + frappe-ui + Tailwind
设计系统、组件库与布局方式;业务入口改为 LIMS:

- 应用入口:`src/main.js`
- LIMS 应用壳与页面:`src/lims/`(布局、路由、API、页面)
- LIMS 后端接口:`test/api/*.py`
- 构建输出:`../test/public/lims`
- 页面模板:`../test/www/lims/index.html`
- 访问地址:`/lims`

## 构建

```bash
cd desk
yarn install
yarn build
```

构建后:

```bash
bench --site <site> migrate
bench --site <site> clear-cache
```

Desk 的 Apps 面板会出现「环境试验 LIMS」入口;也可直接访问 `https://<site>/lims`。

> 说明:helpdesk 原本的 `src/pages`、`src/stores`、`src/components` 等文件全部保留,便于后续
> 继续复用其样式与组件;当前构建入口只引用 `src/lims/` 下的 LIMS 页面。
