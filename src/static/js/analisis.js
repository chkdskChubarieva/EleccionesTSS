// Variables globales
let sensChart;
let debounceTimer;

// Helper para seleccionar elementos (mismo estilo que dashboard.js)
function qs(id) { return document.getElementById(id); }

// 1. Configuración e Inicialización del Gráfico
function initChart() {
    const ctx = qs('chartSensibilidad').getContext('2d');
    
    // Gradientes para que se vea moderno
    const gradientA = ctx.createLinearGradient(0, 0, 0, 400);
    gradientA.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // Blue
    gradientA.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    const gradientB = ctx.createLinearGradient(0, 0, 0, 400);
    gradientB.addColorStop(0, 'rgba(236, 72, 153, 0.5)'); // Pink
    gradientB.addColorStop(1, 'rgba(236, 72, 153, 0.0)');

    sensChart = new Chart(ctx, {
        type: 'line',
        data: {
            // Etiquetas iniciales (se pueden actualizar dinámicamente si el backend las manda)
            labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6'], 
            datasets: [
                { 
                    label: 'Candidato A (Proyección)', 
                    data: [], // Se llena al cargar
                    borderColor: '#3b82f6', 
                    backgroundColor: gradientA,
                    tension: 0.4,
                    fill: true 
                },
                { 
                    label: 'Candidato B (Proyección)', 
                    data: [], // Se llena al cargar
                    borderColor: '#ec4899', 
                    backgroundColor: gradientB,
                    tension: 0.4,
                    fill: true 
                }
            ]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: { beginAtZero: false } // Para ver mejor la variación
            }
        }
    });
}

// 2. Función principal: Recopila datos y llama a la API
function actualizarAnalisis() {
    // UI Feedback: Mostrar spinners o estado cargando si fuera necesario
    const tbody = qs('tbodySensibilidad');
    if(tbody) tbody.style.opacity = '0.5';

    // A. Obtener valores de los 5 sliders
    const lealtad = qs('slider_lealtad').value;
    const contagio = qs('slider_contagio').value;
    const ruido = qs('slider_ruido').value;
    const medios = qs('slider_medios').value;   // Nuevo
    const memoria = qs('slider_memoria').value; // Nuevo

    // B. Actualizar etiquetas visuales (Feedback numérico)
    qs('val_lealtad').textContent = parseFloat(lealtad).toFixed(1) + 'x';
    qs('val_contagio').textContent = parseFloat(contagio).toFixed(1) + 'x';
    qs('val_ruido').textContent = parseFloat(ruido).toFixed(1) + 'x';
    qs('val_medios').textContent = parseFloat(medios).toFixed(1) + 'x'; // Nuevo
    qs('val_memoria').textContent = parseFloat(memoria).toFixed(1);     // Nuevo

    // C. Llamada al Backend con todas las variables
    fetch('/api/sensitivity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            factor_lealtad: lealtad,
            factor_contagio: contagio,
            factor_ruido: ruido,
            factor_medios: medios,    // Nuevo
            factor_memoria: memoria   // Nuevo
        })
    })
    .then(response => response.json())
    .then(data => {
        renderTable(data.rows);
        updateChart(data.projection);
    })
    .catch(err => console.error("Error en análisis de sensibilidad:", err))
    .finally(() => {
        if(tbody) tbody.style.opacity = '1';
    });
}

