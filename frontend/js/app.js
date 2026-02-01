// ═══════════════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════════════
let lists       = [];
let categories  = [];
let items       = [];
let currentList = null;
let recipes     = [];
let currentRecipe = null;
let recipeIngredients = [];
let recipeSteps = [];
let currentScaleFactor = 1;

// ═══════════════════════════════════════════════════════════
//  API HELPERS
// ═══════════════════════════════════════════════════════════
const API = "/api";
async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  const r = await fetch(API + path, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ═══════════════════════════════════════════════════════════
//  NAVIGATION
// ═══════════════════════════════════════════════════════════
function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("view--active"));
  document.getElementById(id).classList.add("view--active");
  updateTopbarNav(id);
}

function updateTopbarNav(currentView) {
  const actions = document.getElementById("topbarActions");
  actions.innerHTML = "";

  if (currentView === "viewLists") {
    const btn = document.createElement("button");
    btn.className = "btn btn--ghost";
    btn.innerHTML = "Recipes";
    btn.onclick = () => { showView("viewRecipes"); loadRecipes(); };
    actions.appendChild(btn);
  } else if (currentView === "viewRecipes") {
    const btn = document.createElement("button");
    btn.className = "btn btn--ghost";
    btn.innerHTML = "Lists";
    btn.onclick = () => { showView("viewLists"); loadLists(); };
    actions.appendChild(btn);
  }
}

// ═══════════════════════════════════════════════════════════
//  LISTS VIEW
// ═══════════════════════════════════════════════════════════
async function loadLists() {
  lists = await api("GET", "/lists");
  renderLists();
}

function renderLists() {
  const grid  = document.getElementById("listsGrid");
  const empty = document.getElementById("listsEmpty");
  // Remove old cards
  grid.querySelectorAll(".list-card").forEach(c => c.remove());

  if (!lists.length) { empty.style.display="block"; return; }
  empty.style.display = "none";

  lists.forEach((list, i) => {
    const card = document.createElement("div");
    card.className = "list-card";
    card.style.animationDelay = i * 0.04 + "s";
    card.innerHTML = `
      <div class="list-card__icon">🛍️</div>
      <div class="list-card__body">
        <div class="list-card__name">
          ${esc(list.name)}
          ${list.is_default ? '<span class="list-card__badge">Default</span>' : ''}
        </div>
        <div class="list-card__meta">Created ${formatDate(list.created)}</div>
      </div>
      <div class="list-card__actions">
        ${!list.is_default ? '<button data-action="setdefault" title="Set as default"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></button>' : ''}
        <button data-action="rename" title="Rename"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
        <button data-action="delete" title="Delete"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
      </div>`;
    card.addEventListener("click", (e) => {
      if (e.target.closest("[data-action]")) return;
      openList(list.id);
    });
    const setDefaultBtn = card.querySelector("[data-action=setdefault]");
    if (setDefaultBtn) {
      setDefaultBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await api("POST", `/lists/${list.id}/set-default`);
        await loadLists();
      });
    }
    card.querySelector("[data-action=rename]").addEventListener("click", (e) => {
      e.stopPropagation();
      openRenameModal(list);
    });
    card.querySelector("[data-action=delete]").addEventListener("click", (e) => {
      e.stopPropagation();
      openDeleteListModal(list);
    });
    grid.appendChild(card);
  });
}

// ═══════════════════════════════════════════════════════════
//  DETAIL VIEW
// ═══════════════════════════════════════════════════════════
async function openList(id) {
  currentList = lists.find(l => l.id === id);
  categories  = await api("GET", `/lists/${id}/categories`);
  items       = await api("GET", `/lists/${id}/items`);
  document.getElementById("detailNameInput").value = currentList.name;
  renderDetail();
  showView("viewDetail");
}

function renderDetail() {
  const body = document.getElementById("detailBody");
  body.innerHTML = "";

  // Group items by category
  const uncatItems = items.filter(i => !i.category);
  const catGroups  = categories.map(c => ({ cat: c, items: items.filter(i => i.category === c.id) }));

  // Uncategorised first
  if (uncatItems.length || !categories.length) {
    body.appendChild(buildCategorySection(null, uncatItems));
  }
  catGroups.forEach(g => {
    body.appendChild(buildCategorySection(g.cat, g.items));
  });

  updateStats();
}

function buildCategorySection(cat, catItems) {
  const section = document.createElement("div");
  section.className = "cat-section";

  // Header
  const header = document.createElement("div");
  header.className = "cat-section__header";
  if (cat) {
    header.innerHTML = `
      <div class="cat-section__name"><input value="${esc(cat.name)}" data-cat-id="${cat.id}" /></div>
      <div class="cat-section__actions">
        <button data-action="delcat" data-cat-id="${cat.id}" title="Remove category">✕</button>
      </div>`;
    const nameInput = header.querySelector("input");
    nameInput.addEventListener("change", async () => {
      await api("PUT", `/lists/${currentList.id}/categories/${cat.id}`, { name: nameInput.value });
      const c = categories.find(c => c.id === cat.id);
      if (c) c.name = nameInput.value;
    });
    header.querySelector("[data-action=delcat]").addEventListener("click", () => {
      openDeleteCategoryModal(cat);
    });
  } else {
    header.innerHTML = `<div class="cat-section__name" style="font-style:normal;color:var(--text-low);font-size:.82rem;">General</div>`;
  }
  section.appendChild(header);

  // Item list
  const list = document.createElement("div");
  list.className = "item-list";
  catItems.forEach(item => list.appendChild(buildItemRow(item)));
  section.appendChild(list);

  // Add-item bar
  section.appendChild(buildAddBar(cat ? cat.id : null));
  return section;
}

