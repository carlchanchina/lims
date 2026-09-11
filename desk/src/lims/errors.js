// Frappe 把业务报错放在 messages / _server_messages 里,统一取成可读文本。

export function extractFrappeError(caught, fallback = "操作失败") {
	const messages = caught?.messages || caught?._server_messages;
	if (Array.isArray(messages) && messages.length) {
		return messages
			.map((message) => {
				try {
					return JSON.parse(message).message || message;
				} catch {
					return message;
				}
			})
			.join("\n");
	}
	return caught?.message || fallback;
}
