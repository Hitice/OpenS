document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const alertEl = document.getElementById("loginAlert");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alertEl.classList.add("d-none");

    const email = document.getElementById("email").value.trim();
    const senha = document.getElementById("senha").value;

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, senha })
      });

      if (res.ok) {
        window.location.href = "/dashboard";
        return;
      }

      const data = await res.json();
      alertEl.textContent = data.erro || data.msg || "Erro no login";
      alertEl.classList.remove("d-none");
    } catch (err) {
      alertEl.textContent = "Erro de conexão";
      alertEl.classList.remove("d-none");
      console.error(err);
    }
  });
});