function buildItemRow(item) {
  const row = document.createElement("div");
  row.className = "item-row" + (item.done ? " item-row--done" : "");
  row.innerHTML = `
    <div class="item-row__check" data-id="${item.id}">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
    </div>
    <div class="item-row__name" title="${esc(item.name)}">${esc(item.name)}</div>
    ${item.quantity && item.quantity !== "1" ? `<span class="item-row__qty">×${esc(item.quantity)}</span>` : ""}
    <div class="item-row__actions">
      <button data-action="edit" data-id="${item.id}" title="Edit">✎</button>
      <button data-action="del"  data-id="${item.id}" title="Delete">✕</button>
    </div>`;
  row.querySelector(".item-row__check").addEventListener("click", async () => {
    const res = await api("POST", `/lists/${currentList.id}/items/${item.id}/toggle`);
    item.done = res.done;
    row.classList.toggle("item-row--done", !!item.done);
    updateStats();
  });
  row.querySelector("[data-action=edit]").addEventListener("click", () => openEditItemModal(item));
  row.querySelector("[data-action=del]").addEventListener("click",  () => openDeleteItemModal(item));
  return row;
}

function buildAddBar(categoryId) {
  const bar = document.createElement("div");
  bar.className = "add-bar";

  // Category select
  let selectHtml = "";
  if (categories.length > 1 || (categories.length === 1 && !categoryId)) {
    selectHtml = `<select id="addBarCat">
      <option value="">${categoryId ? categories.find(c=>c.id===categoryId)?.name || "General" : "General"}</option>
      ${categories.map(c => `<option value="${c.id}"${c.id===categoryId?' selected':''}>${esc(c.name)}</option>`).join("")}
    </select>`;
  }

  bar.innerHTML = `
    <input type="text" placeholder="Add an item…" class="add-bar__input" />
    <input type="text" placeholder="Qty" class="add-bar__qty" style="width:52px;" />
    <button class="add-bar__submit" title="Add">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
    </button>`;

  const nameInput = bar.querySelector(".add-bar__input");
  const qtyInput  = bar.querySelector(".add-bar__qty");

  const submit = async () => {
    const name = nameInput.value.trim();
    if (!name) return;
    const newItem = {
      name,
      quantity: qtyInput.value.trim() || "1",
      category: categoryId || null
    };
    const res = await api("POST", `/lists/${currentList.id}/items`, newItem);
    items.push({ ...newItem, id: res.id, done: 0 });
    nameInput.value = "";
    qtyInput.value  = "";
    renderDetail();
    nameInput.focus();
  };

  nameInput.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  bar.querySelector(".add-bar__submit").addEventListener("click", submit);
  return bar;
}

function updateStats() {
  const total = items.length;
  const done  = items.filter(i => i.done).length;
  const pct   = total ? (done / total * 100) : 0;
  document.getElementById("statsFill").style.width = pct + "%";
  document.getElementById("statsLabel").textContent = `${done} / ${total}`;
}

// ═══════════════════════════════════════════════════════════
//  MODALS
// ═══════════════════════════════════════════════════════════
function openModal(title, desc, bodyHtml, actions) {
  document.getElementById("modalTitle").textContent  = title;
  document.getElementById("modalDesc").textContent   = desc || "";
  document.getElementById("modalBody").innerHTML     = bodyHtml || "";
  document.getElementById("modalActions").innerHTML  = "";
  actions.forEach(a => {
    const btn = document.createElement("button");
    btn.className = "btn btn--sm " + (a.cls || "btn--ghost");
    btn.textContent = a.label;
    btn.addEventListener("click", a.fn);
    document.getElementById("modalActions").appendChild(btn);
  });
  document.getElementById("modalOverlay").classList.add("modal-overlay--open");
}
function closeModal() {
  document.getElementById("modalOverlay").classList.remove("modal-overlay--open");
}
document.getElementById("modalOverlay").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) closeModal();
});

// --- New List ---
document.getElementById("btnNewList").addEventListener("click", () => {
  openModal("New list", "Give your shopping list a name.", `
    <div class="modal__input-row">
      <label>List name</label>
      <input id="modalNewListName" type="text" placeholder="e.g. Weekly Groceries" autofocus />
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Create", cls: "btn--primary", fn: async () => {
      const name = document.getElementById("modalNewListName").value.trim();
      if (!name) return;
      const res = await api("POST", "/lists", { name });
      lists.unshift({ id: res.id, name, created: new Date().toISOString() });
      closeModal();
      renderLists();
    }}
  ]);
  setTimeout(() => document.getElementById("modalNewListName").focus(), 50);
});

// --- Rename List ---
function openRenameModal(list) {
  openModal("Rename list", "", `
    <div class="modal__input-row">
      <label>New name</label>
      <input id="modalRenameName" type="text" value="${esc(list.name)}" autofocus />
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Save", cls: "btn--primary", fn: async () => {
      const name = document.getElementById("modalRenameName").value.trim();
      if (!name) return;
      await api("PUT", `/lists/${list.id}`, { name });
      list.name = name;
      closeModal();
      renderLists();
    }}
  ]);
  setTimeout(() => document.getElementById("modalRenameName").focus(), 50);
}

// --- Delete List ---
function openDeleteListModal(list) {
  openModal("Delete list", `Are you sure you want to delete "${esc(list.name)}"? This can't be undone.`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Delete", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/lists/${list.id}`);
      lists = lists.filter(l => l.id !== list.id);
      closeModal();
      renderLists();
    }}
  ]);
}

