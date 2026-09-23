const API_BASE = "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("kh_token");
  return token ? { Authorization: "Bearer " + token } : {};
}

async function apiGet(path) {
  const res = await fetch(API_BASE + path, { headers: authHeaders() });
  if (!res.ok) throw await res.json().catch(() => ({ detail: res.statusText }));
  return res.json();
}

async function apiSend(path, method, body) {
  const res = await fetch(API_BASE + path, {
    method,
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await res.json().catch(() => ({ detail: res.statusText }));
  return res.json();
}

async function apiUpload(path, formData) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) throw await res.json().catch(() => ({ detail: res.statusText }));
  return res.json();
}

function requireLogin() {
  if (!localStorage.getItem("kh_token")) window.location.href = "login.html";
}

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}
