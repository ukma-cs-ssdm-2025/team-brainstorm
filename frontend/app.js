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

function getCoverUrl(book) {
  if (book.cover_image) return book.cover_image;
  if (book.isbn) {
    return `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(
      book.isbn
    )}-L.jpg?default=false`;
  }
  return "";
}

function renderCover(book) {
  const coverUrl = getCoverUrl(book);
  const title = escapeHtml(book.title || "книгу");

  if (!coverUrl) {
    return `<div class="book__cover">
      <div class="book__cover--blank">Обкладинка</div>
    </div>`;
  }

  return `
    <div class="book__cover" data-has-cover>
      <img
        src="${coverUrl}"
        alt="Обкладинка ${title}"
        onload="this.closest('.book__cover')?.classList.add('is-loaded')"
        onerror="this.style.display='none'; this.closest('.book__cover')?.classList.add('is-broken')"
      />
      <div class="book__cover--blank">Обкладинка</div>
    </div>
  `;
}

let currentReviewBookId = null;
let currentReviewBookTitle = "";
let selectedReviewRating = 0;
let reviewRatingStars = [];
let currentEditBook = null;

function openBookEditor(book) {
  if (!isLibrarian()) return;
  currentEditBook = book;
  const modal = $("#bookEditModal");
  const form = $("#bookEditForm");
  if (!modal || !form) return;

  $("#bookEditModalTitle").textContent = `Редагування: ${escapeHtml(
    book.title || "Нова книга"
  )}`;
  $("#editBookIsbn").textContent = book.isbn || "—";

  form.elements.title.value = book.title || "";
  form.elements.author.value = book.author || "";
  form.elements.description.value = book.description || "";
  form.elements.year.value = book.published_year ?? "";
  form.elements.genres.value = (book.genres || []).join(", ");
  form.elements.copies.value = book.total_copies ?? "";
  form.elements.cover_image.value = book.cover_image || "";

  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
}

function closeBookEditor() {
  const modal = $("#bookEditModal");
  const form = $("#bookEditForm");
  if (modal) {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
  }
  if (form) {
    form.reset();
  }
  currentEditBook = null;
}

async function handleBookEditSubmit(event) {
  event.preventDefault();
  if (!currentEditBook) return;
  const form = event.currentTarget;
  const title = form.elements.title.value.trim();
  const author = form.elements.author.value.trim();
  if (!title || !author) {
    showToast("Назва та автор обов'язкові", "danger");
    return;
  }

  const description = form.elements.description.value.trim();
  const yearValue = Number(form.elements.year.value);
  const genres = (form.elements.genres.value || "")
    .split(",")
    .map((g) => g.trim())
    .filter(Boolean);
  const cover = form.elements.cover_image.value.trim();
  const copiesValue = Number(form.elements.copies.value);

  const payload = {
    title,
    author,
    description: description || undefined,
    published_year: Number.isFinite(yearValue) ? yearValue : undefined,
    genres: genres.length ? genres : undefined,
    cover_image: cover || undefined,
    total_copies: Number.isFinite(copiesValue) ? copiesValue : undefined,
  };

  try {
    const resp = await fetch(`${apiBase()}/books/${currentEditBook.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || "Не вдалося оновити книгу");
    }

    closeBookEditor();
    await loadBooks();
    showToast("Інформацію про книгу оновлено", "success");
  } catch (err) {
    showToast(`Не вдалося зберегти: ${err.message || err}`, "danger");
  }
}

// ---------- AUTH helpers ----------
function storeToken(token) {
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

function getToken() {
  return localStorage.getItem("token");
}

function storeRole(role) {
  if (role) localStorage.setItem("role", role);
  else localStorage.removeItem("role");
}

function getStoredRole() {
  return localStorage.getItem("role");
}

function isLibrarian() {
  return getStoredRole() === "librarian";
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
    const roleLabel = getStoredRole() === "librarian" ? " (бібліотекар)" : "";
    cur.textContent = `${email}${roleLabel}`;
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
  if (typeof updateReviewFormState === "function") {
    updateReviewFormState();
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

    if (msg) msg.textContent = "Реєстрація успішна. Логінемо вас...";

    // auto-login after registration
    const loginRes = await fetch(`${apiBase()}/users/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!loginRes.ok) {
      if (msg) msg.textContent = "Реєстрація успішна. Тепер увійдіть вручну.";
      return;
    }

    const loginData = await loginRes.json();
    console.log("AUTO LOGIN RESPONSE:", loginData);

    // <-- ТУТ СЕРВЕР ПОВЕРТАЄ loginData.access_token
    storeToken(loginData.access_token);
    storeRole(loginData.role);
    updateAuthUI(email);

    window.location.href = "index.html";
  } catch (e) {
    if (msg) msg.textContent = `error ${e.message}`;
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
    storeRole(data.role);
    updateAuthUI(email);

    if (msg) msg.textContent = " Вхід успішний";

    if (location.pathname.endsWith("auth.html")) {
      window.location.href = "index.html";
    }
  } catch (e) {
    if (msg) msg.textContent = `error ${e.message}`;
  }
}