// --- Edit Item ---
function openEditItemModal(item) {
  let catSelect = categories.map(c =>
    `<option value="${c.id}"${item.category===c.id?' selected':''}>${esc(c.name)}</option>`
  ).join("");

  openModal("Edit item", "", `
    <div class="modal__input-row">
      <label>Item name</label>
      <input id="modalEditName" type="text" value="${esc(item.name)}" />
    </div>
    <div class="modal__input-row">
      <label>Quantity</label>
      <input id="modalEditQty" type="text" value="${esc(item.quantity||'1')}" />
    </div>
    <div class="modal__input-row">
      <label>Note</label>
      <textarea id="modalEditNote">${esc(item.note||'')}</textarea>
    </div>
    <div class="modal__input-row">
      <label>Category</label>
      <select id="modalEditCat">
        <option value="">General</option>
        ${catSelect}
      </select>
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Save", cls: "btn--primary", fn: async () => {
      const updates = {
        name:     document.getElementById("modalEditName").value.trim(),
        quantity: document.getElementById("modalEditQty").value.trim() || "1",
        note:     document.getElementById("modalEditNote").value.trim(),
        category: document.getElementById("modalEditCat").value || null
      };
      if (!updates.name) return;
      await api("PUT", `/lists/${currentList.id}/items/${item.id}`, updates);
      Object.assign(item, updates);
      closeModal();
      renderDetail();
    }}
  ]);
}

// --- Delete Item ---
function openDeleteItemModal(item) {
  openModal("Delete item", `Remove "${esc(item.name)}" from your list?`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Delete", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/lists/${currentList.id}/items/${item.id}`);
      items = items.filter(i => i.id !== item.id);
      closeModal();
      renderDetail();
    }}
  ]);
}

// --- Delete Category ---
function openDeleteCategoryModal(cat) {
  openModal("Remove category", `Items in "${esc(cat.name)}" will move to General.`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Remove", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/lists/${currentList.id}/categories/${cat.id}`);
      items.filter(i => i.category === cat.id).forEach(i => i.category = null);
      categories = categories.filter(c => c.id !== cat.id);
      closeModal();
      renderDetail();
    }}
  ]);
}

// ═══════════════════════════════════════════════════════════
//  DETAIL FOOTER ACTIONS
// ═══════════════════════════════════════════════════════════
document.getElementById("btnBack").addEventListener("click", () => {
  // Save list name on back
  const name = document.getElementById("detailNameInput").value.trim();
  if (name && currentList && name !== currentList.name) {
    api("PUT", `/lists/${currentList.id}`, { name });
    currentList.name = name;
    const li = lists.find(l => l.id === currentList.id);
    if (li) li.name = name;
  }
  showView("viewLists");
  renderLists();
});

document.getElementById("detailNameInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") e.target.blur();
});
document.getElementById("detailNameInput").addEventListener("blur", async () => {
  const name = document.getElementById("detailNameInput").value.trim();
  if (name && currentList && name !== currentList.name) {
    await api("PUT", `/lists/${currentList.id}`, { name });
    currentList.name = name;
    const li = lists.find(l => l.id === currentList.id);
    if (li) li.name = name;
  }
});

document.getElementById("btnAddCategory").addEventListener("click", async () => {
  openModal("New category", "Organise your list by category.", `
    <div class="modal__input-row">
      <label>Category name</label>
      <input id="modalCatName" type="text" placeholder="e.g. Produce, Dairy, …" autofocus />
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Add", cls: "btn--primary", fn: async () => {
      const name = document.getElementById("modalCatName").value.trim();
      if (!name) return;
      const res = await api("POST", `/lists/${currentList.id}/categories`, { name });
      categories.push({ id: res.id, name, list_id: currentList.id, position: res.position });
      closeModal();
      renderDetail();
    }}
  ]);
  setTimeout(() => document.getElementById("modalCatName").focus(), 50);
});

document.getElementById("btnClearDone").addEventListener("click", async () => {
  const doneCount = items.filter(i => i.done).length;
  if (!doneCount) return;
  openModal("Clear completed", `Remove ${doneCount} completed item${doneCount>1?'s':''}?`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Clear", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/lists/${currentList.id}/items/clear-done`);
      items = items.filter(i => !i.done);
      closeModal();
      renderDetail();
    }}
  ]);
});

// ═══════════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════════
function esc(s) {
  return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month:"short", day:"numeric", year:"numeric" });
}

// ═══════════════════════════════════════════════════════════
//  RECIPES VIEW
// ═══════════════════════════════════════════════════════════
async function loadRecipes() {
  recipes = await api("GET", "/recipes");
  renderRecipes();
}

function renderRecipes() {
  const grid  = document.getElementById("recipesGrid");
  const empty = document.getElementById("recipesEmpty");
  grid.querySelectorAll(".list-card").forEach(c => c.remove());

  if (!recipes.length) { empty.style.display="block"; return; }
  empty.style.display = "none";

  recipes.forEach((recipe, i) => {
    const card = document.createElement("div");
    card.className = "list-card";
    card.style.animationDelay = i * 0.04 + "s";
    const servingsText = recipe.servings ? `Serves ${recipe.servings}` : "";
    const times = [recipe.prep_time, recipe.cook_time].filter(Boolean).join(" • ");

    // Show photo thumbnail if available, otherwise show icon
    const thumbnailHTML = recipe.photo
      ? `<div class="list-card__thumbnail"><img src="${recipe.photo}" alt="${esc(recipe.name)}" /></div>`
      : `<div class="list-card__icon">🍳</div>`;

    card.innerHTML = `
      ${thumbnailHTML}
      <div class="list-card__body">
        <div class="list-card__name">${esc(recipe.name)}</div>
        <div class="list-card__meta">${servingsText}${servingsText && times ? " • " : ""}${times}</div>
      </div>
      <div class="list-card__actions">
        <button data-action="edit" title="Edit"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
        <button data-action="delete" title="Delete"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
      </div>`;
    card.addEventListener("click", (e) => {
      if (e.target.closest("[data-action]")) return;
      openRecipe(recipe.id);
    });
    card.querySelector("[data-action=edit]").addEventListener("click", (e) => {
      e.stopPropagation();
      openEditRecipeModal(recipe);
    });
    card.querySelector("[data-action=delete]").addEventListener("click", (e) => {
      e.stopPropagation();
      openDeleteRecipeModal(recipe);
    });
    grid.appendChild(card);
  });
}

