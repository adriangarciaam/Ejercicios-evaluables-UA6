const state = {
    user: null,
    entries: [],
    editingId: null,
};

const selectors = {
    accountBadge: document.querySelector("#account-badge"),
    accountName: document.querySelector("#account-name"),
    accountDetail: document.querySelector("#account-detail"),
    entryForm: document.querySelector("#entry-form"),
    flashContainer: document.querySelector("#flash-container"),
    healthButton: document.querySelector("#health-button"),
    healthCopy: document.querySelector("#health-copy"),
    healthPill: document.querySelector("#health-pill"),
    libraryTableBody: document.querySelector("#library-table-body"),
    loginForm: document.querySelector("#login-form"),
    logoutButton: document.querySelector("#logout-button"),
    passwordForm: document.querySelector("#password-form"),
    passwordUsername: document.querySelector("#password-username"),
    primaryAction: document.querySelector("#primary-action"),
    refreshButton: document.querySelector("#refresh-button"),
    registerForm: document.querySelector("#register-form"),
    sidebarSessionCopy: document.querySelector("#sidebar-session-copy"),
    sidebarSessionDetail: document.querySelector("#sidebar-session-detail"),
    topbarStatus: document.querySelector("#topbar-status"),
};

const STATUS_OPTIONS = ["wishlist", "playing", "completed", "dropped"];

function showFlash(kind, title, message) {
    const item = document.createElement("article");
    item.className = `flash flash--${kind}`;
    item.innerHTML = `<strong class="flash__title">${title}</strong><div class="flash__body">${message}</div>`;
    selectors.flashContainer.appendChild(item);
    window.setTimeout(() => item.remove(), 4200);
}

function toJsonMessage(payload, fallback) {
    if (!payload) {
        return fallback;
    }

    if (payload.message) {
        return payload.message;
    }

    if (payload.details) {
        return Object.entries(payload.details)
            .map(([key, value]) => `${key}: ${value}`)
            .join(", ");
    }

    return fallback;
}

async function requestJson(url, options = {}) {
    const config = {
        method: options.method || "GET",
        headers: {},
    };

    if (options.body !== undefined) {
        config.headers["Content-Type"] = "application/json";
        config.body = JSON.stringify(options.body);
    }

    const response = await fetch(url, config);
    let payload = null;

    try {
        payload = await response.json();
    } catch (error) {
        payload = null;
    }

    return { response, payload };
}

function setHealthState(ok, message) {
    selectors.healthPill.className = `status-badge ${ok ? "status-badge--ok" : "status-badge--alert"}`;
    selectors.healthPill.textContent = ok ? "OK" : "Error";
    selectors.healthCopy.textContent = message;
}

async function checkHealth() {
    selectors.healthCopy.textContent = "Comprobando /api/health/...";

    try {
        const { response, payload } = await requestJson("/api/health/");

        if (response.ok && payload?.status === "ok") {
            setHealthState(true, "Estado operativo. La API responde correctamente.");
            return;
        }

        setHealthState(false, "La comprobación no devolvió el estado esperado.");
    } catch (error) {
        setHealthState(false, "No se pudo contactar con la API.");
    }
}

function renderSessionState() {
    const isAuthenticated = Boolean(state.user);

    selectors.logoutButton.disabled = !isAuthenticated;
    selectors.passwordForm.querySelectorAll("input, button").forEach((element) => {
        element.disabled = !isAuthenticated;
    });
    selectors.entryForm.querySelectorAll("input, select, button").forEach((element) => {
        element.disabled = !isAuthenticated;
    });

    if (!isAuthenticated) {
        selectors.accountBadge.className = "status-badge status-badge--muted";
        selectors.accountBadge.textContent = "Sin sesión";
        selectors.accountName.textContent = "No autenticado";
        selectors.accountDetail.textContent = "Inicia sesión para ver y editar tu biblioteca.";
        selectors.sidebarSessionCopy.textContent = "No autenticado";
        selectors.sidebarSessionDetail.textContent = "Inicia sesión para cargar y actualizar tu colección.";
        selectors.topbarStatus.textContent = "Sesión pendiente";
        selectors.primaryAction.textContent = "Crear cuenta";
        selectors.passwordUsername.value = "";
        return;
    }

    selectors.accountBadge.className = "status-badge status-badge--ok";
    selectors.accountBadge.textContent = "Activa";
    selectors.accountName.textContent = state.user.username;
    selectors.accountDetail.textContent = `Usuario autenticado con id ${state.user.id}.`;
    selectors.sidebarSessionCopy.textContent = state.user.username;
    selectors.sidebarSessionDetail.textContent = "Puedes añadir juegos y editar tu progreso desde esta interfaz.";
    selectors.topbarStatus.textContent = `Sesión activa: ${state.user.username}`;
    selectors.primaryAction.textContent = "Añadir juego";
    selectors.passwordUsername.value = state.user.username;
}

