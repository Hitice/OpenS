async function logout() {
  try {
    await fetch("/logout", { method: "POST", credentials: "include" });
  } catch (e) {}
  window.location.href = "/";
}