// ═══════════════════════════════════════════════════════════
//  RECIPE DETAIL VIEW
// ═══════════════════════════════════════════════════════════
async function openRecipe(id) {
  currentRecipe = await api("GET", `/recipes/${id}`);
  recipeIngredients = await api("GET", `/recipes/${id}/ingredients`);
  recipeSteps = await api("GET", `/recipes/${id}/steps`);
  currentScaleFactor = 1;  // Reset scale factor when opening a recipe
  showView("viewRecipeDetail");
  renderRecipeDetail();
}

function renderRecipeDetail() {
  if (!currentRecipe) return;

  // Recipe name
  const nameInput = document.getElementById("recipeNameInput");
  nameInput.value = currentRecipe.name;
  nameInput.onblur = async () => {
    const newName = nameInput.value.trim();
    if (newName && newName !== currentRecipe.name) {
      await api("PUT", `/recipes/${currentRecipe.id}`, { name: newName });
      currentRecipe.name = newName;
      const recipe = recipes.find(r => r.id === currentRecipe.id);
      if (recipe) recipe.name = newName;
    }
  };
  nameInput.onkeydown = (e) => { if (e.key === "Enter") nameInput.blur(); };

  // Top actions
  const topActions = document.getElementById("recipeTopActions");
  topActions.innerHTML = `
    <button class="btn btn--sm btn--ghost" id="btnExportRecipe">📤 Export</button>
    <button class="btn btn--sm btn--danger" id="btnDeleteRecipe">Delete</button>`;
  document.getElementById("btnExportRecipe").onclick = async () => {
    try {
      const data = await api("GET", `/recipes/${currentRecipe.id}/export`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentRecipe.name.replace(/[^a-z0-9]/gi, '_')}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error exporting recipe: " + err.message);
    }
  };
  document.getElementById("btnDeleteRecipe").onclick = () => openDeleteRecipeModal(currentRecipe);

  // Recipe photo
  const photoSection = document.getElementById("recipePhoto");
  if (currentRecipe.photo) {
    photoSection.innerHTML = `
      <div class="recipe-photo">
        <img src="${currentRecipe.photo}" alt="${esc(currentRecipe.name)}" />
        <button class="btn btn--sm btn--danger recipe-photo__delete" id="btnDeletePhoto">Remove Photo</button>
      </div>
      <div class="recipe-photo-upload">
        <input type="file" id="recipePhotoInput" accept="image/*" style="display:none;" />
        <button class="btn btn--sm btn--ghost" id="btnChangePhoto">Change Photo</button>
      </div>`;
  } else {
    photoSection.innerHTML = `
      <div class="recipe-photo-upload">
        <input type="file" id="recipePhotoInput" accept="image/*" style="display:none;" />
        <button class="btn btn--sm btn--primary" id="btnUploadPhoto">📷 Add Photo</button>
      </div>`;
  }
  setupPhotoHandlers();

  // Recipe metadata
  const meta = document.getElementById("recipeMeta");
  meta.innerHTML = `
    <div class="recipe-meta__field">
      <div class="recipe-meta__label">Description</div>
      <textarea class="recipe-meta__input" id="recipeDescription" rows="2" placeholder="Brief description of the recipe">${esc(currentRecipe.description || "")}</textarea>
    </div>
    <div class="recipe-meta__field">
      <div class="recipe-meta__label">Notes</div>
      <textarea class="recipe-meta__input" id="recipeNotes" rows="3" placeholder="Tips, variations, serving suggestions, etc.">${esc(currentRecipe.notes || "")}</textarea>
    </div>
    <div class="recipe-meta__row">
      <div class="recipe-meta__field">
        <div class="recipe-meta__label">Servings</div>
        <input type="number" class="recipe-meta__input" id="recipeServings" value="${currentRecipe.servings || 4}" min="1" />
      </div>
      <div class="recipe-meta__field">
        <div class="recipe-meta__label">Prep Time</div>
        <input type="text" class="recipe-meta__input" id="recipePrepTime" value="${esc(currentRecipe.prep_time || "")}" placeholder="e.g. 15 mins" />
      </div>
      <div class="recipe-meta__field">
        <div class="recipe-meta__label">Cook Time</div>
        <input type="text" class="recipe-meta__input" id="recipeCookTime" value="${esc(currentRecipe.cook_time || "")}" placeholder="e.g. 30 mins" />
      </div>
    </div>`;

  // Auto-save metadata changes
  ["recipeDescription", "recipeNotes", "recipeServings", "recipePrepTime", "recipeCookTime"].forEach(id => {
    const el = document.getElementById(id);
    el.onblur = async () => {
      const updates = {
        description: document.getElementById("recipeDescription").value.trim(),
        notes: document.getElementById("recipeNotes").value.trim(),
        servings: parseInt(document.getElementById("recipeServings").value) || 4,
        prep_time: document.getElementById("recipePrepTime").value.trim(),
        cook_time: document.getElementById("recipeCookTime").value.trim()
      };
      await api("PUT", `/recipes/${currentRecipe.id}`, updates);
      Object.assign(currentRecipe, updates);
      const recipe = recipes.find(r => r.id === currentRecipe.id);
      if (recipe) Object.assign(recipe, updates);
    };
  });

  // Ingredients section
  const ingSection = document.getElementById("recipeIngredientsSection");
  ingSection.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
      <h3 class="recipe-section__header" style="margin-bottom: 0;">Ingredients</h3>
      <button class="btn btn--sm btn--primary" id="btnAddToShoppingList">
        🛒 Add to Shopping List
      </button>
    </div>
    <div class="recipe-scale-controls" id="scaleControls">
      <div class="recipe-scale-controls__label">Servings:</div>
      <button class="btn btn--sm btn--ghost" id="btnDecreaseServings" title="Decrease servings">−</button>
      <div class="recipe-scale-controls__value" id="scaledServings">${currentRecipe.servings || 4}</div>
      <button class="btn btn--sm btn--ghost" id="btnIncreaseServings" title="Increase servings">+</button>
      <button class="btn btn--sm btn--ghost" id="btnResetScale" style="margin-left: 8px; display: none;" title="Reset to original">↺ Reset</button>
    </div>
    <div class="recipe-section__list" id="ingredientsList"></div>
    <div class="recipe-add-bar" id="addIngredientBar">
      <input type="text" id="newIngredientName" placeholder="Ingredient name" />
      <input type="text" id="newIngredientQty" placeholder="Qty" style="max-width:80px;" />
      <input type="text" id="newIngredientUnit" placeholder="Unit" style="max-width:100px;" />
      <button class="btn btn--sm btn--primary">Add</button>
    </div>`;

  renderIngredients();

  // Scale controls handlers
  document.getElementById("btnIncreaseServings").onclick = () => {
    const newServings = (currentRecipe.servings || 4) * currentScaleFactor + 1;
    currentScaleFactor = newServings / (currentRecipe.servings || 4);
    updateScaleDisplay();
  };

  document.getElementById("btnDecreaseServings").onclick = () => {
    const currentServings = (currentRecipe.servings || 4) * currentScaleFactor;
    if (currentServings > 1) {
      const newServings = currentServings - 1;
      currentScaleFactor = newServings / (currentRecipe.servings || 4);
      updateScaleDisplay();
    }
  };

  document.getElementById("btnResetScale").onclick = () => {
    currentScaleFactor = 1;
    updateScaleDisplay();
  };

  function updateScaleDisplay() {
    const scaledServings = Math.round((currentRecipe.servings || 4) * currentScaleFactor);
    document.getElementById("scaledServings").textContent = scaledServings;
    document.getElementById("btnResetScale").style.display = currentScaleFactor === 1 ? 'none' : 'inline-block';
    renderIngredients();
  }

  // Add to shopping list handler
  const btnAddToShoppingList = document.getElementById("btnAddToShoppingList");
  if (btnAddToShoppingList) {
    btnAddToShoppingList.onclick = async () => {
      try {
        const result = await api("POST", `/recipes/${currentRecipe.id}/add-to-shopping-list`);

        // Show success with details
        let message = result.message;
        if (result.skipped.length) {
          message += '\n\nSkipped (already in list): ' + result.skipped.join(', ');
        }

        if (confirm(message + '\n\nView shopping list now?')) {
          await openList(result.list_id);
        }

      } catch (err) {
        const errorMsg = err.message || "Failed to add ingredients";

        if (errorMsg.includes("No default list")) {
          if (confirm("No default shopping list set. Would you like to go to the lists page to set one?")) {
            showView("viewLists");
            await loadLists();
          }
        } else {
          alert("Error: " + errorMsg);
        }
      }
    };
  }

  // Steps section
  const stepsSection = document.getElementById("recipeStepsSection");
  stepsSection.innerHTML = `
    <h3 class="recipe-section__header">Instructions</h3>
    <div class="recipe-section__list" id="stepsList"></div>
    <div class="recipe-add-bar" id="addStepBar">
      <textarea id="newStepInstruction" placeholder="Step instruction"></textarea>
      <button class="btn btn--sm btn--primary">Add</button>
    </div>`;
  renderSteps();

  // Add ingredient
  const addIngBar = document.getElementById("addIngredientBar");
  addIngBar.querySelector(".btn").onclick = async () => {
    const name = document.getElementById("newIngredientName").value.trim();
    if (!name) return;
    const ingredient = {
      name,
      quantity: document.getElementById("newIngredientQty").value.trim(),
      unit: document.getElementById("newIngredientUnit").value.trim()
    };
    const res = await api("POST", `/recipes/${currentRecipe.id}/ingredients`, ingredient);
    recipeIngredients.push({ ...ingredient, id: res.id, recipe_id: currentRecipe.id, position: res.position });
    document.getElementById("newIngredientName").value = "";
    document.getElementById("newIngredientQty").value = "";
    document.getElementById("newIngredientUnit").value = "";
    renderIngredients();
    document.getElementById("newIngredientName").focus();
  };

  // Add step
  const addStepBar = document.getElementById("addStepBar");
  addStepBar.querySelector(".btn").onclick = async () => {
    const instruction = document.getElementById("newStepInstruction").value.trim();
    if (!instruction) return;
    const res = await api("POST", `/recipes/${currentRecipe.id}/steps`, { instruction });
    recipeSteps.push({ id: res.id, recipe_id: currentRecipe.id, step_number: res.step_number, instruction });
    document.getElementById("newStepInstruction").value = "";
    renderSteps();
    document.getElementById("newStepInstruction").focus();
  };
}

// Quantity scaling utilities
function parseQuantity(qtyStr) {
  if (!qtyStr || typeof qtyStr !== 'string') return null;
  qtyStr = qtyStr.trim();
  if (!qtyStr) return null;

  // Handle ranges (e.g., "2-3")
  if (qtyStr.includes('-')) {
    const parts = qtyStr.split('-').map(p => parseQuantity(p.trim()));
    if (parts[0] !== null && parts[1] !== null) {
      return { type: 'range', min: parts[0].value, max: parts[1].value };
    }
  }

  // Handle fractions and mixed numbers
  // Patterns: "1/2", "1 1/2", "2.5", "2"
  const mixedRegex = /^(\d+)\s+(\d+)\/(\d+)$/;  // "1 1/2"
  const fractionRegex = /^(\d+)\/(\d+)$/;        // "1/2"
  const decimalRegex = /^(\d*\.?\d+)$/;          // "2.5" or "2"

  let match;
  if ((match = qtyStr.match(mixedRegex))) {
    const whole = parseInt(match[1]);
    const numerator = parseInt(match[2]);
    const denominator = parseInt(match[3]);
    return { type: 'number', value: whole + numerator / denominator };
  } else if ((match = qtyStr.match(fractionRegex))) {
    const numerator = parseInt(match[1]);
    const denominator = parseInt(match[2]);
    return { type: 'number', value: numerator / denominator };
  } else if ((match = qtyStr.match(decimalRegex))) {
    return { type: 'number', value: parseFloat(match[1]) };
  }

  // If we can't parse it, return as text (e.g., "a pinch", "to taste")
  return { type: 'text', value: qtyStr };
}

function scaleQuantity(qtyStr, scaleFactor) {
  if (scaleFactor === 1) return qtyStr;  // No scaling needed

  const parsed = parseQuantity(qtyStr);
  if (!parsed) return qtyStr;

  if (parsed.type === 'text') return qtyStr;  // Can't scale text

  if (parsed.type === 'range') {
    const scaledMin = formatQuantity(parsed.min * scaleFactor);
    const scaledMax = formatQuantity(parsed.max * scaleFactor);
    return `${scaledMin}-${scaledMax}`;
  }

  if (parsed.type === 'number') {
    return formatQuantity(parsed.value * scaleFactor);
  }

  return qtyStr;
}

function formatQuantity(num) {
  // Convert decimal to fraction if it's a common fraction
  const commonFractions = {
    0.125: '⅛', 0.25: '¼', 0.333: '⅓', 0.375: '⅜',
    0.5: '½', 0.625: '⅝', 0.666: '⅔', 0.75: '¾', 0.875: '⅞'
  };

  const whole = Math.floor(num);
  const decimal = num - whole;

  // Check if decimal part matches a common fraction (with tolerance)
  for (const [dec, frac] of Object.entries(commonFractions)) {
    if (Math.abs(decimal - parseFloat(dec)) < 0.01) {
      if (whole === 0) return frac;
      return `${whole} ${frac}`;
    }
  }

  // Round to 2 decimal places and remove trailing zeros after decimal point only
  const rounded = Math.round(num * 100) / 100;
  const str = rounded.toString();
  // Only remove trailing zeros if there's a decimal point (e.g., "2.50" → "2.5", but keep "500" as "500")
  return str.includes('.') ? str.replace(/\.?0+$/, '') : str;
}

function renderIngredients() {
  const list = document.getElementById("ingredientsList");
  if (!list) return;
  list.innerHTML = "";
  recipeIngredients.forEach((ing, i) => {
    const row = document.createElement("div");
    row.className = "recipe-ingredient-row";
    row.style.animationDelay = i * 0.03 + "s";
    row.draggable = true;
    row.dataset.ingredientId = ing.id;

    // Scale the quantity based on current scale factor
    const scaledQty = scaleQuantity(ing.quantity, currentScaleFactor || 1);
    const amount = [scaledQty, ing.unit].filter(Boolean).join(" ");

    row.innerHTML = `
      <div class="recipe-ingredient-row__drag-handle" title="Drag to reorder">⋮⋮</div>
      <div class="recipe-ingredient-row__content">
        <div class="recipe-ingredient-row__name">${esc(ing.name)}</div>
        ${amount ? `<div class="recipe-ingredient-row__amount">${esc(amount)}</div>` : ""}
      </div>
      <div class="recipe-row__actions">
        <button data-action="addtolist" title="Add to shopping list"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>
        <button data-action="edit" title="Edit"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
        <button data-action="delete" title="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
      </div>`;

    // Drag and drop handlers
    row.addEventListener('dragstart', (e) => {
      row.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', row.innerHTML);
    });

    row.addEventListener('dragend', () => {
      row.classList.remove('dragging');
      document.querySelectorAll('.recipe-ingredient-row').forEach(r => r.classList.remove('drag-over'));
    });

    row.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const dragging = document.querySelector('.dragging');
      if (dragging && dragging !== row) {
        row.classList.add('drag-over');
      }
    });

    row.addEventListener('dragleave', () => {
      row.classList.remove('drag-over');
    });

    row.addEventListener('drop', async (e) => {
      e.preventDefault();
      row.classList.remove('drag-over');
      const dragging = document.querySelector('.dragging');
      if (!dragging || dragging === row) return;

      // Reorder in DOM
      const allRows = [...list.querySelectorAll('.recipe-ingredient-row')];
      const dragIndex = allRows.indexOf(dragging);
      const dropIndex = allRows.indexOf(row);

      if (dragIndex < dropIndex) {
        row.after(dragging);
      } else {
        row.before(dragging);
      }

      // Update backend
      const newOrder = [...list.querySelectorAll('.recipe-ingredient-row')].map(r => r.dataset.ingredientId);
      try {
        await api("PUT", `/recipes/${currentRecipe.id}/ingredients/reorder`, { ingredient_ids: newOrder });
        // Reload to sync positions
        recipeIngredients = await api("GET", `/recipes/${currentRecipe.id}/ingredients`);
        renderIngredients();
      } catch (err) {
        alert("Error reordering: " + err.message);
        renderIngredients(); // Revert on error
      }
    });
    row.querySelector("[data-action=addtolist]").onclick = async () => {
      try {
        const result = await api("POST", `/recipes/${currentRecipe.id}/ingredients/${ing.id}/add-to-shopping-list`);
        if (result.skipped) {
          alert(result.message);
        } else {
          if (confirm(result.message + '\n\nView shopping list now?')) {
            await openList(result.list_id);
          }
        }
      } catch (err) {
        const errorMsg = err.message || "Failed to add ingredient";
        if (errorMsg.includes("No default list")) {
          if (confirm("No default shopping list set. Would you like to go to the lists page to set one?")) {
            showView("viewLists");
            await loadLists();
          }
        } else {
          alert("Error: " + errorMsg);
        }
      }
    };
    row.querySelector("[data-action=edit]").onclick = () => openEditIngredientModal(ing);
    row.querySelector("[data-action=delete]").onclick = () => openDeleteIngredientModal(ing);
    list.appendChild(row);
  });
}

function renderSteps() {
  const list = document.getElementById("stepsList");
  if (!list) return;
  list.innerHTML = "";
  recipeSteps.forEach((step, i) => {
    const row = document.createElement("div");
    row.className = "recipe-step-row";
    row.style.animationDelay = i * 0.03 + "s";
    row.draggable = true;
    row.dataset.stepId = step.id;
    row.innerHTML = `
      <div class="recipe-step-row__drag-handle" title="Drag to reorder">⋮⋮</div>
      <div class="recipe-step-row__number">${step.step_number}</div>
      <div class="recipe-step-row__text">${esc(step.instruction)}</div>
      <div class="recipe-row__actions">
        <button data-action="edit" title="Edit"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
        <button data-action="delete" title="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
      </div>`;

    // Drag and drop handlers
    row.addEventListener('dragstart', (e) => {
      row.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', row.innerHTML);
    });

    row.addEventListener('dragend', () => {
      row.classList.remove('dragging');
      document.querySelectorAll('.recipe-step-row').forEach(r => r.classList.remove('drag-over'));
    });

    row.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const dragging = document.querySelector('.dragging');
      if (dragging && dragging !== row) {
        row.classList.add('drag-over');
      }
    });

    row.addEventListener('dragleave', () => {
      row.classList.remove('drag-over');
    });

    row.addEventListener('drop', async (e) => {
      e.preventDefault();
      row.classList.remove('drag-over');
      const dragging = document.querySelector('.dragging');
      if (!dragging || dragging === row) return;

      // Reorder in DOM
      const allRows = [...list.querySelectorAll('.recipe-step-row')];
      const dragIndex = allRows.indexOf(dragging);
      const dropIndex = allRows.indexOf(row);

      if (dragIndex < dropIndex) {
        row.after(dragging);
      } else {
        row.before(dragging);
      }

      // Update backend
      const newOrder = [...list.querySelectorAll('.recipe-step-row')].map(r => r.dataset.stepId);
      try {
        await api("PUT", `/recipes/${currentRecipe.id}/steps/reorder`, { step_ids: newOrder });
        // Reload to sync step numbers
        recipeSteps = await api("GET", `/recipes/${currentRecipe.id}/steps`);
        renderSteps();
      } catch (err) {
        alert("Error reordering: " + err.message);
        renderSteps(); // Revert on error
      }
    });

    row.querySelector("[data-action=edit]").onclick = () => openEditStepModal(step);
    row.querySelector("[data-action=delete]").onclick = () => openDeleteStepModal(step);
    list.appendChild(row);
  });
}

function setupPhotoHandlers() {
  const uploadBtn = document.getElementById("btnUploadPhoto") || document.getElementById("btnChangePhoto");
  const deleteBtn = document.getElementById("btnDeletePhoto");
  const fileInput = document.getElementById("recipePhotoInput");

  if (uploadBtn) {
    uploadBtn.onclick = () => fileInput.click();
  }

  if (fileInput) {
    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert("Image too large. Please choose a file smaller than 5MB.");
        return;
      }

      // Upload photo
      const formData = new FormData();
      formData.append('photo', file);

      try {
        const response = await fetch(`/api/recipes/${currentRecipe.id}/photo`, {
          method: 'PUT',
          body: formData
        });

        if (!response.ok) {
          const error = await response.json();
          alert(error.error || "Failed to upload photo");
          return;
        }

        // Reload recipe to show new photo
        await openRecipe(currentRecipe.id);
      } catch (err) {
        alert("Error uploading photo: " + err.message);
      }
    };
  }

  if (deleteBtn) {
    deleteBtn.onclick = async () => {
      if (!confirm("Remove this photo?")) return;

      try {
        await api("DELETE", `/recipes/${currentRecipe.id}/photo`);
        await openRecipe(currentRecipe.id);
      } catch (err) {
        alert("Error deleting photo: " + err.message);
      }
    };
  }
}

// ═══════════════════════════════════════════════════════════
//  RECIPE MODALS
// ═══════════════════════════════════════════════════════════
document.getElementById("btnNewRecipe").addEventListener("click", () => {
  openModal("New recipe", "Create a new recipe.", `
    <div class="modal__input-row">
      <label>Recipe name</label>
      <input id="modalNewRecipeName" type="text" placeholder="e.g. Chocolate Chip Cookies" autofocus />
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Create", cls: "btn--primary", fn: async () => {
      const name = document.getElementById("modalNewRecipeName").value.trim();
      if (!name) return;
      const res = await api("POST", "/recipes", { name });
      const newRecipe = { id: res.id, name, description: "", servings: 4, prep_time: "", cook_time: "", created: new Date().toISOString() };
      recipes.unshift(newRecipe);
      closeModal();
      renderRecipes();
      openRecipe(res.id);
    }}
  ]);
  setTimeout(() => document.getElementById("modalNewRecipeName").focus(), 50);
});