function statusPill(status) {
    return `<span class="pill pill--${status}">${status}</span>`;
}

function createRow(entry) {
    const isEditing = state.editingId === entry.id;
    const statusControl = isEditing
        ? `<select class="inline-select" data-role="status">${STATUS_OPTIONS
              .map((option) => `<option value="${option}" ${option === entry.status ? "selected" : ""}>${option}</option>`)
              .join("")}</select>`
        : statusPill(entry.status);
    const hoursControl = isEditing
        ? `<input class="inline-number" data-role="hours" type="number" min="0" value="${entry.hours_played}">`
        : `<span>${entry.hours_played}</span>`;
    const actionControl = isEditing
        ? `<button class="mini-button mini-button--primary" type="button" data-action="save">Guardar</button>
           <button class="mini-button" type="button" data-action="cancel">Cancelar</button>`
        : `<button class="mini-button" type="button" data-action="edit">Editar</button>`;

    return `
        <tr data-entry-id="${entry.id}">
            <td>${entry.id}</td>
            <td>
                <div class="game-title">
                    <span class="game-title__mark">${entry.external_game_id.slice(0, 2)}</span>
                    <div>
                        <strong>${entry.external_game_id}</strong>
                    </div>
                </div>
            </td>
            <td>${statusControl}</td>
            <td>${hoursControl}</td>
            <td><div class="row-actions">${actionControl}</div></td>
        </tr>
    `;
}

function renderEntries() {
    if (!state.user) {
        selectors.libraryTableBody.innerHTML = `
            <tr class="table-empty">
                <td colspan="5">Inicia sesión para cargar tu biblioteca.</td>
            </tr>
        `;
        return;
    }

    if (!state.entries.length) {
        selectors.libraryTableBody.innerHTML = `
            <tr class="table-empty">
                <td colspan="5">Todavía no has añadido juegos. Usa el formulario de la derecha.</td>
            </tr>
        `;
        return;
    }

    selectors.libraryTableBody.innerHTML = state.entries.map(createRow).join("");
}

async function refreshSession() {
    try {
        const { response, payload } = await requestJson("/api/users/me/");

        if (!response.ok) {
            state.user = null;
            state.entries = [];
            state.editingId = null;
            renderSessionState();
            renderEntries();
            return;
        }

        state.user = payload;
        renderSessionState();
        await loadEntries();
    } catch (error) {
        state.user = null;
        state.entries = [];
        state.editingId = null;
        renderSessionState();
        renderEntries();
        showFlash("error", "Sesión", "No se pudo comprobar la sesión actual.");
    }
}

