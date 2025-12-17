let lineVol, flowScenario;
let injectedShocks = {}; // {t: {D_add:3}}
let autoSimEnabled = true; // Control para simulación automática
let simTimeout = null; // Para debouncing

function qs(id) {
  return document.getElementById(id);
}

function setStatus(msg) {
  const statusEl = qs("status");
  if (statusEl) statusEl.textContent = msg;
}

function renderTable(rows) {
  const tb = qs("sensTable").querySelector("tbody");
  if (!tb) return;
  tb.innerHTML = "";
  rows.forEach((r) => {
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

  container.innerHTML = "";
  const times = Object.keys(injectedShocks).sort((a, b) => a - b);

  if (times.length === 0) {
    container.innerHTML =
      '<div class="text-center py-4 text-slate-400 text-xs italic">No hay eventos programados</div>';
    return;
  }

  times.forEach((t) => {
    const events = injectedShocks[t];
    events.forEach((ev, idx) => {
      // Estilos según polaridad
      const isNeg = ev.polarity < 0;
      const bgColor = isNeg ? "bg-red-50" : "bg-green-50";
      const borderColor = isNeg ? "border-red-200" : "border-green-200";
      const icon = isNeg ? "📉" : "📈";
      const targetLabel =
        ev.target === "A" ? "Tuto" : ev.target === "B" ? "Paz" : "Sistema";

      const div = document.createElement("div");
      div.className = `flex items-center justify-between ${bgColor} border ${borderColor} rounded-lg p-2 text-xs mb-1`;
      div.innerHTML = `
        <div class="flex-1">
          <div class="font-bold text-slate-700">Semana ${t}: ${icon} ${targetLabel}</div>
          <div class="text-slate-500 flex gap-2">
             <span>${ev.topic}</span>
             <span class="font-mono opacity-75">Int: ${ev.magnitude}</span>
          </div>
        </div>
        <button onclick="removeShock(${t}, ${idx})" class="ml-2 text-slate-400 hover:text-red-600 font-bold px-2">
          ✕
        </button>
      `;
      container.appendChild(div);
    });
  });
}

function removeShock(t, idx) {
  if (injectedShocks[t]) {
    injectedShocks[t].splice(idx, 1);
    if (injectedShocks[t].length === 0) delete injectedShocks[t];
  }
  updateShockListVisual();
  if (autoSimEnabled) scheduleAutoSim();
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
      phi_min: +(qs("phi_min")?.value || 0.3),
      phi_max: +(qs("phi_max")?.value || 0.6),
      alpha_min: +(qs("alpha_min")?.value || 0.2),
      alpha_max: +(qs("alpha_max")?.value || 0.4),
    },
    injected_shocks: injectedShocks,
  };

  try {
    const res = await fetch("/api/montecarlo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (data.error) {
      setStatus("❌ Error: " + data.error);
      return;
    }

    // Actualizar resultados finales
    qs("resA").textContent = (data.final.A.mean * 100).toFixed(1) + "%";
    qs("icA").textContent = `${(data.final.A.lo95 * 100).toFixed(1)}% — ${(
      data.final.A.hi95 * 100
    ).toFixed(1)}%`;

    qs("resB").textContent = (data.final.B.mean * 100).toFixed(1) + "%";
    qs("icB").textContent = `${(data.final.B.lo95 * 100).toFixed(1)}% — ${(
      data.final.B.hi95 * 100
    ).toFixed(1)}%`;

    // Gráfico de volatilidad
    const trace = data.sample_trace || [];
    const tLabels = trace.map((_, i) => `Semana ${i}`);
    const serieA = trace.map((p) => (p.A || 0) * 100);
    const serieB = trace.map((p) => (p.B || 0) * 100);
    const inde = trace.map((p) => (p.Indeciso || 0) * 100);

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
            borderColor: "rgb(54, 162, 235)",
            backgroundColor: "rgba(54, 162, 235, 0.1)",
            tension: 0.3,
            fill: false,
            borderWidth: 3,
            pointBackgroundColor: "rgb(54, 162, 235)",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: "Paz (B)",
            data: serieB,
            borderColor: "rgb(255, 99, 132)",
            backgroundColor: "rgba(255, 99, 132, 0.1)",
            tension: 0.3,
            fill: false,
            borderWidth: 3,
            pointBackgroundColor: "rgb(255, 99, 132)",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: "Indeciso",
            data: inde,
            borderColor: "rgb(255, 159, 64)",
            backgroundColor: "rgba(255, 159, 64, 0.1)",
            tension: 0.3,
            fill: false,
            borderWidth: 3,
            pointBackgroundColor: "rgb(255, 159, 64)",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
          tooltip: {
            mode: "index",
            intersect: false,
            callbacks: {
              label: function (context) {
                return (
                  context.dataset.label +
                  ": " +
                  context.parsed.y.toFixed(1) +
                  "%"
                );
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function (value) {
                return value + "%";
              },
            },
            grid: {
              color: "rgba(0, 0, 0, 0.05)",
            },
          },
          x: {
            grid: {
              display: false,
            },
          },
        },
        interaction: {
          mode: "nearest",
          axis: "x",
          intersect: false,
        },
      },
    });

    setStatus(
      `✅ ${isAuto ? "Auto-simulación" : "Simulación"} completada - ${
        data.replicas_stored
      } réplicas`
    );
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
    const labels = debug.map((d) => `Semana ${d.t}`);
    const ht = debug.map((d) => d.h_t || 0);

    if (flowScenario) flowScenario.destroy();

    const ctxFlow = document.getElementById("flowScenario");
    flowScenario = new Chart(ctxFlow, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Factor macro h(t)",
            data: ht,
            borderColor: "rgb(75, 192, 192)",
            backgroundColor: "rgba(75, 192, 192, 0.1)",
            tension: 0.4,
            fill: true,
            borderWidth: 3,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                return "h(t): " + context.parsed.y.toFixed(3);
              },
            },
          },
        },
        scales: {
          y: {
            grid: {
              color: "rgba(0, 0, 0, 0.05)",
            },
          },
          x: {
            grid: {
              display: false,
            },
          },
        },
      },
    });

    setStatus(`📊 Mostrando escenario réplica ${replica}`);
  } catch (err) {
    console.error("Error cargando escenario:", err);
    setStatus("❌ Error al cargar escenario");
  }
}