document.getElementById("btnExportAllRecipes").addEventListener("click", async () => {
  try {
    const data = await api("GET", "/recipes/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recipes_export_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Error exporting recipes: " + err.message);
  }
});

document.getElementById("btnImportRecipes").addEventListener("click", () => {
  document.getElementById("importRecipeFile").click();
});

document.getElementById("importRecipeFile").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const text = await file.text();
    const data = JSON.parse(text);
    const result = await api("POST", "/recipes/import", data);

    alert(result.message + '\n\nImported: ' + result.imported.join(', '));

    // Reload recipes
    await loadRecipes();

    // Clear file input
    e.target.value = '';
  } catch (err) {
    alert("Error importing recipes: " + err.message);
    e.target.value = '';
  }
});

document.getElementById("btnBackRecipe").addEventListener("click", () => {
  showView("viewRecipes");
  renderRecipes();
});

function openEditRecipeModal(recipe) {
  openModal("Edit recipe", "", `
    <div class="modal__input-row">
      <label>Recipe name</label>
      <input id="modalEditRecipeName" type="text" value="${esc(recipe.name)}" autofocus />
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Save", cls: "btn--primary", fn: async () => {
      const name = document.getElementById("modalEditRecipeName").value.trim();
      if (!name) return;
      await api("PUT", `/recipes/${recipe.id}`, { name });
      recipe.name = name;
      closeModal();
      renderRecipes();
    }}
  ]);
  setTimeout(() => document.getElementById("modalEditRecipeName").focus(), 50);
}

function openDeleteRecipeModal(recipe) {
  openModal("Delete recipe", `Are you sure you want to delete "${esc(recipe.name)}"? This can't be undone.`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Delete", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/recipes/${recipe.id}`);
      recipes = recipes.filter(r => r.id !== recipe.id);
      closeModal();
      if (currentRecipe && currentRecipe.id === recipe.id) {
        showView("viewRecipes");
      }
      renderRecipes();
    }}
  ]);
}