async function loadEntries() {
    if (!state.user) {
        renderEntries();
        return;
    }

    try {
        const { response, payload } = await requestJson("/api/library/entries/");

        if (!response.ok) {
            showFlash("error", "Biblioteca", toJsonMessage(payload, "No se pudo cargar la biblioteca."));
            return;
        }

        state.entries = payload;
        renderEntries();
    } catch (error) {
        showFlash("error", "Biblioteca", "No se pudo contactar con la API para cargar los juegos.");
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    const { response, payload: body } = await requestJson("/api/auth/login/", {
        method: "POST",
        body: payload,
    });

    if (!response.ok) {
        showFlash("error", "Login", toJsonMessage(body, "No se pudo iniciar sesión."));
        return;
    }

    form.reset();
    showFlash("success", "Login", `Sesión iniciada como ${body.username}.`);
    await refreshSession();
}

async function handleRegister(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    const { response, payload: body } = await requestJson("/api/auth/register/", {
        method: "POST",
        body: payload,
    });

    if (!response.ok) {
        showFlash("error", "Registro", toJsonMessage(body, "No se pudo crear la cuenta."));
        return;
    }

    form.reset();
    showFlash("success", "Registro", `Cuenta creada para ${body.username}. Ya puedes iniciar sesión.`);
}

async function handleLogout() {
    const { response, payload } = await requestJson("/api/auth/logout/", {
        method: "POST",
    });

    if (!response.ok) {
        showFlash("error", "Sesión", toJsonMessage(payload, "No se pudo cerrar la sesión."));
        return;
    }

    state.user = null;
    state.entries = [];
    state.editingId = null;
    renderSessionState();
    renderEntries();
    showFlash("success", "Sesión", "La sesión se ha cerrado.");
}

async function handlePassword(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    const { response, payload: body } = await requestJson("/api/users/me/password/", {
        method: "POST",
        body: payload,
    });

    if (!response.ok) {
        showFlash("error", "Contraseña", toJsonMessage(body, "No se pudo actualizar la contraseña."));
        return;
    }

    form.reset();
    showFlash("success", "Contraseña", body.message || "Contraseña actualizada.");
}

async function handleEntryCreate(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.hours_played = Number(payload.hours_played);

    const { response, payload: body } = await requestJson("/api/library/entries/", {
        method: "POST",
        body: payload,
    });

    if (!response.ok) {
        showFlash("error", "Biblioteca", toJsonMessage(body, "No se pudo añadir el juego."));
        return;
    }

    form.reset();
    form.elements.status.value = "wishlist";
    form.elements.hours_played.value = 0;
    showFlash("success", "Biblioteca", `${body.external_game_id} se ha añadido correctamente.`);
    await loadEntries();
}

async function saveEntry(entryId, row) {
    const status = row.querySelector('[data-role="status"]').value;
    const hours = Number(row.querySelector('[data-role="hours"]').value);

    const { response, payload } = await requestJson(`/api/library/entries/${entryId}/`, {
        method: "PATCH",
        body: {
            status,
            hours_played: hours,
        },
    });

    if (!response.ok) {
        showFlash("error", "Biblioteca", toJsonMessage(payload, "No se pudo actualizar el juego."));
        return;
    }

    state.entries = state.entries.map((entry) => (entry.id === entryId ? payload : entry));
    state.editingId = null;
    renderEntries();
    showFlash("success", "Biblioteca", `Juego ${payload.external_game_id} actualizado.`);
}

function bindTableActions(event) {
    const target = event.target.closest("button[data-action]");

    if (!target) {
        return;
    }

    const row = target.closest("tr[data-entry-id]");
    const entryId = Number(row.dataset.entryId);
    const action = target.dataset.action;

    if (action === "edit") {
        state.editingId = entryId;
        renderEntries();
        return;
    }

    if (action === "cancel") {
        state.editingId = null;
        renderEntries();
        return;
    }

    if (action === "save") {
        saveEntry(entryId, row);
    }
}

function handlePrimaryAction() {
    const targetId = state.user ? "#biblioteca" : "#cuenta";
    document.querySelector(targetId).scrollIntoView({ behavior: "smooth", block: "start" });
}

function initNavigationHighlight() {
    const links = [...document.querySelectorAll(".nav__link")];
    const sections = links
        .map((link) => document.querySelector(link.getAttribute("href")))
        .filter(Boolean);

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                links.forEach((link) => {
                    link.classList.toggle("is-active", link.getAttribute("href") === `#${entry.target.id}`);
                });
            });
        },
        {
            rootMargin: "-30% 0px -55% 0px",
            threshold: 0.1,
        },
    );

    sections.forEach((section) => observer.observe(section));
}

async function bootstrap() {
    const initialUserNode = document.querySelector("#initial-user-data");
    state.user = initialUserNode ? JSON.parse(initialUserNode.textContent) : null;
    renderSessionState();
    renderEntries();
    selectors.loginForm.addEventListener("submit", handleLogin);
    selectors.registerForm.addEventListener("submit", handleRegister);
    selectors.logoutButton.addEventListener("click", handleLogout);
    selectors.passwordForm.addEventListener("submit", handlePassword);
    selectors.entryForm.addEventListener("submit", handleEntryCreate);
    selectors.healthButton.addEventListener("click", checkHealth);
    selectors.refreshButton.addEventListener("click", async () => {
        await checkHealth();
        await refreshSession();
        showFlash("success", "Sincronización", "La interfaz se ha actualizado.");
    });
    selectors.primaryAction.addEventListener("click", handlePrimaryAction);
    selectors.libraryTableBody.addEventListener("click", bindTableActions);
    initNavigationHighlight();

    await checkHealth();
    if (state.user) {
        await loadEntries();
    }
}

bootstrap();
