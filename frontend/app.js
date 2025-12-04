// helper
const $ = (sel) => document.querySelector(sel);

function addListener(selector, event, handler) {
  const el = $(selector);
  if (el) el.addEventListener(event, handler);
}
addListener("#clearReservations", "click", async () => {
    if (!confirm("Очистити всі резервації?")) return;

    try {
        await fetch(`${apiBase()}/reservations/clear/all`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });

        await loadReservations();
        await loadReservedBooks();
        await loadBooks();

        showToast("Усі резервації очищено", "info");

    } catch (err) {
        showToast("Помилка очищення", "danger");
    }
});


function apiBase() {
  const baseEl = $("#apiBase");
  return (baseEl ? baseEl.value : "/api").replace(/\/$/, "");
}

function userEmail() {
  const el = $("#userEmail");
  return el ? el.value.trim() : "";
}

function showToast(message, kind = "info", timeout = 2500) {
  const t = $("#toast");
  if (!t) return;
  t.textContent = message;
  t.className = `toast show ${kind}`;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => (t.className = "toast"), timeout);
}

// ---------- AUTH helpers ----------
function storeToken(token) {
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

function getToken() {
  return localStorage.getItem("token");
}

function storeEmail(email) {
  if (email) localStorage.setItem("email", email);
  else localStorage.removeItem("email");
}

function getStoredEmail() {
  return localStorage.getItem("email");
}

function updateAuthUI(email) {
  const cur = $("#currentUser");
  const logoutBtn = $("#logoutBtn");
  const emailInput = $("#userEmail");

  if (!cur) return;

  if (email) {
    cur.textContent = email;
    cur.removeAttribute("href");
    cur.classList.add("is-logged");
    if (logoutBtn) logoutBtn.style.display = "inline-block";
    if (emailInput) emailInput.value = email;
    storeEmail(email);
  } else {
    cur.textContent = "Увійти";
    cur.setAttribute("href", "auth.html");
    cur.classList.remove("is-logged");
    if (logoutBtn) logoutBtn.style.display = "none";
    if (emailInput) emailInput.value = "";
    storeEmail(null);
  }
}


function getAuthHeaders() {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const email = userEmail();
  if (email) headers["X-User-Email"] = email;
  return headers;
}

// ---------- Registration & Login ----------
async function registerUser() {
  const email = $("#reg-email")?.value.trim();
  const password = $("#reg-password")?.value;
  const role = $("#reg-role")?.value || "user";
  const msg = $("#auth-message");
  if (msg) msg.textContent = "";

  if (!email || !password) {
    if (msg) msg.textContent = "Вкажіть email та пароль";
    return;
  }

  try {
    const res = await fetch(`${apiBase()}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Помилка" }));
      throw new Error(err.detail || "Помилка реєстрації");
    }

    if (msg) msg.textContent = "✅ Реєстрація успішна. Логінемо вас...";

    // auto-login after registration
    const loginRes = await fetch(`${apiBase()}/users/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!loginRes.ok) {
      if (msg) msg.textContent = "✅ Реєстрація успішна. Тепер увійдіть вручну.";
      return;
    }

    const loginData = await loginRes.json();
    console.log("AUTO LOGIN RESPONSE:", loginData);

    // <-- ТУТ СЕРВЕР ПОВЕРТАЄ loginData.access_token
    storeToken(loginData.access_token);
    updateAuthUI(email);

    window.location.href = "index.html";
  } catch (e) {
    if (msg) msg.textContent = `❌ ${e.message}`;
  }
}

async function loginUser() {
  const email = $("#login-email")?.value.trim();
  const password = $("#login-password")?.value;
  const msg = $("#auth-message");
  if (msg) msg.textContent = "";

  if (!email || !password) {
    if (msg) msg.textContent = "Вкажіть email та пароль";
    return;
  }

  try {
    const res = await fetch(`${apiBase()}/users/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Помилка входу" }));
      throw new Error(err.detail || "Помилка входу");
    }

    const data = await res.json();
    console.log("LOGIN RESPONSE:", data);

    // <-- ТУТ БЕРЕМО data.access_token
    storeToken(data.access_token);
    updateAuthUI(email);

    if (msg) msg.textContent = "✅ Вхід успішний";

    if (location.pathname.endsWith("auth.html")) {
      window.location.href = "index.html";
    }
  } catch (e) {
    if (msg) msg.textContent = `❌ ${e.message}`;
  }
}

function logout() {
  storeToken(null);
  updateAuthUI(null);
  showToast("Ви вийшли", "info");

  // on dashboard, send back to auth
  const onDashboard =
    location.pathname.endsWith("index.html") || location.pathname.endsWith("/");
  if (onDashboard) {
    window.location.href = "auth.html";
  }
}

// ---------- Books / UI ----------
function li(text) {
  const el = document.createElement("li");
  el.textContent = text;
  return el;
}

async function loadBooks() {
  const btn = $("#loadBooks");
  btn.setAttribute("aria-busy", "true");

  try {
    // --- Фільтри ---
    const availableOnly = $("#availableOnly").checked;
    const genres = $("#genres").value
      .split(",")
      .map((g) => g.trim())
      .filter(Boolean);

    const url = new URL(`${apiBase().replace(/\/$/, "")}/books/`, window.location.origin);
    if (availableOnly) url.searchParams.set("available_only", "true");
    genres.forEach((g) => url.searchParams.append("genres", g));

    // --- Запит ---
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error(await res.text());

    const books = await res.json();
    const list = $("#books");
    list.innerHTML = "";

    // --- Генерація списку ---
    books.forEach((b) => {
      const li = document.createElement("li");
      const available = b.total_copies - b.reserved_count;

      li.innerHTML = `
        <div class="book">
          <div>
            <div class="title">${escapeHtml(b.title)}</div>
            <div class="muted small">Автор: ${escapeHtml(b.author || "—")}</div>
            <div class="muted small">Жанр: ${escapeHtml((b.genres || []).join(", ") || "—")}</div>
            <div class="muted small">ID: ${escapeHtml(b.id)}</div>
            <div class="muted small">  Статус: ${available > 0 ? "✅ Доступна" : "⛔ Зарезервована"}</div>
          </div>

          <div class="actions">
            <button
              class="btn btn-outline reserve-btn"
              data-id="${escapeHtml(b.id)}"
              ${available > 0 ? "" : "disabled"}>
              Резервувати
            </button>

            <button
              class="btn btn-outline fav-btn"
              data-id="${escapeHtml(b.id)}">
              У вибране
            </button>
          </div>
        </div>
      `;

      // --- Резервування ---
      li.querySelector(".reserve-btn")?.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;

        if (!confirm(`Зарезервувати книгу ID ${id}?`)) return;

        const button = e.currentTarget;
        button.setAttribute("aria-busy", "true");

        try {
          const r = await fetch(`${apiBase()}/reservations/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...getAuthHeaders(),
            },
            body: JSON.stringify({ book_id: id }),
          });

          if (!r.ok) throw new Error(await r.text());

          showToast("Резервація створена", "success");
          await loadBooks();
          await loadReservations();

        } catch (err) {
          showToast(`Помилка резервації: ${err}`, "danger");
        } finally {
          button.removeAttribute("aria-busy");
        }
      });

      // --- Додавання у вибране ---
      li.querySelector(".fav-btn")?.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        const button = e.currentTarget;

        button.setAttribute("aria-busy", "true");

        try {
          const r = await fetch(`${apiBase()}/favorites/me`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...getAuthHeaders(),
            },
            body: JSON.stringify({ book_id: id }),
          });

          if (!r.ok) throw new Error(await r.text());

          showToast("Додано у вибране", "info");
          await loadFavorites();

        } catch (err) {
          showToast(`Помилка: ${err}`, "danger");
        } finally {
          button.removeAttribute("aria-busy");
        }
      });

      list.appendChild(li);
    });
  } catch (e) {
    showToast("Не вдалося завантажити книги", "danger");
  } finally {
    btn.removeAttribute("aria-busy");
  }
}

