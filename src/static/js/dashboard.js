let pieVoto, barEstrato, barIdeo, lineVol, flowScenario;
let injectedShocks = {}; // {t: {D_add:3}}

function qs(id){ return document.getElementById(id); }

function setStatus(msg){ qs("status").textContent = msg; }

function renderTable(rows){
  const tb = qs("sensTable").querySelector("tbody");
  tb.innerHTML = "";
  rows.forEach(r=>{
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="p-2 border">${r.estrato}</td>
      <td class="p-2 border">${r.factor}</td>
      <td class="p-2 border">${(+r.coef).toFixed(3)}</td>
    `;
    tb.appendChild(tr);
  });
}

function buildChart(canvasId, type, labels, datasets){
  const ctx = document.getElementById(canvasId);
  return new Chart(ctx, { type, data: { labels, datasets }, options: { responsive: true } });
}

async function loadDescriptivo(){
  const res = await fetch("/api/calibrate");
  const data = await res.json();

  // Pie voto
  const init = data.init_dist || {};
  const labels = Object.keys(init);
  const values = Object.values(init);

  if (pieVoto) pieVoto.destroy();
  pieVoto = buildChart("pieVoto", "pie", labels, [{ label: "Voto", data: values }]);

  // Barras estrato: % A y % B (si hay)
  const be = data.by_estrato || {};
  const estLabels = Object.keys(be);
  const A = estLabels.map(e => (be[e]["A"] || 0));
  const B = estLabels.map(e => (be[e]["B"] || 0));
  if (barEstrato) barEstrato.destroy();
  barEstrato = buildChart("barEstrato","bar", estLabels, [
    { label: "Tuto (A)", data: A },
    { label: "Paz (B)", data: B }
  ]);

  // Barras ideología
  const bi = data.by_ideologia || {};
  const ideLabels = Object.keys(bi);
  const Ai = ideLabels.map(e => (bi[e]["A"] || 0));
  const Bi = ideLabels.map(e => (bi[e]["B"] || 0));
  if (barIdeo) barIdeo.destroy();
  barIdeo = buildChart("barIdeo","bar", ideLabels, [
    { label: "Tuto (A)", data: Ai },
    { label: "Paz (B)", data: Bi }
  ]);
}

async function loadSensitivity(){
  const res = await fetch("/api/sensitivity");
  const data = await res.json();
  renderTable(data.rows || []);
}

function updateShockList(){
  qs("shock_list").textContent = JSON.stringify(injectedShocks, null, 2);
}

async function runSim(){
  setStatus("Ejecutando Monte Carlo... (esto puede tardar)");
  const payload = {
    steps: +qs("steps").value,
    replicas: +qs("replicas").value,
    umbral: +qs("umbral").value,
    params: {
      p_crisis: +qs("p_crisis").value,
      lam_denuncias: +qs("lam_denuncias").value,
      mu_debate: +qs("mu_debate").value,
      sigma_debate: +qs("sigma_debate").value,
      phi_min: +qs("phi_min").value,
      phi_max: +qs("phi_max").value,
      alpha_min: +qs("alpha_min").value,
      alpha_max: +qs("alpha_max").value
    },
    injected_shocks: injectedShocks
  };

  const res = await fetch("/api/montecarlo", {
    method: "POST",
    headers: { "Content-Type":"application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  if (data.error){
    setStatus("Error: " + data.error);
    return;
  }

  // IC95 final
  qs("resA").textContent = (data.final.A.mean*100).toFixed(1) + "%";
  qs("icA").textContent = `IC95: ${(data.final.A.lo95*100).toFixed(1)}% – ${(data.final.A.hi95*100).toFixed(1)}%`;

  qs("resB").textContent = (data.final.B.mean*100).toFixed(1) + "%";
  qs("icB").textContent = `IC95: ${(data.final.B.lo95*100).toFixed(1)}% – ${(data.final.B.hi95*100).toFixed(1)}%`;

  // Serie (sample)
  const trace = data.sample_trace || [];
  const tLabels = trace.map((_,i)=>`t${i}`);
  const serieA = trace.map(p=>p.A || 0);
  const serieB = trace.map(p=>p.B || 0);
  const inde = trace.map(p=>p.Indeciso || 0);

  if (lineVol) lineVol.destroy();
  lineVol = buildChart("lineVol","line", tLabels, [
    { label:"Tuto (A)", data: serieA },
    { label:"Paz (B)", data: serieB },
    { label:"Indeciso", data: inde }
  ]);

  setStatus(`Listo. Réplicas guardadas para escenarios: ${data.replicas_stored}`);
}

async function loadScenario(replica){
  const res = await fetch(`/api/scenario/${replica}`);
  const data = await res.json();
  if (data.error){ setStatus("Error: " + data.error); return; }

  const debug = data.debug || [];
  const labels = debug.map(d=>`t${d.t}`);
  const ht = debug.map(d=>d.h_t || 0);

  if (flowScenario) flowScenario.destroy();
  flowScenario = buildChart("flowScenario","line", labels, [
    { label:"h(t) macro", data: ht }
  ]);

  setStatus(`Mostrando escenario de réplica ${replica}`);
}

document.addEventListener("DOMContentLoaded", async ()=>{
  await loadDescriptivo();
  await loadSensitivity();
  updateShockList();

  qs("btnAddShock").addEventListener("click", ()=>{
    const t = +qs("shock_t").value;
    const tipo = qs("shock_tipo").value;
    const val = +qs("shock_val").value;

    if (!injectedShocks[t]) injectedShocks[t] = {};

    if (tipo === "E") injectedShocks[t]["E"] = 1;
    else if (tipo === "D_add") injectedShocks[t]["D_add"] = Math.round(val);
    else if (tipo === "R_set") injectedShocks[t]["R_set"] = val;
    else if (tipo === "P_set") injectedShocks[t]["P_set"] = val;

    updateShockList();
  });

  qs("btnRun").addEventListener("click", runSim);
  qs("btnReplica").addEventListener("click", ()=>{
    loadScenario(+qs("replica_id").value);
  });
});
