document.addEventListener("DOMContentLoaded", () => {
  const tb = document.getElementById("tbChamados");
  const paginator = document.getElementById("paginator");
  const metaInfo = document.getElementById("metaInfo");
  const f_q = document.getElementById("f_q");
  const f_prioridade = document.getElementById("f_prioridade");
  const f_status = document.getElementById("f_status");
  const f_perpage = document.getElementById("f_perpage");
  const btnFiltrar = document.getElementById("btn_filtrar");
  const btnLimpar = document.getElementById("btn_limpar");
  const exportCsv = document.getElementById("exportCsv");

  const modalElement = document.getElementById("modalChamado");
  const modal = new bootstrap.Modal(modalElement);
  const formEdit = document.getElementById("formChamadoEdit");

  let currentPage = 1;

  const params = () => {
    const p = new URLSearchParams();
    if (f_q.value.trim()) p.set("q", f_q.value.trim());
    if (f_prioridade.value) p.set("prioridade", f_prioridade.value);
    if (f_status.value) p.set("status", f_status.value);
    p.set("page", currentPage);
    p.set("per_page", f_perpage.value || 25);
    return p.toString();
  };

  const load = async () => {
    tb.innerHTML = `<tr><td colspan="7" class="text-center py-5"><div class="spinner-border text-primary"></div></td></tr>`;
    try {
      const res = await fetch(`/api/chamados?${params()}`, { credentials: "include" });
      if (res.status === 401) return location.href = "/login";
      const data = await res.json();
      renderTable(data.items || []);
      renderPaginator(data.meta || {});
      metaInfo.textContent = `Mostrando ${data.items?.length || 0} de ${data.meta?.total || 0} chamados`;
    } catch (e) {
      tb.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-5">Erro ao carregar dados</td></tr>`;
    }
  };

  const renderTable = (items) => {
    if (!items.length) {
      tb.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted">Nenhum chamado encontrado</td></tr>`;
      return;
    }

    tb.innerHTML = items.map(c => `
      <tr>
        <td class="text-center fw-bold text-primary">#${c.id}</td>
        <td class="fw-medium">${escape(c.titulo)}</td>
        <td class="text-center"><span class="badge badge-status ${priorityClass(c.prioridade)}">${c.prioridade}</span></td>
        <td class="text-center"><span class="badge bg-secondary-subtle text-secondary">${c.status}</span></td>
        <td><small class="text-muted">${escape(c.autor || "—")}</small></td>
        <td><small class="text-muted">${new Date(c.data_iso || c.data).toLocaleDateString("pt-BR")}</small></td>
        <td class="text-center">
          <button class="btn btn-sm btn-outline-primary btn-view" data-id="${c.id}">Ver</button>
        </td>
      </tr>
    `).join("");

    document.querySelectorAll(".btn-view").forEach(b => b.onclick = () => openModal(b.dataset.id));
  };

  const priorityClass = (p) => ({
    "CRÍTICA": "bg-danger text-white",
    "ALTA": "bg-warning text-dark",
    "MÉDIA": "bg-info text-dark",
    "BAIXA": "bg-success text-white"
  }[p] || "bg-secondary text-white");

  const escape = (s) => s ? String(s).replace(/[&<>"']/g, c => "&#" + c.charCodeAt(0) + ";") : "";

  const renderPaginator = (meta) => {
    paginator.innerHTML = "";
    if (!meta || meta.total_pages <= 1) return;

    const btn = (text, page, disabled = false) => {
      const b = document.createElement("button");
      b.className = `btn btn-sm ${disabled ? "btn-secondary" : "btn-outline-secondary"}`;
      b.textContent = text;
      b.disabled = disabled;
      b.onclick = () => { currentPage = page; load(); };
      return b;
    };

    paginator.append(btn("Primeira", 1, meta.page === 1));
    paginator.append(btn("Anterior", meta.page - 1, meta.page === 1));
    paginator.append(Object.assign(document.createElement("span"), {
      className: "px-3 py-1 text-muted",
      textContent: `Página ${meta.page} de ${meta.total_pages}`
    }));
    paginator.append(btn("Próxima", meta.page + 1, meta.page === meta.total_pages));
    paginator.append(btn("Última", meta.total_pages, meta.page === meta.total_pages));
  };

  // ===== ABRE O MODAL E PREENCHE OS CAMPOS =====
  const openModal = async (id) => {
    try {
      const res = await fetch(`/api/chamados/${id}`, { credentials: "include" });
      if (!res.ok) throw new Error("Chamado não encontrado");

      const c = await res.json();

      document.getElementById("modalId").textContent = `#${c.id}`;
      document.getElementById("edit_id").value = c.id;
      document.getElementById("edit_titulo").value = c.titulo || "";
      document.getElementById("edit_descricao").value = c.descricao || "";
      document.getElementById("edit_prioridade").value = c.prioridade || "MÉDIA";
      document.getElementById("edit_status").value = c.status || "ABERTO";

      modal.show();
    } catch (e) {
      alert("Erro ao carregar chamado: " + e.message);
    }
  };

  // ===== SALVAR EDIÇÃO =====
  formEdit.onsubmit = async (e) => {
    e.preventDefault();
    const id = document.getElementById("edit_id").value;
    const payload = {
      titulo: document.getElementById("edit_titulo").value.trim(),
      descricao: document.getElementById("edit_descricao").value.trim(),
      prioridade: document.getElementById("edit_prioridade").value,
      status: document.getElementById("edit_status").value
    };

    try {
      const res = await fetch(`/api/chamados/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw await res.json();
      modal.hide();
      load();
    } catch (err) {
      alert(err.erro || "Erro ao salvar");
    }
  };

  // ===== BOTÃO REMOVER — AGORA FUNCIONA 100% =====
  document.getElementById("btnDelete").addEventListener("click", async () => {
    const id = document.getElementById("edit_id").value;
    if (!id) return;

    if (!confirm("⚠️ Tem certeza que deseja REMOVER este chamado?\nEsta ação NÃO pode ser desfeita.")) {
      return;
    }

    try {
      const res = await fetch(`/api/chamados/${id}`, {
        method: "DELETE",
        credentials: "include"
      });

      if (!res.ok) {
        const erro = await res.text();
        throw new Error(erro || "Erro ao remover");
      }

      modal.hide();
      load();
      alert("Chamado removido com sucesso!");
    } catch (e) {
      console.error(e);
      alert("Erro ao remover chamado: " + e.message);
    }
  });

  // ===== FILTROS E EXPORTAR =====
  btnFiltrar.onclick = () => { currentPage = 1; load(); };
  btnLimpar.onclick = () => {
    f_q.value = f_prioridade.value = f_status.value = "";
    currentPage = 1;
    load();
  };

  exportCsv.onclick = () => {
    window.open(`/api/chamados/export?format=csv&${params()}`, "_blank");
  };

  // ===== INICIAR =====
  load();
});