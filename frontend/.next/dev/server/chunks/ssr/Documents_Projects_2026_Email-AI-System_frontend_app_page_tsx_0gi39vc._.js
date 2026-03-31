module.exports = [
"[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>HomePage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/navigation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
"use client";
;
;
;
function HomePage() {
    const router = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRouter"])();
    const [chatId, setChatId] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("");
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        try {
            const saved = localStorage.getItem("telegram_chat_id");
            if (saved) setChatId(saved);
        } catch  {
        // ignore
        }
    }, []);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
        style: {
            padding: 24,
            fontFamily: "system-ui, sans-serif"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                style: {
                    marginBottom: 12
                },
                children: "NextRole AI Dashboard"
            }, void 0, false, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                lineNumber: 21,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                style: {
                    marginBottom: 18
                },
                children: [
                    "Set your Telegram ",
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("code", {
                        children: "chat_id"
                    }, void 0, false, {
                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                        lineNumber: 23,
                        columnNumber: 27
                    }, this),
                    " so the dashboard can fetch your data."
                ]
            }, void 0, true, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                lineNumber: 22,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                style: {
                    display: "block",
                    marginBottom: 8
                },
                children: [
                    "Telegram chat_id",
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                        value: chatId,
                        onChange: (e)=>setChatId(e.target.value),
                        style: {
                            display: "block",
                            width: "100%",
                            maxWidth: 520,
                            padding: 10,
                            marginTop: 8
                        },
                        placeholder: "e.g. 123456789"
                    }, void 0, false, {
                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                        lineNumber: 28,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                lineNumber: 26,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    marginTop: 12
                },
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: ()=>{
                        try {
                            localStorage.setItem("telegram_chat_id", chatId);
                        } catch  {
                        // ignore
                        }
                        router.push("/dashboard");
                    },
                    disabled: !chatId.trim(),
                    style: {
                        padding: "10px 14px",
                        cursor: chatId.trim() ? "pointer" : "not-allowed"
                    },
                    children: "Continue"
                }, void 0, false, {
                    fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                    lineNumber: 37,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
                lineNumber: 36,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/page.tsx",
        lineNumber: 20,
        columnNumber: 5
    }, this);
}
}),
];

//# sourceMappingURL=Documents_Projects_2026_Email-AI-System_frontend_app_page_tsx_0gi39vc._.js.map