function addReservationToList(res) {
  const list = $("#reservations");
  const item = document.createElement("li");
  item.innerHTML = `
    <div class="fav">
      <div>
        <div class="title">Резервація</div>
        <div class="muted small">Книга ID: ${escapeHtml(res.book_id)}</div>
        <div class="muted small">Користувач: ${escapeHtml(res.user_email || userEmail() || "—")}</div>
        <div class="muted small">Статус: ${escapeHtml(res.status)}</div>
        <div class="muted small">Створено: ${escapeHtml(res.from_date || "—")}</div>
      </div>
      <div class="actions">
        <button class="btn btn-outline cancel-res-btn" data-id="${escapeHtml(res.id)}">Скасувати</button>
      </div>
    </div>
  `;

  item.querySelector(".cancel-res-btn")?.addEventListener("click", async (e) => {
    const id = e.currentTarget.dataset.id;
    const ok = confirm(`Скасувати резервацію ID ${id}?`);
    if (!ok) return;
    const button = e.currentTarget;
    button.setAttribute("aria-busy", "true");
    try {
      const r = await fetch(`${apiBase()}/reservations/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (!r.ok) throw new Error(await r.text());
      await loadReservations();
      await loadBooks();
      showToast("Резервація скасована", "info");
    } catch (err) {
      showToast(`Помилка скасування: ${err}`, "danger");
    } finally {
      button.removeAttribute("aria-busy");
    }
  });

  list.appendChild(item);
}

async function loadReservations() {
  const list = $("#reservations");
  list.innerHTML = "";
  try {
    const res = await fetch(`${apiBase()}/reservations/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(await res.text());
    const reservations = await res.json();
    reservations.forEach(addReservationToList);
  } catch (e) {
    // optional: silently ignore on pages without reservations list
  }
}

async function loadFavorites() {
  const btn = $("#loadFavs");
  if (btn) btn.setAttribute("aria-busy", "true");
  try {
    const res = await fetch(`${apiBase()}/favorites/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(await res.text());
    const favs = await res.json();
    const list = $("#favorites");
    list.innerHTML = "";
    favs.forEach((b) => {
      const item = document.createElement("li");
      item.innerHTML = `
        <div class="fav">
          <div>
            <div class="title">${escapeHtml(b.title)}</div>
            <div class="muted small">Автор: ${escapeHtml(b.author || "—")}</div>
            <div class="muted small">ID: ${escapeHtml(b.id)}</div>
          </div>
          <div class="actions">
            <button class="btn btn-outline remove-fav-btn" data-id="${escapeHtml(b.id)}">Прибрати</button>
          </div>
        </div>
      `;
      item.querySelector(".remove-fav-btn")?.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        const ok = confirm(`Прибрати з вибраного книгу ID ${id}?`);
        if (!ok) return;
        const button = e.currentTarget;
        button.setAttribute("aria-busy", "true");
        try {
          const r = await fetch(`${apiBase()}/favorites/me/${id}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
          });
          if (!r.ok) throw new Error(await r.text());
          await loadFavorites();
          await countFavorites();
          showToast("Прибрано", "info");
        } catch (err) {
          showToast(`Помилка видалення: ${err}`, "danger");
        } finally {
          button.removeAttribute("aria-busy");
        }
      });
      list.appendChild(item);
    });
    await countFavorites();
  } catch (e) {
    showToast("Не вдалося завантажити вибране", "danger");
  } finally {
    if (btn) btn.removeAttribute("aria-busy");
  }
}