function logout() {
  storeToken(null);
  storeRole(null);
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

    const url = new URL(`${apiBase().replace(/\/$/, "")}/books/search`, window.location.origin);
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
      li.dataset.bookId = b.id;
      const available = b.total_copies - b.reserved_count;
      const descriptionHtml = b.description
        ? `<p class="muted small book-description">${escapeHtml(
            b.description
          )}</p>`
        : "";
      const yearHtml = b.published_year
        ? `<p class="muted small book-year">Рік видання: ${escapeHtml(
            String(b.published_year)
          )}</p>`
        : "";
      const editBtn = isLibrarian()
        ? `<button class="btn btn-ghost edit-btn" data-id="${escapeHtml(
            b.id
          )}">Редагувати</button>`
        : "";
      li.innerHTML = `
        <div class="book">
          ${renderCover(b)}
          <div>
            <div class="title">${escapeHtml(b.title)}</div>
            <div class="muted small">Автор: ${escapeHtml(b.author || "-")}</div>
            ${descriptionHtml}
            ${yearHtml}
            <div class="muted small">Жанр: ${escapeHtml((b.genres || []).join(", ") || "-")}</div>
            <div class="muted small">  Статус: ${available > 0 ? " Доступна" : " Зарезервована"}</div>
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
            <button
              class="btn btn-ghost review-btn"
              data-id="${escapeHtml(b.id)}"
              data-title="${escapeHtml(b.title)}">
              Відгуки
            </button>
            ${editBtn}
          </div>
        </div>
      `;

      // --- Резервування ---
      li.querySelector(".reserve-btn")?.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;

        const bookTitle = escapeHtml(b.title || "книгу");
        if (!confirm(`Зарезервувати "${bookTitle}"?`)) return;

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
      li.querySelector(".review-btn")?.addEventListener("click", () => {
        selectReviewTarget({ id: b.id, title: b.title });
      });
      li.querySelector(".edit-btn")?.addEventListener("click", () => openBookEditor(b));

      list.appendChild(li);
    });
    highlightActiveBookCard();
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
        <div class="muted small">Користувач: ${escapeHtml(res.user_email || userEmail() || "-")}</div>
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
    const bookTitle = escapeHtml(res.book?.title || "книгу");
    const ok = confirm(`Скасувати резервацію "${bookTitle}"?`);
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
          </div>
          <div class="actions">
            <button class="btn btn-outline remove-fav-btn" data-id="${escapeHtml(b.id)}">Прибрати</button>
          </div>
        </div>
      `;
      item.querySelector(".remove-fav-btn")?.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        const title = escapeHtml(b.title || "книгу");
        const ok = confirm(`Прибрати "${title}" з вибраного?`);
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


function renderBook(b) {
  const list = $("#books");
  const li = document.createElement("li");
  const available = b.total_copies - b.reserved_count;
  const descriptionHtml = b.description
    ? `<p class="muted small book-description">${escapeHtml(b.description)}</p>`
    : "";
  const yearHtml = b.published_year
    ? `<p class="muted small book-year">Рік видання: ${escapeHtml(String(b.published_year))}</p>`
    : "";
  const editBtn = isLibrarian()
    ? `<button class="btn btn-ghost edit-btn" data-id="${escapeHtml(b.id)}">Редагувати</button>`
    : "";

  li.innerHTML = `
    <div class="book">
      ${renderCover(b)}
      <div>
        <div class="title">${escapeHtml(b.title)}</div>
        <div class="muted small">Автор: ${escapeHtml(b.author || "-")}</div>
        ${descriptionHtml}
        ${yearHtml}
        <div class="muted small">Жанр: ${escapeHtml((b.genres || []).join(", ") || "-")}</div>
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
        ${editBtn}
      </div>
    </div>
  `;

  // прив'язуємо ті ж самі події — як у loadBooks()
  li.querySelector(".reserve-btn")?.addEventListener("click", reserveHandler);
  li.querySelector(".fav-btn")?.addEventListener("click", favoriteHandler);
  li.querySelector(".edit-btn")?.addEventListener("click", () => openBookEditor(b));

  list.appendChild(li);
}

function pluralizeReviews(count) {
  const numeric = Number(count);
  const total = Math.max(0, Number.isFinite(numeric) ? numeric : 0);
  if (total === 1) return "1 відгук";
  if (total > 1 && total < 5) return `${total} відгуки`;
  return `${total} відгуків`;
}

function formatReviewDate(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleDateString("uk-UA", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function highlightActiveBookCard() {
  document.querySelectorAll("#books li").forEach((li) => {
    const bookEl = li.querySelector(".book");
    const isActive = li.dataset.bookId === currentReviewBookId;
    if (bookEl) {
      bookEl.classList.toggle("is-active-book", isActive);
    }
  });
}

function selectReviewTarget(book = {}) {
  if (!book.id) return;
  const bookId = String(book.id);
  const isNew = bookId !== currentReviewBookId;
  currentReviewBookId = bookId;
  currentReviewBookTitle = book.title || "";
  const label = $("#reviewTargetLabel");
  if (label) {
    label.innerHTML = `Відгуки для <strong>${escapeHtml(currentReviewBookTitle)}</strong>`;
  }
  if (isNew) {
    resetReviewForm();
  }
  updateReviewFormState();
  loadReviewsForBook(currentReviewBookId);
  highlightActiveBookCard();
}

async function loadReviewsForBook(bookId) {
  if (!bookId) return;
  const summary = $("#reviewSummary");
  const average = $("#reviewAverageValue");
  const count = $("#reviewCountBadge");
  const list = $("#reviewList");

  if (list) {
    list.innerHTML = `<p class="muted small">Завантаження відгуків...</p>`;
  }

  try {
    const resp = await fetch(`${apiBase()}/books/${bookId}/reviews`, {
      headers: getAuthHeaders(),
    });

    if (!resp.ok) {
      throw new Error(await resp.text());
    }

    const data = await resp.json();
    const averageValue = Number(data.average_rating ?? 0).toFixed(1);
    average && (average.textContent = averageValue);
    count && (count.textContent = pluralizeReviews(data.count ?? 0));
    summary?.classList.remove("hidden");

    if (list) {
      if (!Array.isArray(data.items) || data.items.length === 0) {
        list.innerHTML = `<p class="muted small">Поки що немає відгуків. Станьте першим!</p>`;
      } else {
        list.innerHTML = "";
        data.items.forEach((review) => list.appendChild(renderReviewItem(review)));
      }
    }
  } catch (error) {
    summary?.classList.add("hidden");
    if (list) {
      list.innerHTML = `<p class="muted small">Не вдалося завантажити відгуки.</p>`;
    }
    const message = error?.message || error;
    showToast(`Не вдалося завантажити відгуки: ${message}`, "danger");
  }
}

function renderReviewItem(review) {
  const comment = (review.comment || "").trim() || "Без коментаря";
  const author = review.user_email || "Анонім";
  const postedAt = formatReviewDate(review.created_at);
  const card = document.createElement("div");
  card.className = "review-item";
  card.innerHTML = `
    <div class="review-item__header">
      <div class="review-item__rating">
        <span aria-hidden="true">★</span>
        <span>${escapeHtml(String(review.rating ?? 0))}/5</span>
      </div>
      <span class="muted small">${escapeHtml(author)}</span>
    </div>
    <p class="review-item__comment">${escapeHtml(comment)}</p>
    <div class="review-item__meta">${escapeHtml(postedAt)}</div>
  `;
  return card;
}

function setReviewRating(value) {
  selectedReviewRating = value;
  reviewRatingStars.forEach((star) => {
    const starValue = Number(star.dataset.value);
    const isActive = starValue > 0 && starValue <= value;
    star.classList.toggle("is-active", isActive);
    star.setAttribute("aria-pressed", String(isActive));
  });
  updateReviewFormState();
}

function resetReviewForm() {
  setReviewRating(0);
  const commentInput = $("#reviewComment");
  if (commentInput) {
    commentInput.value = "";
  }
}

function updateReviewFormState() {
  const isBookSelected = Boolean(currentReviewBookId);
  const hasRating = selectedReviewRating > 0;
  const isAuthed = Boolean(getToken());
  const submitBtn = $("#submitReviewButton");
  const commentInput = $("#reviewComment");
  const hint = $("#reviewFormHint");

  reviewRatingStars.forEach((star) => {
    star.disabled = !isBookSelected;
  });

  if (submitBtn) {
    submitBtn.disabled = !(isBookSelected && hasRating && isAuthed);
  }
  if (commentInput) {
    commentInput.disabled = !isBookSelected;
  }
  if (hint) {
    if (!isBookSelected) {
      hint.textContent = "Оберіть книгу, щоб залишити відгук.";
    } else if (!isAuthed) {
      hint.textContent = "Авторизуйтесь, щоб поділитися відгуком.";
    } else if (!hasRating) {
      hint.textContent = "Оберіть оцінку, щоб продовжити.";
    } else {
      hint.textContent = "Додайте коментар та натисніть «Поділитися враженнями».";
    }
  }
}

async function handleReviewSubmit(event) {
  event.preventDefault();
  if (!currentReviewBookId) {
    showToast("Оберіть книгу, до якої хочете залишити відгук.", "info");
    return;
  }
  if (selectedReviewRating === 0) {
    showToast("Оберіть оцінку перед публікацією.", "info");
    return;
  }

  const commentInput = $("#reviewComment");
  const payload = {
    rating: selectedReviewRating,
    comment: commentInput ? commentInput.value.trim() : "",
  };
  const button = $("#submitReviewButton");
  button?.setAttribute("aria-busy", "true");

  try {
    const resp = await fetch(`${apiBase()}/books/${currentReviewBookId}/reviews`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || "Не вдалося додати відгук.");
    }

    await loadReviewsForBook(currentReviewBookId);
    resetReviewForm();
    showToast("Відгук додано", "success");
  } catch (error) {
    const message = error?.message || error;
    showToast(`Не вдалося додати відгук: ${message}`, "danger");
  } finally {
    button?.removeAttribute("aria-busy");
  }
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
  // Books / favorites / reservations – only if elements exist
  addListener("#loadBooks", "click", loadBooks);
  addListener("#loadFavs", "click", loadFavorites);
  addListener("#countFavs", "click", countFavorites);
  addListener("#clearFavs", "click", clearFavorites);

  reviewRatingStars = Array.from(document.querySelectorAll(".rating-input__star"));
  reviewRatingStars.forEach((star) => {
    star.addEventListener("click", () => {
      if (star.disabled) return;
      setReviewRating(Number(star.dataset.value));
    });
  });
  const reviewForm = $("#reviewForm");
  reviewForm?.addEventListener("submit", handleReviewSubmit);

  const editForm = $("#bookEditForm");
  editForm?.addEventListener("submit", handleBookEditSubmit);

  const editModal = $("#bookEditModal");
  if (editModal) {
    editModal
      .querySelectorAll("[data-modal-close]")
      .forEach((el) => el.addEventListener("click", closeBookEditor));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !editModal.classList.contains("hidden")) {
        closeBookEditor();
      }
    });
  }

  // Auth buttons – only if elements exist
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
  updateReviewFormState();
});
