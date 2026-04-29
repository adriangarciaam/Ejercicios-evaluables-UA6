const sessionStatus = document.querySelector("#session-status");
const resultLog = document.querySelector("#result-log");
const detailOutput = document.querySelector("#detail-output");
const entriesList = document.querySelector("#entries-list");
const healthButton = document.querySelector("#health-check");
const refreshSessionButton = document.querySelector("#refresh-session");
const logoutButton = document.querySelector("#logout-button");
const deleteAccountButton = document.querySelector("#delete-account-button");

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

function logResult(title, response, body) {
  const responseBody = response.status === 204 ? "(body vacio)" : formatJson(body);
  resultLog.textContent = `${title}\nHTTP ${response.status}\n${responseBody}`;
  resultLog.classList.toggle("error", response.status >= 400);
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let body = null;
  try {
    body = await response.json();
  } catch {
    body = {};
  }

  return { response, body };
}

function getFormData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function refreshSession() {
  const { response, body } = await apiRequest("/api/users/me/", {
    method: "GET",
  });

  if (response.ok) {
    sessionStatus.textContent = `${body.username} (#${body.id})`;
  } else {
    sessionStatus.textContent = "Sin autenticar";
  }

  logResult("GET /api/users/me/", response, body);
  return response.ok;
}

async function checkHealth() {
  const { response, body } = await apiRequest("/api/health/", {
    method: "GET",
  });

  logResult("GET /api/health/", response, body);
}

function renderEntries(entries) {
  if (!Array.isArray(entries) || entries.length === 0) {
    entriesList.innerHTML = "<p>No hay juegos guardados.</p>";
    return;
  }

  entriesList.innerHTML = "";
  for (const entry of entries) {
    const item = document.createElement("article");
    item.className = "entry-item";

    const content = document.createElement("div");
    const title = document.createElement("strong");
    const meta = document.createElement("span");
    const badge = document.createElement("span");

    title.textContent = entry.external_game_id;
    meta.className = "entry-meta";
    meta.textContent = `ID ${entry.id} - ${entry.hours_played} h`;
    badge.className = "badge";
    badge.textContent = entry.status;

    content.append(title, meta);
    item.append(content, badge);
    item.addEventListener("click", () => {
      document.querySelector("#detail-form [name='entry_id']").value = entry.id;
      document.querySelector("#patch-form [name='entry_id']").value = entry.id;
      document.querySelector("#put-form [name='entry_id']").value = entry.id;
      document.querySelector("#put-form [name='external_game_id']").value = entry.external_game_id;
      document.querySelector("#put-form [name='status']").value = entry.status;
      document.querySelector("#put-form [name='hours_played']").value = entry.hours_played;
      detailOutput.textContent = formatJson(entry);
    });
    entriesList.appendChild(item);
  }
}

async function loadEntries() {
  const { response, body } = await apiRequest("/api/library/entries/", {
    method: "GET",
  });

  if (response.ok) {
    renderEntries(body);
  } else {
    entriesList.innerHTML = "<p>No se pudo cargar la biblioteca.</p>";
  }

  logResult("GET /api/library/entries/", response, body);
}

healthButton.addEventListener("click", checkHealth);
refreshSessionButton.addEventListener("click", refreshSession);
document.querySelector("#load-entries").addEventListener("click", loadEntries);

logoutButton.addEventListener("click", async () => {
  const { response, body } = await apiRequest("/api/auth/logout/", {
    method: "POST",
    body: "",
  });

  logResult("POST /api/auth/logout/", response, body);
  sessionStatus.textContent = "Sin autenticar";
  entriesList.innerHTML = "<p>No hay juegos guardados.</p>";
  detailOutput.textContent = "";
});

deleteAccountButton.addEventListener("click", async () => {
  const confirmed = window.confirm("Seguro que quieres borrar tu cuenta y la biblioteca?");
  if (!confirmed) {
    return;
  }

  const { response, body } = await apiRequest("/api/users/me/", {
    method: "DELETE",
  });

  logResult("DELETE /api/users/me/", response, body);
  if (response.ok) {
    sessionStatus.textContent = "Sin autenticar";
    entriesList.innerHTML = "<p>No hay juegos guardados.</p>";
    detailOutput.textContent = "";
  }
});

document.querySelector("#register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);

  const { response, body } = await apiRequest("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(data),
  });

  logResult("POST /api/auth/register/", response, body);
});

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);

  const { response, body } = await apiRequest("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify(data),
  });

  logResult("POST /api/auth/login/", response, body);
  if (response.ok) {
    await refreshSession();
    await loadEntries();
  }
});

document.querySelector("#password-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);

  const { response, body } = await apiRequest("/api/users/me/password/", {
    method: "POST",
    body: JSON.stringify(data),
  });

  logResult("POST /api/users/me/password/", response, body);
  if (response.ok) {
    event.currentTarget.reset();
  }
});

document.querySelector("#entry-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  data.hours_played = Number(data.hours_played);

  const { response, body } = await apiRequest("/api/library/entries/", {
    method: "POST",
    body: JSON.stringify(data),
  });

  logResult("POST /api/library/entries/", response, body);
  if (response.ok) {
    event.currentTarget.reset();
    event.currentTarget.elements.hours_played.value = 0;
    await loadEntries();
  }
});

document.querySelector("#detail-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);

  const { response, body } = await apiRequest(`/api/library/entries/${data.entry_id}/`, {
    method: "GET",
  });

  detailOutput.textContent = formatJson(body);
  logResult(`GET /api/library/entries/${data.entry_id}/`, response, body);
});

document.querySelector("#patch-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = getFormData(form);
  const payload = {};

  if (data.status) {
    payload.status = data.status;
  }
  if (data.hours_played !== "") {
    payload.hours_played = Number(data.hours_played);
  }

  const { response, body } = await apiRequest(`/api/library/entries/${data.entry_id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

  logResult(`PATCH /api/library/entries/${data.entry_id}/`, response, body);
  if (response.ok) {
    detailOutput.textContent = formatJson(body);
    await loadEntries();
  }
});

document.querySelector("#put-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = getFormData(form);
  const payload = {
    external_game_id: data.external_game_id,
    status: data.status,
    hours_played: Number(data.hours_played),
  };

  const { response, body } = await apiRequest(`/api/library/entries/${data.entry_id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

  logResult(`PUT /api/library/entries/${data.entry_id}/`, response, body);
  if (response.ok) {
    detailOutput.textContent = formatJson(body);
    await loadEntries();
  }
});

refreshSession();
