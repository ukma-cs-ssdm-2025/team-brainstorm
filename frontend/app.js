const $ = (sel) => document.querySelector(sel);

function apiBase() {
  return $("#apiBase").value.replace(/\/$/, "");
}

function userEmail() {
  return $("#userEmail").value.trim();
}

function setHealth(status) {
  const el = $("#healthStatus");
  el.className = "badge";
  if (status === "ok") {
    el.classList.add("success");
    el.textContent = "online";
  } else if (status === "error") {
    el.classList.add("danger");
    el.textContent = "offline";
  } else {
    el.textContent = status;
  }
}

function showToast(message, kind = "info", timeout = 2500) {
  const t = $("#toast");
  t.textContent = message;
  t.className = `toast show ${kind}`;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => (t.className = "toast"), timeout);
}

async function ping() {
  try {
    const res = await fetch(`${apiBase()}/health`);
    if (!res.ok) throw new Error("status " + res.status);
    const json = await res.json();
    setHealth(json.status || "ok");
    showToast("API доступне", "info");
  } catch (e) {
    setHealth("error");
    showToast("API недоступне", "danger");
  }
}

function li(text) {
  const el = document.createElement("li");
  el.textContent = text;
  return el;
}

async function loadBooks() {
  const btn = $("#loadBooks");
  btn.setAttribute("aria-busy", "true");
  try {
    const availableOnly = $("#availableOnly").checked;
    const genres = $("#genres").value
      .split(",")
      .map((g) => g.trim())
      .filter(Boolean);
    const url = new URL(`${apiBase().replace(/\/$/, '')}/books/`, window.location.origin);
    if (availableOnly) url.searchParams.set("available_only", "true");
    for (const g of genres) url.searchParams.append("genres", g);

    const res = await fetch(url);
    if (!res.ok) throw new Error(await res.text());
    const books = await res.json();
    const list = $("#books");
    list.innerHTML = "";

    books.forEach((b) => {
      const available = Math.max(0, (b.total_copies ?? 0) - (b.reserved_count ?? 0));
      const item = document.createElement("li");
      item.innerHTML = `
        <div class="book">
          <div class="meta">
            <div class="title">${b.title}</div>
            <div class="sub">${b.author} • ISBN: ${b.isbn}</div>
            <div class="chips">${(b.genres || [])
              .map((g) => `<span class=\"chip\">${g}</span>`)
              .join("")}</div>
            <div class="sub">Доступно: ${available}</div>
          </div>
          <div class="actions">
            <label class="sr-only" for="until">До дати</label>
            <input type="date" class="input until" />
            <button class="btn btn-primary reserve">Зарезервувати</button>
            <button class="btn btn-outline fav">У вибране</button>
          </div>
        </div>
      `;

      item.querySelector(".reserve").addEventListener("click", async () => {
        const untilStr = item.querySelector(".until").value || null;
        const user_id = crypto.randomUUID();
        const payload = { user_id, book_id: b.id, until: untilStr };
        const button = item.querySelector(".reserve");
        button.setAttribute("aria-busy", "true");
        try {
          const r = await fetch(`${apiBase()}/reservations/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (!r.ok) throw new Error(await r.text());
          const created = await r.json();
          addReservationToList(created);
          showToast(`Створено резервацію ${created.id}`, "info");
        } catch (e) {
          showToast(`Помилка резервації: ${e}`, "danger");
        } finally {
          button.removeAttribute("aria-busy");
        }
      });

      item.querySelector(".fav").addEventListener("click", async () => {
        const email = userEmail();
        if (!email) {
          showToast("Вкажіть email (X-User-Email)", "danger");
          return;
        }
        const button = item.querySelector(".fav");
        button.setAttribute("aria-busy", "true");
        try {
          const r = await fetch(`${apiBase()}/favorites/me`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-User-Email": email,
            },
            body: JSON.stringify({ book_id: b.id }),
          });
          if (!r.ok) throw new Error(await r.text());
          await loadFavorites();
          showToast("Додано у вибране", "info");
        } catch (e) {
          showToast(`Помилка додавання у вибране: ${e}`, "danger");
        } finally {
          button.removeAttribute("aria-busy");
        }
      });

      list.appendChild(item);
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
        <div class="sub">ID: <code>${res.id}</code> • Книга: <code>${res.book_id}</code></div>
      </div>
      <button class="btn btn-danger cancel">Скасувати</button>
    </div>
  `;
  item.querySelector(".cancel").addEventListener("click", async () => {
    const btn = item.querySelector(".cancel");
    btn.setAttribute("aria-busy", "true");
    try {
      const r = await fetch(`${apiBase()}/reservations/${res.id}`, { method: "DELETE" });
      if (!r.ok && r.status !== 204) throw new Error(await r.text());
      item.remove();
      showToast("Резервацію скасовано", "info");
    } catch (e) {
      showToast(`Помилка скасування: ${e}` , "danger");
    }
  });
  list.appendChild(item);
}

async function loadFavorites() {
  const email = userEmail();
  if (!email) {
    showToast("Вкажіть email користувача (X-User-Email)", "danger");
    return;
  }
  const res = await fetch(`${apiBase()}/favorites/me?expand=true`, {
    headers: { "X-User-Email": email },
  });
  if (!res.ok) {
    showToast(`Не вдалося отримати вибране: ${await res.text()}`, "danger");
    return;
  }
  const data = await res.json();
  const list = $("#favorites");
  list.innerHTML = "";
  data.items.forEach((b) => {
    const item = document.createElement("li");
    item.innerHTML = `
      <div class="fav">
        <div>
          <div class="title">${b.title}</div>
          <div class="sub">${b.author}</div>
        </div>
        <div>
          <code>${b.id}</code>
          <button class="btn btn-danger rm" style="margin-left:8px">Прибрати</button>
        </div>
      </div>
    `;
    item.querySelector(".rm").addEventListener("click", async () => {
      const r = await fetch(`${apiBase()}/favorites/me/${b.id}`, {
        method: "DELETE",
        headers: { "X-User-Email": email },
      });
      if (!r.ok && r.status !== 204) {
        showToast(`Помилка видалення: ${await r.text()}`, "danger");
      }
      await loadFavorites();
    });
    list.appendChild(item);
  });
}

async function countFavorites() {
  const email = userEmail();
  if (!email) {
    showToast("Вкажіть email користувача (X-User-Email)", "danger");
    return;
  }
  const r = await fetch(`${apiBase()}/favorites/me/count`, {
    headers: { "X-User-Email": email },
  });
  if (!r.ok) {
    $("#favCount").textContent = "(помилка)";
    return;
  }
  const data = await r.json();
  const el = $("#favCount");
  el.className = "badge info";
  el.textContent = `Вибране: ${data.count}`;
}

async function clearFavorites() {
  const email = userEmail();
  if (!email) {
    showToast("Вкажіть email користувача (X-User-Email)", "danger");
    return;
  }
  await fetch(`${apiBase()}/favorites/me`, {
    method: "DELETE",
    headers: { "X-User-Email": email },
  });
  await loadFavorites();
  await countFavorites();
  showToast("Очищено", "info");
}

document.addEventListener("DOMContentLoaded", () => {
  $("#ping").addEventListener("click", ping);
  $("#loadBooks").addEventListener("click", loadBooks);
  $("#loadFavs").addEventListener("click", loadFavorites);
  $("#countFavs").addEventListener("click", countFavorites);
  $("#clearFavs").addEventListener("click", clearFavorites);
});
