// ---------------------------------------------------------------
// Voice Command Shopping Assistant -- frontend
// Uses the browser's built-in Web Speech API for recognition (free,
// no API key, works in Chrome/Edge). Falls back gracefully to the
// text input if the browser doesn't support it.
// ---------------------------------------------------------------

const micBtn = document.getElementById("mic-btn");
const micStatus = document.getElementById("mic-status");
const transcriptEl = document.getElementById("transcript");
const feedbackEl = document.getElementById("feedback");
const langSelect = document.getElementById("lang-select");
const listBody = document.getElementById("list-body");
const suggestionsEl = document.getElementById("suggestions");
const typeForm = document.getElementById("type-form");
const typeInput = document.getElementById("type-input");
const searchModal = document.getElementById("search-modal");
const searchResults = document.getElementById("search-results");
const searchTitle = document.getElementById("search-title");
const searchClose = document.getElementById("search-close");

document.getElementById("receipt-date").textContent =
  new Date().toLocaleDateString(undefined, { weekday: "short", year: "numeric", month: "short", day: "numeric" });

// ---------------------------------------------------------------
// Speech recognition setup
// ---------------------------------------------------------------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
let listening = false;

if (SpeechRecognition) {
  recognizer = new SpeechRecognition();
  recognizer.continuous = false;
  recognizer.interimResults = true;
  recognizer.maxAlternatives = 1;

  recognizer.onstart = () => setListening(true);
  recognizer.onend = () => setListening(false);
  recognizer.onerror = (e) => {
    setListening(false);
    showFeedback(`Mic error: ${e.error}. You can type instead.`, true);
  };
  recognizer.onresult = (event) => {
    let finalText = "";
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += chunk;
      else interim += chunk;
    }
    transcriptEl.textContent = finalText || interim || "…";
    if (finalText.trim()) {
      dispatchCommand(finalText.trim());
    }
  };
} else {
  micStatus.textContent = "Voice not supported here — type below";
  micBtn.disabled = true;
  micBtn.style.opacity = 0.4;
}

function setListening(isListening) {
  listening = isListening;
  micBtn.classList.toggle("listening", isListening);
  micStatus.textContent = isListening ? "Listening…" : "Tap to speak";
}

micBtn.addEventListener("click", () => {
  if (!recognizer) return;
  if (listening) {
    recognizer.stop();
    return;
  }
  recognizer.lang = langSelect.value;
  transcriptEl.textContent = "…";
  feedbackEl.textContent = "";
  try {
    recognizer.start();
  } catch (e) {
    // start() throws if called twice in a row too quickly
  }
});

// ---------------------------------------------------------------
// Text fallback
// ---------------------------------------------------------------
typeForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = typeInput.value.trim();
  if (!text) return;
  transcriptEl.textContent = text;
  dispatchCommand(text);
  typeInput.value = "";
});

// ---------------------------------------------------------------
// Command dispatch + rendering
// ---------------------------------------------------------------
async function dispatchCommand(text) {
  showFeedback("Working on it…");
  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    if (data.action === "search") {
      openSearchModal(data);
      showFeedback(data.message);
    } else if (data.action === "unknown") {
      showFeedback(data.message, true);
    } else {
      showFeedback(data.message);
      if (data.substitutes && data.substitutes.length) {
        showFeedback(`${data.message} · substitutes: ${data.substitutes.join(", ")}`);
      }
    }

    if (data.list) renderList(data.list);
    loadSuggestions();
  } catch (err) {
    showFeedback("Couldn't reach the server. Is it running?", true);
  }
}

function showFeedback(msg, isError = false) {
  feedbackEl.textContent = msg;
  feedbackEl.classList.toggle("error", isError);
}

function renderList(items) {
  if (!items.length) {
    listBody.innerHTML = `<p class="empty-state">Your list is empty. Say “add milk” to start.</p>`;
    return;
  }
  const groups = {};
  for (const item of items) {
    groups[item.category] = groups[item.category] || [];
    groups[item.category].push(item);
  }
  listBody.innerHTML = Object.entries(groups).map(([category, group]) => `
    <div class="category-group">
      <div class="category-name">${category}</div>
      ${group.map(itemRowHtml).join("")}
    </div>
  `).join("");

  listBody.querySelectorAll(".remove-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      await fetch(`/api/item/${id}`, { method: "DELETE" });
      refreshList();
      loadSuggestions();
    });
  });
}

function itemRowHtml(item) {
  const qtyLabel = item.unit ? `${item.quantity} ${item.unit}` : `x${item.quantity}`;
  return `
    <div class="line-item">
      <span class="name">${escapeHtml(item.name)}</span>
      <span class="qty">${qtyLabel}</span>
      <button class="remove-btn" data-id="${item.id}" aria-label="Remove ${escapeHtml(item.name)}">×</button>
    </div>
  `;
}

async function refreshList() {
  const res = await fetch("/api/list");
  const items = await res.json();
  renderList(items);
}

async function loadSuggestions() {
  const res = await fetch("/api/suggestions");
  const data = await res.json();
  const blocks = [];

  if (data.frequent && data.frequent.length) {
    blocks.push(suggBlockHtml("You usually buy", data.frequent.map(f => f.name)));
  }
  if (data.seasonal && data.seasonal.length) {
    blocks.push(suggBlockHtml("In season", data.seasonal));
  }
  suggestionsEl.innerHTML = blocks.join("");

  suggestionsEl.querySelectorAll(".chip button").forEach((btn) => {
    btn.addEventListener("click", () => dispatchCommand(`add ${btn.dataset.item}`));
  });
}

function suggBlockHtml(title, names) {
  return `
    <div class="sugg-block">
      <div class="sugg-title">${title}</div>
      <div class="sugg-chips">
        ${names.map(n => `<span class="chip">${escapeHtml(n)}<button data-item="${escapeHtml(n)}">+</button></span>`).join("")}
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------------------------------------------------------
// Search modal
// ---------------------------------------------------------------
function openSearchModal(data) {
  searchTitle.textContent = `Results for “${data.item}”`;
  if (!data.results.length) {
    searchResults.innerHTML = `<p class="empty-state">No matches. Try a different item or brand.</p>`;
  } else {
    searchResults.innerHTML = data.results.map(p => `
      <div class="search-result">
        <div>
          <div>${escapeHtml(p.name)} <span class="meta">· ${escapeHtml(p.brand)} · ${escapeHtml(p.size)}</span></div>
        </div>
        <div class="price">$${p.price.toFixed(2)}</div>
      </div>
    `).join("");
  }
  searchModal.classList.remove("hidden");
}
searchClose.addEventListener("click", () => searchModal.classList.add("hidden"));
searchModal.addEventListener("click", (e) => {
  if (e.target === searchModal) searchModal.classList.add("hidden");
});

// ---------------------------------------------------------------
// Initial load
// ---------------------------------------------------------------
refreshList();
loadSuggestions();
