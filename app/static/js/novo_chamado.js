document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formChamado");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const dados = {
      titulo: document.getElementById("titulo").value.trim(),
      descricao: document.getElementById("descricao").value.trim(),
      prioridade: document.getElementById("prioridade").value,
      data: document.getElementById("data").value
    };
    if (!dados.titulo) return alert("Título é obrigatório");

    try {
      const res = await fetch("/api/chamados/novo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(dados)
      });
      if (!res.ok) {
        const err = await res.json();
        return alert(err.erro || "Erro ao abrir chamado");
      }
      const body = await res.json();
      alert("Chamado criado: #" + (body.id || ""));
      window.location.href = "/chamados";
    } catch (e) {
      console.error(e);
      alert("Erro de conexão");
    }
  });
});
