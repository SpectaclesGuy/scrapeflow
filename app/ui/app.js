const state = {
  user: null,
  project: null,
  conversation: null,
  messages: [],
  context: null,
};

const els = {
  baseUrl: document.getElementById("baseUrl"),
  healthBadge: document.getElementById("healthBadge"),
  workspaceForm: document.getElementById("workspaceForm"),
  messageForm: document.getElementById("messageForm"),
  messageContent: document.getElementById("messageContent"),
  messageList: document.getElementById("messageList"),
  contextCard: document.getElementById("contextCard"),
  contextVersion: document.getElementById("contextVersion"),
  activityFeed: document.getElementById("activityFeed"),
  userId: document.getElementById("userId"),
  projectId: document.getElementById("projectId"),
  conversationId: document.getElementById("conversationId"),
  reloadMessagesBtn: document.getElementById("reloadMessagesBtn"),
  refreshContextBtn: document.getElementById("refreshContextBtn"),
};

els.baseUrl.textContent = window.location.origin;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.success === false) {
    const detail = payload.message || payload.detail || `Request failed with status ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

function pushActivity(title, detail, tone = "info") {
  const item = document.createElement("article");
  item.className = "activity-item";
  item.innerHTML = `<h4>${title}</h4><p>${detail}</p>`;
  if (tone === "error") {
    item.style.borderColor = "rgba(177, 59, 50, 0.35)";
  }
  els.activityFeed.prepend(item);
}

function renderIds() {
  els.userId.textContent = state.user?.id || "Not created";
  els.projectId.textContent = state.project?.id || "Not created";
  els.conversationId.textContent = state.conversation?.id || "Not created";
}

function formatDate(value) {
  if (!value) return "Pending";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function renderMessages() {
  if (!state.messages.length) {
    els.messageList.className = "message-list empty-state";
    els.messageList.textContent = "Create a workspace and send a message to begin.";
    return;
  }

  els.messageList.className = "message-list";
  els.messageList.innerHTML = "";
  const template = document.getElementById("messageTemplate");

  state.messages.forEach((message) => {
    const node = template.content.cloneNode(true);
    node.querySelector(".message-role").textContent = message.role;
    node.querySelector(".message-time").textContent = formatDate(message.created_at);
    node.querySelector(".message-body").textContent = message.content;
    els.messageList.appendChild(node);
  });
}

function renderTags(values) {
  if (!values || !values.length) {
    return '<span class="tag">None</span>';
  }
  return values.map((value) => `<span class="tag">${value}</span>`).join("");
}

function renderContext() {
  if (!state.context) {
    els.contextVersion.textContent = "v0";
    els.contextCard.className = "context-card empty-state";
    els.contextCard.textContent = "No context loaded yet.";
    return;
  }

  const context = state.context;
  els.contextVersion.textContent = `v${context.version || 0}`;
  els.contextCard.className = "context-card";
  els.contextCard.innerHTML = `
    <div class="context-grid">
      <div class="context-field"><strong>Target URL</strong><span>${context.target_url || "-"}</span></div>
      <div class="context-field"><strong>Domain</strong><span>${context.domain || "-"}</span></div>
      <div class="context-field"><strong>Entity</strong><span>${context.entity || "-"}</span></div>
      <div class="context-field"><strong>Export Format</strong><span>${context.export_format || "-"}</span></div>
      <div class="context-field"><strong>Auth Required</strong><span>${context.auth_required ? "Yes" : "No"}</span></div>
      <div class="context-field"><strong>Updated</strong><span>${formatDate(context.updated_at)}</span></div>
    </div>
    <div>
      <strong>Fields</strong>
      <div class="tag-row">${renderTags(context.fields)}</div>
    </div>
    <div>
      <strong>Filters</strong>
      <div class="tag-row">${renderTags(context.filters)}</div>
    </div>
    <div>
      <strong>Current summary</strong>
      <div class="context-field"><span>${context.summary || context.current_plan || "No summary yet."}</span></div>
    </div>
  `;
}

async function checkHealth() {
  try {
    const payload = await api("/health", { method: "GET" });
    els.healthBadge.className = "status-pill ok";
    els.healthBadge.textContent = payload.data.status === "ok" ? "API healthy" : "API unknown";
    pushActivity("Health check", "Render service responded successfully.");
  } catch (error) {
    els.healthBadge.className = "status-pill error";
    els.healthBadge.textContent = "Health check failed";
    pushActivity("Health check", error.message, "error");
  }
}

async function createWorkspace(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const userName = form.get("userName").toString().trim();
  const userEmail = form.get("userEmail").toString().trim();
  const projectName = form.get("projectName").toString().trim();
  const conversationTitle = form.get("conversationTitle").toString().trim();

  try {
    const user = (await api("/users", {
      method: "POST",
      body: JSON.stringify({
        name: userName,
        email: userEmail,
        password_hash: "ui-seeded",
      }),
    })).data;

    const project = (await api("/projects", {
      method: "POST",
      body: JSON.stringify({
        user_id: user.id,
        name: projectName,
        description: "Created from the Render test console",
      }),
    })).data;

    const conversation = (await api("/conversations", {
      method: "POST",
      body: JSON.stringify({
        project_id: project.id,
        user_id: user.id,
        title: conversationTitle,
      }),
    })).data;

    state.user = user;
    state.project = project;
    state.conversation = conversation;
    renderIds();
    pushActivity("Workspace created", `User ${user.id}, project ${project.id}, and conversation ${conversation.id} were created live.`);
    await refreshContext();
    await loadMessages();
  } catch (error) {
    pushActivity("Workspace creation failed", error.message, "error");
  }
}

async function sendMessage(event) {
  event.preventDefault();
  if (!state.conversation) {
    pushActivity("Missing conversation", "Create a workspace before sending messages.", "error");
    return;
  }

  const content = els.messageContent.value.trim();
  if (!content) return;

  try {
    const payload = await api(`/conversations/${state.conversation.id}/messages`, {
      method: "POST",
      body: JSON.stringify({
        role: "user",
        content,
      }),
    });

    state.context = payload.data.context;
    state.messages.push(payload.data.message);
    els.messageContent.value = "";
    renderMessages();
    renderContext();
    pushActivity("Message stored", `Context version is now ${state.context.version}. Entity: ${state.context.entity || "-"}.`);
  } catch (error) {
    pushActivity("Message send failed", error.message, "error");
  }
}

async function loadMessages() {
  if (!state.conversation) return;
  try {
    const payload = await api(`/conversations/${state.conversation.id}/messages`, { method: "GET" });
    state.messages = payload.data;
    renderMessages();
    pushActivity("Messages reloaded", `${state.messages.length} messages fetched from the live API.`);
  } catch (error) {
    pushActivity("Message reload failed", error.message, "error");
  }
}

async function refreshContext() {
  if (!state.project) return;
  try {
    const payload = await api(`/projects/${state.project.id}/context`, { method: "GET" });
    state.context = payload.data;
    renderContext();
    pushActivity("Context refreshed", `Project context version ${state.context.version} loaded from Neon-backed storage.`);
  } catch (error) {
    pushActivity("Context refresh failed", error.message, "error");
  }
}

function bindSamples() {
  document.querySelectorAll(".sample-pill").forEach((button) => {
    button.addEventListener("click", () => {
      els.messageContent.value = button.dataset.prompt || "";
      els.messageContent.focus();
    });
  });
}

els.workspaceForm.addEventListener("submit", createWorkspace);
els.messageForm.addEventListener("submit", sendMessage);
els.reloadMessagesBtn.addEventListener("click", loadMessages);
els.refreshContextBtn.addEventListener("click", refreshContext);

bindSamples();
checkHealth();
renderIds();
renderMessages();
renderContext();
