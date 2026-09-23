requireLogin();

// ---------- Helpers ----------
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const fmtDateTime = (d) =>
  new Date(d).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });

const fmtDate = (d) => new Date(d).toLocaleDateString("en-US", { dateStyle: "medium" });

// ---------- Sidebar navigation (admin dashboard) ----------
function showSection(name) {
  const panels = document.querySelectorAll(".panel");
  if (!panels.length) return;
  const target = document.getElementById("sec-" + name) ? name : "documents";

  panels.forEach((p) => p.classList.toggle("active", p.id === "sec-" + target));
  document.querySelectorAll(".sb-nav a").forEach((a) =>
    a.classList.toggle("active", a.dataset.target === target)
  );

  // refresh data each time a section is opened
  if (target === "documents") loadDocs();
  if (target === "users") loadUsers();
  if (target === "feedback") loadFeedback();
  if (target === "chat") {
    const q = document.getElementById("question");
    if (q) q.focus();
  }
}

// ---------- Documents ----------
async function uploadDoc() {
  const fileInput = document.getElementById("file");
  const tag = document.getElementById("tag") ? document.getElementById("tag").value : "";
  const msg = document.getElementById("uploadMsg");
  if (!fileInput || !fileInput.files.length) {
    msg.innerText = "Please choose a file first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("tag", tag);

  msg.innerText = "Uploading and indexing... (the first upload can take a minute while the model downloads)";
  try {
    const res = await apiUpload("/admin/documents", formData);
    msg.innerText = `Done: ${res.chunks_indexed} chunks indexed.`;
    fileInput.value = "";
    loadDocs();
  } catch (e) {
    msg.innerText = "Error: " + (e.detail || "upload failed");
  }
}

async function loadDocs() {
  const body = document.getElementById("docsBody");
  if (!body) return;
  try {
    const docs = await apiGet("/admin/documents");
    if (!docs.length) {
      body.innerHTML = `<tr><td class="empty" colspan="5">No documents yet. Upload one above.</td></tr>`;
      return;
    }
    body.innerHTML = docs
      .map(
        (d) => `
      <tr>
        <td>${esc(d.filename)}</td>
        <td><span class="tag">${esc(d.type)}</span></td>
        <td>${esc(d.tag || "-")}</td>
        <td>${fmtDateTime(d.uploaded_at)}</td>
        <td><button class="danger" onclick="deleteDoc('${esc(d.id)}')">Delete</button></td>
      </tr>`
      )
      .join("");
  } catch (e) {
    body.innerHTML = `<tr><td class="empty" colspan="5">Could not load documents: ${esc(e.detail || "error")}</td></tr>`;
  }
}

async function deleteDoc(id) {
  if (!confirm("Delete this document and its indexed content?")) return;
  const res = await fetch(`${API_BASE}/admin/documents/${id}`, { method: "DELETE", headers: authHeaders() });
  if (!res.ok) alert("Could not delete the document.");
  loadDocs();
}

// ---------- Users ----------
async function createUser() {
  const nameEl = document.getElementById("fullName");
  const emailEl = document.getElementById("email");
  const msg = document.getElementById("createMsg");
  const full_name = nameEl.value.trim();
  const email = emailEl.value.trim();
  if (!full_name || !email) {
    msg.innerText = "Please enter a name and an email.";
    return;
  }
  try {
    await apiSend("/admin/users", "POST", { full_name, email });
    msg.innerText =
      "Account created. A temporary password was emailed (or printed in the server console if SMTP is not configured).";
    nameEl.value = "";
    emailEl.value = "";
    loadUsers();
  } catch (e) {
    msg.innerText = "Error: " + (typeof e.detail === "string" ? e.detail : "could not create the account");
  }
}

async function loadUsers() {
  const body = document.getElementById("usersBody");
  if (!body) return;
  try {
    const users = await apiGet("/admin/users");
    if (!users.length) {
      body.innerHTML = `<tr><td class="empty" colspan="3">No users yet.</td></tr>`;
      return;
    }
    body.innerHTML = users
      .map(
        (u) => `
      <tr><td>${esc(u.full_name)}</td><td>${esc(u.email)}</td><td>${u.is_active ? "Active" : "Suspended"}</td></tr>`
      )
      .join("");
  } catch (e) {
    body.innerHTML = `<tr><td class="empty" colspan="3">Could not load users: ${esc(e.detail || "error")}</td></tr>`;
  }
}

// ---------- Feedback ----------
async function loadFeedback() {
  const body = document.getElementById("feedbackBody");
  const statsBox = document.getElementById("statsBox");
  if (!body) return;
  try {
    const stats = await apiGet("/feedback/stats");
    statsBox.innerText = stats.total_ratings
      ? `Average rating: ${stats.average_score} / 5 (${stats.total_ratings} ratings)`
      : "No ratings yet.";

    const items = await apiGet("/feedback");
    if (!items.length) {
      body.innerHTML = `<tr><td class="empty" colspan="4">No feedback yet. Ratings from the chatbot will appear here.</td></tr>`;
      return;
    }
    body.innerHTML = items
      .map(
        (f) => `
      <tr>
        <td>${"⭐".repeat(f.score)}</td>
        <td>${esc(f.comment || "-")}</td>
        <td>${f.reviewed ? "Reviewed" : "Pending review"}</td>
        <td>${f.reviewed ? "" : `<button class="primary" style="margin-top:0" onclick="markReviewed('${esc(f.id)}')">Mark reviewed</button>`}</td>
      </tr>`
      )
      .join("");
  } catch (e) {
    statsBox.innerText = "Could not load feedback: " + (e.detail || "error");
  }
}

async function markReviewed(id) {
  await fetch(`${API_BASE}/feedback/${id}/mark-reviewed`, { method: "PUT", headers: authHeaders() });
  loadFeedback();
}

// ---------- Super-admin page ----------
async function createOrg() {
  const nameEl = document.getElementById("orgName");
  const name = nameEl.value.trim();
  const msg = document.getElementById("orgMsg");
  if (!name) {
    msg.innerText = "Please enter an organization name.";
    return;
  }
  try {
    await apiSend("/super-admin/organizations", "POST", { name });
    msg.innerText = "Organization created.";
    nameEl.value = "";
    loadOrgs();
  } catch (e) {
    msg.innerText = "Error: " + (typeof e.detail === "string" ? e.detail : "could not create the organization");
  }
}

async function loadOrgs() {
  const body = document.getElementById("orgsBody");
  const select = document.getElementById("orgSelect");
  if (!body && !select) return;
  try {
    const orgs = await apiGet("/super-admin/organizations");
    if (body) {
      body.innerHTML = orgs
        .map(
          (o) => `
        <tr><td>${esc(o.name)}</td><td>${o.is_active ? "Active" : "Suspended"}</td>
        <td>${fmtDate(o.created_at)}</td></tr>`
        )
        .join("");
    }
    if (select) {
      select.innerHTML = orgs.map((o) => `<option value="${esc(o.id)}">${esc(o.name)}</option>`).join("");
    }
  } catch (e) {
    if (body) body.innerHTML = `<tr><td colspan="3">Could not load organizations.</td></tr>`;
  }
}

async function createOrgAdmin() {
  const orgId = document.getElementById("orgSelect").value;
  const nameEl = document.getElementById("adminName");
  const emailEl = document.getElementById("adminEmail");
  const msg = document.getElementById("adminMsg");
  const full_name = nameEl.value.trim();
  const email = emailEl.value.trim();
  if (!orgId || !full_name || !email) {
    msg.innerText = "Please choose an organization and enter a name and an email.";
    return;
  }
  try {
    await apiSend(`/super-admin/organizations/${orgId}/admins`, "POST", { full_name, email });
    msg.innerText =
      "Admin account created. A temporary password was emailed (or printed in the server console if SMTP is not configured).";
    nameEl.value = "";
    emailEl.value = "";
  } catch (e) {
    msg.innerText = "Error: " + (typeof e.detail === "string" ? e.detail : "could not create the admin");
  }
}

// ---------- Auto-init ----------
document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector(".sidebar")) {
    const who = document.getElementById("who");
    if (who) who.innerText = (localStorage.getItem("kh_name") || "Admin") + " · Organization admin";
    showSection(location.hash.slice(1));
    window.addEventListener("hashchange", () => showSection(location.hash.slice(1)));
  } else {
    loadOrgs();
  }
});