// 3. Renderizar la Tabla
function renderTable(rows) {
    const tbody = qs('tbodySensibilidad');
    tbody.innerHTML = '';

    if(!rows || rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="p-4 text-center text-slate-400">No hay datos disponibles</td></tr>';
        return;
    }

    // A) Agrupar por estrato
    const byEstrato = {};
    rows.forEach(r => {
        const e = r.estrato || "Sin estrato";
        if (!byEstrato[e]) byEstrato[e] = [];
        byEstrato[e].push(r);
    });

    // B) Ordenar por rank (1..3) dentro de cada estrato
    Object.keys(byEstrato).forEach(e => {
        byEstrato[e].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
    });

    // C) Renderizar 1 fila por estrato (rank 1), con tooltip Top 3
    Object.keys(byEstrato).forEach(estrato => {
        const topList = byEstrato[estrato].slice(0, 3);
        const top1 = topList[0];

        if (!top1) return;

        // Tooltip (formato bonito + reemplaza _ por espacios)
        const tooltip = topList
            .map((x, i) => {
                const name = String(x.factor || "").replaceAll("_", " ");
                const coef = Number(x.coef);
                return `${i+1}) ${name} (${isFinite(coef) ? coef.toFixed(3) : "0.000"})`;
            })
            .join("\n");

        // Colores por coef (solo del top1)
        const coef1 = Number(top1.coef);
        const isHigh = isFinite(coef1) && coef1 > 0.8;
        const colorClass = isHigh ? 'text-green-600' : 'text-slate-600';
        const bgClass = isHigh ? 'bg-green-50' : '';

        const tr = document.createElement('tr');
        tr.className = `border-b hover:bg-slate-50 transition-colors cursor-help ${bgClass}`;

        // ✅ Tooltip nativo del navegador
        tr.title = `Top 3 factores — ${estrato}\n${tooltip}`;

        tr.innerHTML = `
            <td class="p-3 font-medium text-slate-700">${estrato}</td>
            <td class="p-3 text-right text-xs text-slate-500 font-mono">${String(top1.factor || "")}</td>
            <td class="p-3 text-right font-bold ${colorClass}">
                ${isFinite(coef1) ? coef1.toFixed(3) : "0.000"}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 4. Actualizar el Gráfico
function updateChart(projection) {
    if (!projection || !sensChart) return;

    // Asumiendo que el backend devuelve arrays de datos
    sensChart.data.datasets[0].data = projection.A;
    sensChart.data.datasets[1].data = projection.B;
    
    // Si la proyección cambia de longitud, actualizamos labels (opcional)
    if (projection.A.length !== sensChart.data.labels.length) {
        sensChart.data.labels = projection.A.map((_, i) => `Sem ${i+1}`);
    }

    sensChart.update();
}

// 5. Utilidad: Debounce para no saturar con llamadas mientras deslizas
function onSliderInput() {
    // Actualizar texto inmediatamente para UX mientras deslizas
    qs('val_lealtad').textContent = parseFloat(qs('slider_lealtad').value).toFixed(1) + 'x';
    qs('val_contagio').textContent = parseFloat(qs('slider_contagio').value).toFixed(1) + 'x';
    qs('val_ruido').textContent = parseFloat(qs('slider_ruido').value).toFixed(1) + 'x';
    qs('val_medios').textContent = parseFloat(qs('slider_medios').value).toFixed(1) + 'x'; // Nuevo
    qs('val_memoria').textContent = parseFloat(qs('slider_memoria').value).toFixed(1);     // Nuevo

    // Esperar a que el usuario deje de mover para llamar a la API
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(actualizarAnalisis, 300); // 300ms de espera
}

// 6. Resetear valores
function resetSliders() {
    qs('slider_lealtad').value = 1.0;
    qs('slider_contagio').value = 1.0;
    qs('slider_ruido').value = 1.0;
    qs('slider_medios').value = 1.0;  // Nuevo (Default)
    qs('slider_memoria').value = 0.8; // Nuevo (Default)
    actualizarAnalisis();
}

// Inicialización cuando carga el DOM
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    // Listeners para los sliders (input = tiempo real mientras arrastras)
    // Agregamos los IDs de los nuevos sliders al array
    const sliders = [
        'slider_lealtad', 
        'slider_contagio', 
        'slider_ruido', 
        'slider_medios', 
        'slider_memoria'
    ];

    sliders.forEach(id => {
        const el = qs(id);
        if(el) {
            el.addEventListener('input', onSliderInput);
        }
    });

    // Carga inicial
    actualizarAnalisis();
});