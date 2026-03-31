module.exports = [
"[project]/Documents/Projects/2026/Email-AI-System/frontend/src/lib/api.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getApplications",
    ()=>getApplications
]);
const backendBase = ("TURBOPACK compile-time value", "http://localhost:8000");
async function getApplications(chatId) {
    if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
    ;
    const res = await fetch(`${backendBase}/dashboard/applications`, {
        method: "GET",
        headers: {
            "x-telegram-chat-id": chatId
        }
    });
    if (!res.ok) {
        const text = await res.text().catch(()=>"");
        throw new Error(`Backend error ${res.status}: ${text}`);
    }
    return await res.json();
}
}),
"[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Projects/2026/Email-AI-System/frontend/src/lib/api.ts [app-ssr] (ecmascript)");
"use client";
;
;
;
function DashboardPage() {
    const [chatId, setChatId] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("");
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const [apps, setApps] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])([]);
    const backendBase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMemo"])(()=>("TURBOPACK compile-time value", "http://localhost:8000") || "", []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        try {
            const saved = localStorage.getItem("telegram_chat_id");
            if (saved) setChatId(saved);
        } catch  {
        // ignore
        }
    }, []);
    async function refresh() {
        const trimmed = chatId.trim();
        if (!trimmed) return;
        setLoading(true);
        try {
            const data = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getApplications"])(trimmed);
            setApps(data);
        } catch (e) {
            setApps([]);
            alert(e?.message || "Failed to load applications");
        } finally{
            setLoading(false);
        }
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
        style: {
            padding: 24,
            fontFamily: "system-ui, sans-serif"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                style: {
                    marginBottom: 10
                },
                children: "Job Application Dashboard"
            }, void 0, false, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                lineNumber: 39,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    marginBottom: 12
                },
                children: [
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
                                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                lineNumber: 44,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                        lineNumber: 42,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        style: {
                            display: "flex",
                            gap: 10,
                            marginTop: 8,
                            alignItems: "center"
                        },
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: refresh,
                                disabled: loading || !chatId.trim(),
                                style: {
                                    padding: "10px 14px",
                                    cursor: loading ? "progress" : "pointer"
                                },
                                children: loading ? "Refreshing..." : "Refresh"
                            }, void 0, false, {
                                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                lineNumber: 53,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                style: {
                                    fontSize: 12,
                                    color: "#555"
                                },
                                children: [
                                    "Backend: ",
                                    backendBase || "(set NEXT_PUBLIC_BACKEND_URL)"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                lineNumber: 60,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                        lineNumber: 52,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                lineNumber: 41,
                columnNumber: 7
            }, this),
            apps.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                children: "No applications found yet."
            }, void 0, false, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                lineNumber: 67,
                columnNumber: 9
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                style: {
                    width: "100%",
                    borderCollapse: "collapse"
                },
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                    style: {
                                        textAlign: "left",
                                        borderBottom: "1px solid #ddd",
                                        paddingBottom: 8
                                    },
                                    children: "Company"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                    lineNumber: 72,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                    style: {
                                        textAlign: "left",
                                        borderBottom: "1px solid #ddd",
                                        paddingBottom: 8
                                    },
                                    children: "Role"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                    lineNumber: 73,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                    style: {
                                        textAlign: "left",
                                        borderBottom: "1px solid #ddd",
                                        paddingBottom: 8
                                    },
                                    children: "Status"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                    lineNumber: 74,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                    style: {
                                        textAlign: "left",
                                        borderBottom: "1px solid #ddd",
                                        paddingBottom: 8
                                    },
                                    children: "Applied"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                    lineNumber: 75,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                            lineNumber: 71,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                        lineNumber: 70,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                        children: apps.map((j)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                        style: {
                                            paddingTop: 12
                                        },
                                        children: j.company
                                    }, void 0, false, {
                                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                        lineNumber: 81,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                        style: {
                                            paddingTop: 12
                                        },
                                        children: j.role || "-"
                                    }, void 0, false, {
                                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                        lineNumber: 82,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                        style: {
                                            paddingTop: 12
                                        },
                                        children: j.status
                                    }, void 0, false, {
                                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                        lineNumber: 83,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Projects$2f$2026$2f$Email$2d$AI$2d$System$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                        style: {
                                            paddingTop: 12
                                        },
                                        children: j.applied_at || "-"
                                    }, void 0, false, {
                                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                        lineNumber: 84,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, j.id, true, {
                                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                                lineNumber: 80,
                                columnNumber: 15
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                        lineNumber: 78,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
                lineNumber: 69,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Documents/Projects/2026/Email-AI-System/frontend/app/dashboard/page.tsx",
        lineNumber: 38,
        columnNumber: 5
    }, this);
}
}),
"[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

module.exports = __turbopack_context__.r("[project]/Documents/Projects/2026/Email-AI-System/frontend/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)").vendored['react-ssr'].ReactJsxDevRuntime;
}),
];

//# sourceMappingURL=Documents_Projects_2026_Email-AI-System_frontend_0k._j1t._.js.map