// Event listeners
document.addEventListener("DOMContentLoaded", async () => {
  const surveyToggle = qs("surveyToggle");
  const surveyStatusText = qs("surveyStatusText");

  if (surveyToggle) {
    surveyToggle.addEventListener("change", async () => {
      const isActive = surveyToggle.checked;

      // Feedback visual inmediato
      if (isActive) {
        surveyStatusText.textContent = "🟢 Habilitada";
        surveyStatusText.className = "text-sm font-semibold text-green-600";
      } else {
        surveyStatusText.textContent = "⚫ Deshabilitada";
        surveyStatusText.className = "text-sm font-semibold text-slate-500";
      }

      // Llamada a API
      try {
        const res = await fetch("/api/toggle-survey", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ active: isActive }),
        });
        const data = await res.json();
        if (!data.success) alert("Error al guardar estado");
      } catch (e) {
        console.error(e);
        alert("Error de conexión");
        // Revertir en caso de error
        surveyToggle.checked = !isActive;
      }
    });
  }
  // 1. Cargar datos iniciales
  await loadSensitivity();
  updateShockListVisual();

  // 2. Helper para vincular Sliders con sus Textos
  const linkSlider = (id, displayId, formatter = (v) => v) => {
    const el = qs(id);
    const disp = qs(displayId);
    if (el && disp) {
      el.addEventListener("input", () => {
        disp.textContent = formatter(el.value);
      });
    }
  };

  // 3. Vincular Sliders de Parámetros Generales
  linkSlider("steps", "steps_display");
  linkSlider("umbral", "umbral_display", (v) => parseFloat(v).toFixed(2));
  linkSlider("replica_id", "replica_display");

  // 4. Vincular Sliders del Generador de Eventos (NUEVO)
  // Slider de Semana (con formato "Sem X")
  const tSlider = qs("shock_t");
  const tDisplay = qs("shock_t_display");
  if (tSlider && tDisplay) {
    tSlider.addEventListener("input", (e) => {
      tDisplay.textContent = "Sem " + e.target.value;
    });
  }
  // Slider de Magnitud/Intensidad
  linkSlider("shock_mag", "shock_mag_display", (v) => parseFloat(v).toFixed(1));

  // 5. Lógica de Auto-Simulación
  const triggerAutoSim = () => {
    if (autoSimEnabled) scheduleAutoSim();
  };

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

  // Detectar cambios en inputs numéricos del motor
  [
    "steps",
    "replicas",
    "umbral",
    "p_crisis",
    "lam_denuncias",
    "mu_debate",
    "sigma_debate",
    "phi_min",
    "phi_max",
    "alpha_min",
    "alpha_max",
  ].forEach((id) => {
    const el = qs(id);
    if (el) {
      el.addEventListener("input", triggerAutoSim);
      el.addEventListener("change", triggerAutoSim);
    }
  });

  // 6. BOTÓN: AGREGAR SHOCK (LÓGICA PROFESIONAL ACTUALIZADA)
  const btnAddShock = qs("btnAddShock");
  if (btnAddShock) {
    btnAddShock.addEventListener("click", () => {
      // a) Obtener valores del NUEVO formulario HTML
      const t = parseInt(qs("shock_t").value);
      const target = qs("shock_target").value; // "A", "B", "SISTEMA"
      const topic = qs("shock_topic").value; // "economia", "corrupcion", etc.
      const polarity = parseFloat(qs("shock_polarity").value); // 1.0 o -1.0
      const magnitude = parseFloat(qs("shock_mag").value); // 0.1 a 1.0

      // b) Crear objeto de evento semántico
      const newEvent = {
        target: target,
        topic: topic,
        polarity: polarity,
        magnitude: magnitude,
      };

      // c) Inicializar array para esa semana si no existe
      if (!injectedShocks[t]) injectedShocks[t] = [];

      // d) Guardar en la lista
      injectedShocks[t].push(newEvent);

      // e) Actualizar vista y simular
      updateShockListVisual();
      if (autoSimEnabled) {
        scheduleAutoSim();
      }

      // f) Feedback visual (Botón verde momentáneo)
      const originalText = btnAddShock.textContent;
      btnAddShock.textContent = "✓ Evento Inyectado";
      btnAddShock.className =
        "w-full rounded-xl border-2 border-green-500 bg-green-50 text-green-700 font-bold py-2 transition-colors text-sm";

      setTimeout(() => {
        btnAddShock.textContent = originalText;
        btnAddShock.className =
          "w-full rounded-xl border-2 border-amber-500 text-amber-700 font-bold py-2 hover:bg-amber-50 transition-colors text-sm";
      }, 1000);
    });
  }

  // 7. Botón Ejecutar Simulación (Manual)
  const btnRun = qs("btnRun");
  if (btnRun) {
    btnRun.addEventListener("click", async () => {
      btnRun.disabled = true;
      btnRun.style.opacity = "0.6";
      await runSim(); // Llama a la función principal sin modo auto
      btnRun.disabled = false;
      btnRun.style.opacity = "1";
    });
  }

  // 8. Botón Ver Réplica (Escenario)
  const btnReplica = qs("btnReplica");
  if (btnReplica) {
    btnReplica.addEventListener("click", () => {
      loadScenario(+qs("replica_id").value);
    });
  }
});
