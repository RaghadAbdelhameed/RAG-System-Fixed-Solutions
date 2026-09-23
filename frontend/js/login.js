async function doLogin() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const errBox = document.getElementById("err");
  errBox.textContent = "";

  try {
    const data = await apiSend("/auth/login", "POST", { email, password });
    localStorage.setItem("kh_token", data.access_token);
    localStorage.setItem("kh_role", data.role);
    localStorage.setItem("kh_name", data.full_name);
    localStorage.setItem("kh_org", data.organization_id || "");

    if (data.must_change_password) {
      window.location.href = "change_password.html";
      return;
    }
    if (data.role === "super_admin") window.location.href = "superadmin.html";
    else if (data.role === "org_admin") window.location.href = "admin.html";
    else window.location.href = "chat.html";
  } catch (e) {
    errBox.textContent = typeof e.detail === "string" ? e.detail : "Could not sign in. Check your email and password.";
  }
}
