document.addEventListener("DOMContentLoaded", () => {
  carregarTudo();
});

let chamados = [];
let chartPrioridade = null;
let chartStatus = null;

async function carregarTudo() {
  await Promise.all([
    carregarStats(),
    carregarChamados(),
    carregarPowerAutomate()
  ]);
  setupFiltros();
}

async function carregarStats() {
  try {
    const res = await fetch("/api/stats", { credentials: "include" });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("total").textContent = data.total || 0;
    document.getElementById("abertos").textContent = data.abertos || 0;
    document.getElementById("alta").textContent = data.alta || 0;
    document.getElementById("hoje").textContent = data.hoje || 0;
  } catch (e) { console.error(e); }
}

async function carregarChamados() {
  try {
    const res = await fetch("/api/chamados?per_page=500", { credentials: "include" });
    if (!res.ok) return;
    const payload = await res.json();
    chamados = payload.all_items || payload.items || [];
    atualizarGraficos();
    filtrar("ALL");
  } catch (e) { console.error(e); }
}

function atualizarGraficos() {
  // Prioridade (ordem correta: Baixa → Crítica)
  const ordemPrioridade = ["BAIXA", "MÉDIA", "ALTA", "CRÍTICA"];
  const coresPrioridade = ["#28a745", "#ffc107", "#fd7e14", "#dc3545"];
  const dadosP = ordemPrioridade.map(p => chamados.filter(c => c.prioridade === p).length);

  const ctxP = document.getElementById("chartPrioridade");
  if (chartPrioridade) chartPrioridade.destroy();
  chartPrioridade = new Chart(ctxP, {
    type: "doughnut",
    data: {
      labels: ordemPrioridade,
      datasets: [{
        data: dadosP,
        backgroundColor: coresPrioridade,
        borderWidth: 3,
        borderColor: "#fff"
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } }
    }
  });

  // Status
  const statusOrdem = ["ABERTO", "EM ANDAMENTO", "PENDENTE", "RESOLVIDO"];
  const coresStatus = ["#0d6efd", "#0dcaf0", "#ffc107", "#198754"];
  const dadosS = statusOrdem.map(s => chamados.filter(c => c.status === s).length);

  const ctxS = document.getElementById("chartStatus");
  if (chartStatus) chartStatus.destroy();
  chartStatus = new Chart(ctxS, {
    type: "bar",
    data: {
      labels: ["Aberto", "Andamento", "Pendente", "Resolvido"],
      datasets: [{
        data: dadosS,
        backgroundColor: coresStatus,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, grid: { display: false } } }
    }
  });
}

function filtrar(tipo) {
  const tbody = document.getElementById("tbChamados");
  const vazio = document.getElementById("emptyTable");
  let filtrados = chamados;

  if (tipo === "ABERTOS") filtrados = chamados.filter(c => c.status === "ABERTO");
  else if (tipo === "ALTA_CRIT") filtrados = chamados.filter(c => ["ALTA", "CRÍTICA"].includes(c.prioridade));
  else if (tipo === "HOJE") {
    const hoje = new Date().toISOString().split("T")[0];
    filtrados = chamados.filter(c => c.data_iso.startsWith(hoje));
  }

  tbody.innerHTML = "";
  if (filtrados.length === 0) {
    vazio.classList.remove("d-none");
    return;
  }
  vazio.classList.add("d-none");

  const fragment = document.createDocumentFragment();
  filtrados.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="text-center fw-medium text-muted small">${c.id}</td>
      <td class="fw-medium">${c.titulo}</td>
      <td class="text-center">
        <span class="badge ${getStatusClass(c.status)} badge-status">${formatStatus(c.status)}</span>
      </td>
      <td class="text-center">
        <span class="badge ${getPrioridadeClass(c.prioridade)} badge-status">${c.prioridade}</span>
      </td>
      <td class="text-center text-muted small">${formatarData(c.data_iso)}</td>
    `;
    fragment.appendChild(tr);
  });
  tbody.appendChild(fragment);
}

function getStatusClass(status) {
  const classes = {
    "ABERTO": "bg-primary",
    "EM ANDAMENTO": "bg-info text-dark",
    "PENDENTE": "bg-warning text-dark",
    "RESOLVIDO": "bg-success"
  };
  return classes[status] || "bg-secondary";
}

function getPrioridadeClass(prio) {
  const classes = {
    "BAIXA": "bg-success",
    "MÉDIA": "bg-warning text-dark",
    "ALTA": "bg-orange text-white",
    "CRÍTICA": "bg-danger"
  };
  return classes[prio] || "bg-secondary";
}

function formatStatus(s) {
  return s === "EM ANDAMENTO" ? "Em Andamento" : s.charAt(0) + s.slice(1).toLowerCase();
}

function formatarData(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR");
}

function setupFiltros() {
  document.querySelectorAll(".card-stat").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".card-stat").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      filtrar(card.dataset.filter);
    });
  });
}

// Power Automate (com fallback)
async function carregarPowerAutomate() {
  const lista = document.getElementById("listaRegras");
  try {
    const res = await fetch("/api/powerautomate", { credentials: "include" });
    const regras = res.ok ? await res.json() : null;

    renderRegras(regras || [
      { nome: "Notificar Analista", ativa: true },
      { nome: "Fechar Chamados Inativos", ativa: true },
      { nome: "Escalonar Críticos", ativa: false }
    ]);
  } catch {
    renderRegras([
      { nome: "Notificar Analista", ativa: true },
      { nome: "Fechar Chamados Inativos", ativa: true },
      { nome: "Escalonar Críticos", ativa: false }
    ]);
  }

  function renderRegras(regras) {
    lista.innerHTML = regras.map(r => `
      <li class="list-group-item d-flex justify-content-between align-items-center py-3">
        <span class="fw-medium">${r.nome}</span>
        <span class="badge rounded-pill ${r.ativa ? 'bg-success' : 'bg-secondary'}">
          ${r.ativa ? 'Ativa' : 'Inativa'}
        </span>
      </li>
    `).join("");
  }
}