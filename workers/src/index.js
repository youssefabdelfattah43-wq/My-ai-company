const BUSINESS = "si_natural";
const PUBLIC_TASK_LIMIT = 4;
const PUBLIC_TASK_WINDOW_MS = 60 * 60 * 1000;
const APPROVAL_ACTIONS = new Set([
  "campaign_publishing", "budget_changes", "price_changes",
  "bulk_messages", "refunds", "external_account_changes"
]);
const ROUTES = {
  competitor_analysis: "research",
  market_research: "research",
  trend_analysis: "research",
  content_creation: "creative",
  ad_copywriting: "creative",
  creative_brief: "creative",
  campaign_analysis: "media_buyer",
  read_ad_reports: "media_buyer",
  analyze_roas: "media_buyer",
  manage_leads: "sales_crm",
  prepare_replies: "sales_crm",
  order_report: "operations",
  inventory_report: "operations",
  profit_report: "operations"
};
const AGENTS = {
  research: "You are SI NATURAL's Research Agent. Research and reason only from supplied information. Separate verified facts, assumptions and recommendations. Never invent competitor prices or market data.",
  creative: "You are SI NATURAL's Creative Agent. Create conversion-focused Egyptian Arabic beauty and personal-care marketing concepts. Do not invent product ingredients, claims, certifications, reviews or results. Clearly flag missing product facts.",
  media_buyer: "You are SI NATURAL's Media Buying Agent. Analyze only supplied campaign metrics. Calculate metrics transparently, distinguish observations from hypotheses, and never claim access to Meta Ads unless data is supplied.",
  sales_crm: "You are SI NATURAL's Sales and CRM Agent. Prepare customer-service replies and follow-up plans in Egyptian Arabic. Do not send messages or invent customer/order details.",
  operations: "You are SI NATURAL's Business Operations Agent. Analyze only supplied orders, costs, stock and returns. Show formulas and assumptions. Never invent financial figures."
};
const json = (data, status = 200, extra = {}) => new Response(JSON.stringify(data), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra }
});
const now = () => new Date().toISOString();
const id = () => crypto.randomUUID();

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = (env.ALLOWED_ORIGIN || "").split(",").map(x => x.trim()).filter(Boolean);
  const headers = { "Vary": "Origin" };
  if (allowed.includes(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type";
    headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
  }
  return headers;
}
function approvalRequired(action) { return APPROVAL_ACTIONS.has(action); }
function routeTask(taskType) {
  const agent = ROUTES[taskType];
  if (!agent) throw new Error("Unsupported task_type");
  return agent;
}
async function runGemini(agent, taskType, description, env) {
  if (!env.GEMINI_API_KEY) throw new Error("AI provider is not configured");
  const model = env.GEMINI_MODEL || "gemini-2.5-flash";
  const prompt = [
    AGENTS[agent],
    "Business: SI NATURAL (Egyptian cosmetics and personal-care e-commerce).",
    "Task type: " + taskType,
    "User request and supplied context:",
    description,
    "Return a useful, structured answer in Egyptian Arabic. Do not claim to have performed external actions."
  ].join("

");
  const endpoint = "https://generativelanguage.googleapis.com/v1beta/models/" + encodeURIComponent(model) + ":generateContent";
  const requestBody = JSON.stringify({
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: { temperature: 0.5, maxOutputTokens: 1800 }
  });
  let response;
  let data = {};
  let lastNetworkError = null;
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      response = await fetch(endpoint, {
        method: "POST",
        headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
        body: requestBody,
        signal: AbortSignal.timeout(25000)
      });
      data = await response.json().catch(() => ({}));
      lastNetworkError = null;
      if (response.ok || ![429, 500, 502, 503, 504].includes(response.status) || attempt === 3) break;
    } catch (error) {
      lastNetworkError = error;
      if (attempt === 3) throw new Error("AI provider request timed out or failed: " + String(error.message || error).slice(0, 250));
    }
    await new Promise(resolve => setTimeout(resolve, 1200 * (attempt + 1)));
  }
  if (lastNetworkError) throw new Error("AI provider request timed out or failed: " + String(lastNetworkError.message || lastNetworkError).slice(0, 250));
  if (!response.ok) { const providerMessage = String(data.error?.message || data.error?.status || "No provider detail").slice(0, 400); throw new Error("AI provider request failed (" + response.status + "): " + providerMessage); }
  const text = data.candidates?.[0]?.content?.parts?.map(p => p.text || "").join("
").trim();
  if (!text) throw new Error("AI provider returned no text");
  return text;
}
async function writeAudit(env, type, taskId, details) {
  await env.DB.prepare("INSERT INTO audit_events (id,event_type,task_id,details,created_at) VALUES (?,?,?,?,?)")
    .bind(id(), type, taskId, JSON.stringify(details), now()).run();
}
async function handle(request, env) {
  const headers = corsHeaders(request, env);
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
  const url = new URL(request.url);
  if (url.pathname === "/health" && request.method === "GET") {
    return json({ status: "ok", service: "my-ai-company-si-natural", mode: "mvp" }, 200, headers);
  }
  if (url.pathname === "/api/si_natural/agents" && request.method === "GET") {
    return json({
      business: BUSINESS,
      agents: [
        { id: "research", name: "Research Agent", task_types: ["competitor_analysis", "market_research", "trend_analysis"] },
        { id: "creative", name: "Creative Agent", task_types: ["content_creation", "ad_copywriting", "creative_brief"] },
        { id: "media_buyer", name: "Media Buying Agent", task_types: ["campaign_analysis", "read_ad_reports", "analyze_roas"] },
        { id: "sales_crm", name: "Sales & CRM Agent", task_types: ["manage_leads", "prepare_replies"] },
        { id: "operations", name: "Business Operations Agent", task_types: ["order_report", "inventory_report", "profit_report"] }
      ]
    }, 200, headers);
  }
  if (url.pathname === "/api/public/tasks" && request.method === "POST") {
    const origin = request.headers.get("Origin") || "";
    const allowed = (env.ALLOWED_ORIGIN || "").split(",").map(x => x.trim()).filter(Boolean);
    if (origin && !allowed.includes(origin)) return json({ error: "Origin not allowed" }, 403, headers);
    let body; try { body = await request.json(); } catch { return json({ error: "Invalid JSON" }, 400, headers); }
    if (!body || Array.isArray(body) || typeof body.task_type !== "string" || typeof body.description !== "string" || !body.description.trim() || body.description.length > 5000 || !Object.prototype.hasOwnProperty.call(ROUTES,body.task_type)) return json({ error: "Choose a supported task and enter a description (max 5000 characters)." },400,headers);
    const ip=request.headers.get("CF-Connecting-IP")||"unknown";
    const digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(ip));
    const ipHash=Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,"0")).join("");
    const since=new Date(Date.now()-PUBLIC_TASK_WINDOW_MS).toISOString();
    const usage=await env.DB.prepare("SELECT COUNT(*) AS n FROM public_task_usage WHERE ip_hash=? AND created_at>?").bind(ipHash,since).first();
    if((usage?.n||0)>=PUBLIC_TASK_LIMIT)return json({error:"وصلت للحد المؤقت: 4 مهام في الساعة. جرّب بعد ساعة."},429,headers);
    const taskId=id(),stamp=now(),agent=ROUTES[body.task_type];
    await env.DB.prepare("INSERT INTO public_task_usage (id,ip_hash,created_at) VALUES (?,?,?)").bind(id(),ipHash,stamp).run();
    await env.DB.prepare("INSERT INTO tasks (id,business,task_type,description,assigned_agent,status,approval_required,created_at,updated_at) VALUES (?,?,?,?,?,'in_progress',0,?,?)").bind(taskId,BUSINESS,body.task_type,body.description.trim(),agent,stamp,stamp).run();
    try {
      const result=await runGemini(agent,body.task_type,body.description.trim(),env);
      await env.DB.prepare("UPDATE tasks SET result=?,status='completed',updated_at=? WHERE id=?").bind(result,now(),taskId).run();
      await writeAudit(env,"public_task_completed",taskId,{assigned_agent:agent});
      return json({id:taskId,assigned_agent:agent,status:"completed",result,remaining:PUBLIC_TASK_LIMIT-(usage?.n||0)-1},201,headers);
    } catch(error) {
      await env.DB.prepare("UPDATE tasks SET status='failed',error=?,updated_at=? WHERE id=?").bind(error.message,now(),taskId).run();
      await writeAudit(env,"public_task_failed",taskId,{error:error.message});
      return json({id:taskId,status:"failed",error:error.message},502,headers);
    }
  }
  if (!env.API_TOKEN || request.headers.get("Authorization") !== "Bearer " + env.API_TOKEN) {
    return json({ error: "Authentication required" }, 401, headers);
  }
  if (url.pathname === "/api/si_natural/tasks" && request.method === "GET") {
    const result = await env.DB.prepare("SELECT id,business,task_type,description,assigned_agent,status,approval_required,action,result,error,created_at,updated_at FROM tasks ORDER BY created_at DESC LIMIT 100").all();
    return json({ business: BUSINESS, tasks: result.results || [] }, 200, headers);
  }
  if (url.pathname === "/api/si_natural/approvals" && request.method === "GET") {
    const result = await env.DB.prepare("SELECT a.*,t.task_type,t.description,t.assigned_agent FROM approvals a JOIN tasks t ON t.id=a.task_id WHERE a.status='pending' ORDER BY a.requested_at DESC").all();
    return json({ business: BUSINESS, approvals: result.results || [] }, 200, headers);
  }
  if (url.pathname === "/api/si_natural/tasks" && request.method === "POST") {
    let body;
    try { body = await request.json(); } catch { return json({ error: "Invalid JSON" }, 400, headers); }
    if (!body || typeof body !== "object" || Array.isArray(body) ||
        typeof body.task_type !== "string" || typeof body.description !== "string" ||
        !body.description.trim() || body.description.length > 12000 ||
        (body.action != null && typeof body.action !== "string")) {
      return json({ error: "task_type, non-empty description (max 12000 chars), and optional string action are required" }, 400, headers);
    }
    let agent;
    try { agent = routeTask(body.task_type); } catch (e) { return json({ error: e.message }, 400, headers); }
    const taskId = id();
    const created = now();
    const gated = approvalRequired(body.action || null);
    await env.DB.prepare("INSERT INTO tasks (id,business,task_type,description,assigned_agent,status,approval_required,action,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)")
      .bind(taskId, BUSINESS, body.task_type, body.description.trim(), agent, gated ? "awaiting_approval" : "in_progress", gated ? 1 : 0, body.action || null, created, created).run();
    if (gated) {
      await env.DB.prepare("INSERT INTO approvals (id,task_id,action,status,requested_at) VALUES (?,?,?,?,?)")
        .bind(id(), taskId, body.action, "pending", created).run();
    }
    await writeAudit(env, "task_created", taskId, { task_type: body.task_type, assigned_agent: agent, approval_required: gated });
    try {
      const result = await runGemini(agent, body.task_type, body.description.trim(), env);
      const status = gated ? "awaiting_approval" : "completed";
      await env.DB.prepare("UPDATE tasks SET result=?,status=?,updated_at=? WHERE id=?")
        .bind(result, status, now(), taskId).run();
      await writeAudit(env, "agent_completed", taskId, { assigned_agent: agent });
      return json({ id: taskId, business: BUSINESS, task_type: body.task_type, assigned_agent: agent, status, approval_required: gated, result }, 201, headers);
    } catch (e) {
      await env.DB.prepare("UPDATE tasks SET status='failed',error=?,updated_at=? WHERE id=?")
        .bind(e.message, now(), taskId).run();
      await writeAudit(env, "agent_failed", taskId, { error: e.message });
      return json({ id: taskId, business: BUSINESS, assigned_agent: agent, status: "failed", error: e.message }, 502, headers);
    }
  }
  const decisionMatch = url.pathname.match(/^\/api\/si_natural\/approvals\/([0-9a-f-]+)\/decision$/i);
  if (decisionMatch && request.method === "POST") {
    let body;
    try { body = await request.json(); } catch { return json({ error: "Invalid JSON" }, 400, headers); }
    if (!["approved", "rejected"].includes(body?.decision)) return json({ error: "decision must be approved or rejected" }, 400, headers);
    const taskId = decisionMatch[1];
    const stamp = now();
    const row = await env.DB.prepare("SELECT status FROM approvals WHERE task_id=?").bind(taskId).first();
    if (!row || row.status !== "pending") return json({ updated: false }, 409, headers);
    await env.DB.batch([
      env.DB.prepare("UPDATE approvals SET status=?,decided_at=?,decision_note=? WHERE task_id=? AND status='pending'").bind(body.decision, stamp, String(body.note || "").slice(0,500), taskId),
      env.DB.prepare("UPDATE tasks SET status=?,updated_at=? WHERE id=?").bind(body.decision, stamp, taskId)
    ]);
    await writeAudit(env, "approval_" + body.decision, taskId, { note: String(body.note || "").slice(0,500) });
    return json({ updated: true }, 200, headers);
  }
  return json({ error: "Route not found" }, 404, headers);
}
export default { fetch: handle };
export { routeTask, approvalRequired };