function openEditIngredientModal(ingredient) {
  openModal("Edit ingredient", "", `
    <div class="modal__input-row">
      <label>Ingredient name</label>
      <input id="modalIngName" type="text" value="${esc(ingredient.name)}" autofocus />
    </div>
    <div class="modal__input-row">
      <label>Quantity</label>
      <input id="modalIngQty" type="text" value="${esc(ingredient.quantity || "")}" />
    </div>
    <div class="modal__input-row">
      <label>Unit</label>
      <input id="modalIngUnit" type="text" value="${esc(ingredient.unit || "")}" placeholder="e.g. cups, tbsp" />
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Save", cls: "btn--primary", fn: async () => {
      const name = document.getElementById("modalIngName").value.trim();
      if (!name) return;
      const updates = {
        name,
        quantity: document.getElementById("modalIngQty").value.trim(),
        unit: document.getElementById("modalIngUnit").value.trim()
      };
      await api("PUT", `/recipes/${currentRecipe.id}/ingredients/${ingredient.id}`, updates);
      Object.assign(ingredient, updates);
      closeModal();
      renderIngredients();
    }}
  ]);
  setTimeout(() => document.getElementById("modalIngName").focus(), 50);
}

function openDeleteIngredientModal(ingredient) {
  openModal("Delete ingredient", `Remove "${esc(ingredient.name)}" from this recipe?`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Delete", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/recipes/${currentRecipe.id}/ingredients/${ingredient.id}`);
      recipeIngredients = recipeIngredients.filter(i => i.id !== ingredient.id);
      closeModal();
      renderIngredients();
    }}
  ]);
}

