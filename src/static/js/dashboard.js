let lineVol, flowScenario;
let injectedShocks = {}; // {t: {D_add:3}}
let autoSimEnabled = true; // Control para simulación automática
let simTimeout = null; // Para debouncing

function qs(id) { return document.getElementById(id); }

function setStatus(msg) { 
  const statusEl = qs("status");
  if (statusEl) statusEl.textContent = msg; 
}

function renderTable(rows) {
  const tb = qs("sensTable").querySelector("tbody");
  if (!tb) return;
  tb.innerHTML = "";
  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 transition-colors";
    tr.innerHTML = `
      <td class="p-3 border-b border-slate-100">${r.estrato}</td>
      <td class="p-3 border-b border-slate-100">${r.factor}</td>
      <td class="p-3 border-b border-slate-100">
        <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg font-mono text-xs">
          ${(+r.coef).toFixed(3)}
        </span>
      </td>
    `;
    tb.appendChild(tr);
  });
}

function updateShockListVisual() {
  const container = qs("shock_list_visual");
  if (!container) return;
  
  const entries = Object.entries(injectedShocks);
  if (entries.length === 0) {
    container.innerHTML = '<div class="text-xs text-slate-400 italic">Ninguno</div>';
    return;
  }

  container.innerHTML = entries.map(([t, shockObj]) => {
    const shockType = Object.keys(shockObj)[0];
    const shockVal = shockObj[shockType];
    
    let emoji = "⚡";
    let label = shockType;
    if (shockType === "D_add") { emoji = "📰"; label = "Corrupción"; }
    else if (shockType === "E") { emoji = "💸"; label = "Crisis"; }
    else if (shockType === "R_set") { emoji = "📱"; label = "Redes"; }
    else if (shockType === "P_set") { emoji = "🎤"; label = "Debate"; }
    
    return `
      <div class="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-lg p-2">
        <span class="text-xs">
          <span class="font-semibold">Sem ${t}:</span> ${emoji} ${label} 
          <span class="text-amber-700 font-mono">(${shockVal})</span>
        </span>
        <button onclick="removeShock(${t})" class="text-red-500 hover:text-red-700 text-xs">
          ✕
        </button>
      </div>
    `;
  }).join("");
}

function removeShock(t) {
  delete injectedShocks[t];
  updateShockListVisual();
  // Simulación automática al remover shock
  if (autoSimEnabled) {
    scheduleAutoSim();
  }
}

async function loadSensitivity() {
  try {
    const res = await fetch("/api/sensitivity");
    const data = await res.json();
    renderTable(data.rows || []);
  } catch (err) {
    console.error("Error loading sensitivity:", err);
  }
}

// Función para programar simulación automática con debounce
function scheduleAutoSim() {
  if (simTimeout) clearTimeout(simTimeout);
  
  setStatus("⏱️ Cambios detectados, simulando en 2 segundos...");
  
  simTimeout = setTimeout(() => {
    runSim(true); // true indica que es simulación automática
  }, 2000); // 2 segundos de delay
}

// Función para cancelar simulación programada
function cancelAutoSim() {
  if (simTimeout) {
    clearTimeout(simTimeout);
    simTimeout = null;
    setStatus("");
  }
}

async function runSim(isAuto = false) {
  if (!isAuto) {
    cancelAutoSim(); // Cancelar cualquier simulación programada si es manual
  }
  
  const statusPrefix = isAuto ? "🔄 Auto-simulación: " : "⏳ ";
  setStatus(statusPrefix + "Ejecutando Monte Carlo...");
  
  const payload = {
    steps: +qs("steps").value,
    replicas: +qs("replicas").value,
    umbral: +qs("umbral").value,
    params: {
      p_crisis: +qs("p_crisis").value,
      lam_denuncias: +qs("lam_denuncias").value,
      mu_debate: +qs("mu_debate").value,
      sigma_debate: +qs("sigma_debate").value,
      phi_min: +(qs("phi_min")?.value || 0.30),
      phi_max: +(qs("phi_max")?.value || 0.60),
      alpha_min: +(qs("alpha_min")?.value || 0.20),
      alpha_max: +(qs("alpha_max")?.value || 0.40)
    },
    injected_shocks: injectedShocks
  };

  try {
    const res = await fetch("/api/montecarlo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.error) {
      setStatus("❌ Error: " + data.error);
      return;
    }

    // Actualizar resultados finales
    qs("resA").textContent = (data.final.A.mean * 100).toFixed(1) + "%";
    qs("icA").textContent = `${(data.final.A.lo95 * 100).toFixed(1)}% — ${(data.final.A.hi95 * 100).toFixed(1)}%`;

    qs("resB").textContent = (data.final.B.mean * 100).toFixed(1) + "%";
    qs("icB").textContent = `${(data.final.B.lo95 * 100).toFixed(1)}% — ${(data.final.B.hi95 * 100).toFixed(1)}%`;

    // Gráfico de volatilidad
    const trace = data.sample_trace || [];
    const tLabels = trace.map((_, i) => `Semana ${i}`);
    const serieA = trace.map(p => (p.A || 0) * 100);
    const serieB = trace.map(p => (p.B || 0) * 100);
    const inde = trace.map(p => (p.Indeciso || 0) * 100);

    if (lineVol) lineVol.destroy();
    
    const ctxVol = document.getElementById("lineVol");
    lineVol = new Chart(ctxVol, {
      type: "line",
      data: {
        labels: tLabels,
        datasets: [
          {
            label: "Tuto (A)",
            data: serieA,
            borderColor: 'rgb(54, 162, 235)',
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            tension: 0.3,
            fill: false,
            borderWidth: 3,
            pointBackgroundColor: 'rgb(54, 162, 235)',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: "Paz (B)",
            data: serieB,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            tension: 0.3,
            fill: false,
            borderWidth: 3,
            pointBackgroundColor: 'rgb(255, 99, 132)',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: "Indeciso",
            data: inde,
            borderColor: 'rgb(255, 159, 64)',
            backgroundColor: 'rgba(255, 159, 64, 0.1)',
            tension: 0.3,
            fill: false,
            borderWidth: 3,
            pointBackgroundColor: 'rgb(255, 159, 64)',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top'
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }
    });

    setStatus(`✅ ${isAuto ? 'Auto-simulación' : 'Simulación'} completada - ${data.replicas_stored} réplicas`);
  } catch (err) {
    console.error("Error en simulación:", err);
    setStatus("❌ Error en la simulación");
  }
}

async function loadScenario(replica) {
  try {
    const res = await fetch(`/api/scenario/${replica}`);
    const data = await res.json();
    if (data.error) {
      setStatus("❌ " + data.error);
      return;
    }

    const debug = data.debug || [];
    const labels = debug.map(d => `Semana ${d.t}`);
    const ht = debug.map(d => d.h_t || 0);

    if (flowScenario) flowScenario.destroy();
    
    const ctxFlow = document.getElementById("flowScenario");
    flowScenario = new Chart(ctxFlow, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Factor macro h(t)",
          data: ht,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.4,
          fill: true,
          borderWidth: 3,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return 'h(t): ' + context.parsed.y.toFixed(3);
              }
            }
          }
        },
        scales: {
          y: {
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });

    setStatus(`📊 Mostrando escenario réplica ${replica}`);
  } catch (err) {
    console.error("Error cargando escenario:", err);
    setStatus("❌ Error al cargar escenario");
  }
}