async function countFavorites() {
  try {
    const res = await fetch(`${apiBase()}/favorites/me/count`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    $("#favCount").textContent = data.count ?? 0;
  } catch {
    // ignore
  }
}

async function searchByGenres() {
    const genres = $("#genres").value
      .split(",")
      .map((g) => g.trim().toLowerCase())
      .filter(Boolean);

    if (genres.length === 0) {
        showToast("Введіть жанр для пошуку", "warning");
        return;
    }

    const url = new URL(`${apiBase()}/books/search`, window.location.origin);
    genres.forEach((g) => url.searchParams.append("genres", g));

    try {
        const res = await fetch(url, { headers: getAuthHeaders() });
        if (!res.ok) throw new Error(await res.text());

        const books = await res.json();
        const list = $("#books");

        list.innerHTML = "";

        books.forEach(renderBook);

    } catch (e) {
        showToast("Помилка пошуку за жанрами", "danger");
    }
}
function renderBook(b) {
  const list = $("#books");
  const li = document.createElement("li");
  const available = b.total_copies - b.reserved_count;

  li.innerHTML = `
    <div class="book">
      <div>
        <div class="title">${escapeHtml(b.title)}</div>
        <div class="muted small">Автор: ${escapeHtml(b.author || "—")}</div>
        <div class="muted small">Жанр: ${escapeHtml((b.genres || []).join(", ") || "—")}</div>
        <div class="muted small">ID: ${escapeHtml(b.id)}</div>
        <div class="muted small">Статус: ${available > 0 ? "✅ Доступна" : "⛔ Зарезервована"}</div>
      </div>

      <div class="actions">
        <button class="btn btn-outline reserve-btn" data-id="${escapeHtml(b.id)}"
          ${available > 0 ? "" : "disabled"}>
          Резервувати
        </button>

        <button class="btn btn-outline fav-btn" data-id="${escapeHtml(b.id)}">
          У вибране
        </button>
      </div>
    </div>
  `;

  // прив'язуємо ті ж самі події — як у loadBooks()
  li.querySelector(".reserve-btn")?.addEventListener("click", reserveHandler);
  li.querySelector(".fav-btn")?.addEventListener("click", favoriteHandler);

  list.appendChild(li);
}


async function loadReservedBooks() {
    try {
        const res = await fetch(`${apiBase()}/reservations/me`, {
            headers: getAuthHeaders(),
        });

        if (!res.ok) {
            console.error("Помилка завантаження резервацій:", await res.text());
            return;
        }

        const data = await res.json();
        const container = document.getElementById("reservedBooksList");
        container.innerHTML = "";

        data.forEach(item => {
            const endTime = item.until
                ? new Date(item.until).toLocaleDateString("uk-UA")
                : "—";

            const div = document.createElement("div");
            div.classList.add("reserved-item");

            div.innerHTML = `
                <strong>${item.book?.title || "Без назви"}</strong><br>
                До: <span class="time">${endTime}</span>
            `;

            container.appendChild(div);
        });

    } catch (err) {
        console.error("loadReservedBooks error:", err);
    }
}


async function clearFavorites() {
  const ok = confirm("Очистити вибране?");
  if (!ok) return;
  await fetch(`${apiBase()}/favorites/me`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  await loadFavorites();
  await countFavorites();
  showToast("Очищено", "info");
}

// escape basic html to avoid injection when inserting text
function escapeHtml(s) {
  if (!s && s !== 0) return "";
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

// ---------- Init / events ----------
document.addEventListener("DOMContentLoaded", () => {
  // Books / favorites / reservations — only if elements exist
  addListener("#loadBooks", "click", loadBooks);
  addListener("#searchByGenres", "click", searchByGenres);
  addListener("#loadFavs", "click", loadFavorites);
  addListener("#countFavs", "click", countFavorites);
  addListener("#clearFavs", "click", clearFavorites);

  // Auth buttons — only if elements exist
  addListener("#register-btn", "click", registerUser);
  addListener("#login-btn", "click", loginUser);
  addListener("#logoutBtn", "click", logout);

  // Restore session
  const token = getToken();
  const savedEmail = getStoredEmail();
  if (token && savedEmail) {
    updateAuthUI(savedEmail);

    // Довантажуємо все, що потрібно авторизованому користувачу
    loadReservations();
    loadFavorites();
    loadReservedBooks();
  } else {
    updateAuthUI(null);
  }

  // Guard: if user opens dashboard without token, redirect to auth
  const onDashboard =
    location.pathname.endsWith("index.html") || location.pathname.endsWith("/");
  if (onDashboard && !token) {
    window.location.href = "auth.html";
  }
});