function openEditStepModal(step) {
  openModal("Edit step", "", `
    <div class="modal__input-row">
      <label>Instruction</label>
      <textarea id="modalStepInstruction" rows="3" autofocus>${esc(step.instruction)}</textarea>
    </div>`,
  [
    { label: "Cancel", fn: closeModal },
    { label: "Save", cls: "btn--primary", fn: async () => {
      const instruction = document.getElementById("modalStepInstruction").value.trim();
      if (!instruction) return;
      await api("PUT", `/recipes/${currentRecipe.id}/steps/${step.id}`, { instruction });
      step.instruction = instruction;
      closeModal();
      renderSteps();
    }}
  ]);
  setTimeout(() => document.getElementById("modalStepInstruction").focus(), 50);
}

function openDeleteStepModal(step) {
  openModal("Delete step", `Remove step ${step.step_number} from this recipe?`, "",
  [
    { label: "Cancel", fn: closeModal },
    { label: "Delete", cls: "btn--primary", fn: async () => {
      await api("DELETE", `/recipes/${currentRecipe.id}/steps/${step.id}`);
      recipeSteps = recipeSteps.filter(s => s.id !== step.id);
      // Renumber remaining steps
      recipeSteps.forEach((s, i) => s.step_number = i + 1);
      closeModal();
      renderSteps();
    }}
  ]);
}

// ─── INIT ───
loadLists();
updateTopbarNav("viewLists");