// Event listeners
document.addEventListener("DOMContentLoaded", async () => {
  await loadSensitivity();
  updateShockListVisual();

  // Actualizar displays de sliders
  const updateSliderDisplay = (sliderId, displayId, formatter = (v) => v) => {
    const slider = qs(sliderId);
    const display = qs(displayId);
    if (slider && display) {
      slider.addEventListener("input", () => {
        display.textContent = formatter(slider.value);
      });
    }
  };

  updateSliderDisplay("steps", "steps_display");
  updateSliderDisplay("umbral", "umbral_display", (v) => parseFloat(v).toFixed(2));
  updateSliderDisplay("shock_t", "shock_t_display");
  updateSliderDisplay("shock_val", "shock_val_display", (v) => parseFloat(v).toFixed(1));
  updateSliderDisplay("replica_id", "replica_display");

  // Listeners para auto-simulación en cambios de parámetros
  const triggerAutoSim = () => {
    if (autoSimEnabled) scheduleAutoSim();
  };

  // Toggle de auto-simulación
  const autoSimToggle = qs("autoSimToggle");
  if (autoSimToggle) {
    autoSimToggle.addEventListener("change", () => {
      autoSimEnabled = autoSimToggle.checked;
      if (!autoSimEnabled) {
        cancelAutoSim();
        setStatus("⏸️ Auto-simulación desactivada");
      } else {
        setStatus("▶️ Auto-simulación activada");
      }
    });
  }

  // Sliders y inputs que disparan auto-simulación
  ['steps', 'replicas', 'umbral', 'p_crisis', 'lam_denuncias', 
   'mu_debate', 'sigma_debate', 'phi_min', 'phi_max', 'alpha_min', 'alpha_max'].forEach(id => {
    const el = qs(id);
    if (el) {
      el.addEventListener('input', triggerAutoSim);
      el.addEventListener('change', triggerAutoSim);
    }
  });

  // Botón agregar shock
  const btnAddShock = qs("btnAddShock");
  if (btnAddShock) {
    btnAddShock.addEventListener("click", () => {
      const t = +qs("shock_t").value;
      const tipo = qs("shock_tipo").value;
      const val = +qs("shock_val").value;

      if (!injectedShocks[t]) injectedShocks[t] = {};

      if (tipo === "E") injectedShocks[t]["E"] = 1;
      else if (tipo === "D_add") injectedShocks[t]["D_add"] = Math.round(val);
      else if (tipo === "R_set") injectedShocks[t]["R_set"] = val;
      else if (tipo === "P_set") injectedShocks[t]["P_set"] = val;

      updateShockListVisual();
      
      // Auto-simulación al agregar shock
      if (autoSimEnabled) {
        scheduleAutoSim();
      }
      
      // Feedback visual
      btnAddShock.textContent = "✓ Agregado";
      btnAddShock.classList.add("bg-green-50", "border-green-500", "text-green-700");
      setTimeout(() => {
        btnAddShock.textContent = "+ Agregar shock";
        btnAddShock.classList.remove("bg-green-50", "border-green-500", "text-green-700");
      }, 1000);
    });
  }

  // Botón ejecutar simulación
  const btnRun = qs("btnRun");
  if (btnRun) {
    btnRun.addEventListener("click", async () => {
      btnRun.disabled = true;
      btnRun.style.opacity = "0.6";
      await runSim();
      btnRun.disabled = false;
      btnRun.style.opacity = "1";
    });
  }

  // Botón ver réplica
  const btnReplica = qs("btnReplica");
  if (btnReplica) {
    btnReplica.addEventListener("click", () => {
      loadScenario(+qs("replica_id").value);
    });
  }
});