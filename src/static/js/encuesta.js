// Provincias por departamento (Bolivia)
const PROVINCIAS = {
  "La Paz":["Abel Iturralde","Aroma","Bautista Saavedra","Camacho","Caranavi","Franz Tamayo","Gualberto Villarroel","Ingavi","Inquisivi","Larecaja","Loayza","Los Andes","Manco Kapac","Muñecas","Murillo","Nor Yungas","Omasuyos","Pacajes","Sud Yungas"],
  "Santa Cruz":["Andrés Ibáñez","Ángel Sandóval","Caballero","Chiquitos","Cordillera","Florida","Germán Busch","Guarayos","Ichilo","Ñuflo de Chávez","Obispo Santistevan","Sara","Vallegrande","Velasco"],
  "Cochabamba":["Arani","Arque","Ayopaya","Bolívar","Capinota","Cercado","Carrasco","Chapare","Esteban Arce","Germán Jordán","Mizque","Punata","Quillacollo","Tapacarí","Tiraque"],
  "Oruro":["Atahuallpa (Sabaya)","Carangas","Cercado","Eduardo Avaroa","Ladislao Cabrera","Litoral de Atacama","Mejillones","Nor Carangas","Pantaleón Dalence","Poopó","Sajama","San Pedro de Totora","Saucarí","Sebastián Pagador","Sud Carangas","Tomás Barrón"],
  "Potosí":["Alonso de Ibáñez","Antonio Quijarro","Bernardino Bilbao","Charcas","Chayanta","Cornelio Saavedra","Daniel Campos","Enrique Baldivieso","José María Linares","Modesto Omiste","Nor Chichas","Nor Lípez","Rafael Bustillo","Sur Chichas","Sur Lípez","Tomás Frías"],
  "Chuquisaca":["Azurduy","Belisario Boeto","Hernando Siles","Jaime Zudáñez","Juana Azurduy de Padilla","Luis Calvo","Nor Cinti","Oropeza","Sud Cinti","Tomina","Yamparáez"],
  "Tarija":["Aniceto Arce","Avilés","Cercado","Eustaquio Méndez","Gran Chaco","José María Avilés","O’Connor"],
  "Beni":["Cercado","Iténez","José Ballivián","Mamoré","Marbán","Moxos","Vaca Díez","Yacuma"],
  "Pando":["Abuná","Federico Román","Madre de Dios","Manuripi","Nicolás Suárez"]
};

// Etiquetas sliders
const INTERNET_LABEL = {1:"Menos de 2 horas",2:"2-4 horas",3:"5-7 horas",4:"Más de 7 horas"};
const SEGURIDAD_LABEL = {1:"Nada Seguro",2:"Poco Seguro",3:"Moderadamente Seguro",4:"Seguro",5:"Completamente Seguro"};
const INTERES_LABEL = {1:"Nada interesado",2:"Poco interesado",3:"Moderadamente interesado",4:"Interesado",5:"Muy interesado"};
const FRECUENCIA_LABEL = {1:"Nunca",2:"A veces",3:"Frecuentemente",4:"Muy frecuente"};

// Indicadores sección 7 (texto para mostrar si quieres)
const S7_TRAYECTORIA = {1:"Nada influyente",2:"Poco influyente",3:"Moderadamente influyente",4:"Bastante influyente",5:"Muy influyente"};
const S7_CONOCIMIENTO = {1:"No conozco nada",2:"Conozco poco",3:"Conozco algo",4:"Conozco bastante",5:"Conozco muy bien"};
const S7_VP = {1:"Sin importancia",2:"Poca importancia",3:"Moderadamente importante",4:"Importante",5:"Muy importante"};

// Util
const isHidden = (el) => !!el.closest("[hidden]");

document.addEventListener("DOMContentLoaded", () => {
  // ====== Departamento -> Provincia ======
  const dep = document.getElementById("departamento");
  const prov = document.getElementById("provincia");
  if (dep && prov) {
    dep.addEventListener("change", () => {
      const lista = PROVINCIAS[dep.value] || [];
      prov.innerHTML = `<option value="" disabled selected>Seleccione primero un departamento</option>` +
        lista.map(p => `<option>${p}</option>`).join("");
    });
  }

  // ====== Situación educativa (campos condicionales + required dinámico) ======
  const situacion = document.getElementById("situacion");
  const cEstWrap = document.getElementById("campo_carrera_estudiante");
  const cProfWrap = document.getElementById("campo_carrera_profesional");
  const aProfWrap = document.getElementById("campo_area_profesional");
  const cEst = document.getElementById("carrera_est");
  const cProf = document.getElementById("carrera_prof");
  const aProf = document.getElementById("area_prof");

  const toggleSituacion = () => {
    const v = situacion.value;
    const esEst = v === "estudiante";
    const esProf = v === "profesional";

    cEstWrap.hidden = !esEst;
    cProfWrap.hidden = !esProf;
    aProfWrap.hidden = !esProf;

    cEst.required = esEst;
    cProf.required = esProf;
    aProf.required = esProf;

    if (!esEst) cEst.value = "";
    if (!esProf) { cProf.value = ""; aProf.value = ""; }
  };
  if (situacion) {
    situacion.addEventListener("change", toggleSituacion);
    toggleSituacion();
  }

  // ====== Evento determinante -> Otro (toggle required) ======
  const eventoSel = document.getElementById("evento_det");
  const eventoOtroWrap = document.getElementById("campo_evento_otro");
  const eventoOtro = document.getElementById("evento_otro");
  const toggleOtro = () => {
    const show = (eventoSel.value === "Otro (Especificar)");
    eventoOtroWrap.hidden = !show;
    eventoOtro.required = show;
    if (!show) eventoOtro.value = "";
  };
  if (eventoSel && eventoOtroWrap) {
    eventoSel.addEventListener("change", toggleOtro);
    toggleOtro();
  }

  // ====== Sliders y valores ocultos ======
  const bindSlider = (sliderId, labelId, hiddenId, map, sendRawNumber=false) => {
    const slider = document.getElementById(sliderId);
    const label  = document.getElementById(labelId);
    const hidden = document.getElementById(hiddenId);
    if (!slider || !label || !hidden) return;
    const update = () => {
      const txt = map[slider.value] || "Seleccione moviendo el control";
      label.textContent = txt;
      hidden.value = sendRawNumber ? slider.value : txt;
    };
    slider.addEventListener("input", update);
    update(); // inicial para que el hidden nunca quede vacío
  };
  bindSlider("internet_slider","internet_label","internet_value",INTERNET_LABEL);
  bindSlider("seguridad_slider","seguridad_label","seguridad_value",SEGURIDAD_LABEL,true);
  bindSlider("interes_slider","interes_label","interes_value",INTERES_LABEL);
  bindSlider("frecuencia_slider","frecuencia_label","frecuencia_value",FRECUENCIA_LABEL);

  // ====== Render genérico (Likert 1..5) para .likert ======
  document.querySelectorAll(".likert").forEach(div => {
    const name = div.dataset.name;
    for (let i=1; i<=5; i++){
      const id = `${name}_${i}`;
      const input = document.createElement("input");
      input.type = "radio"; input.name = name; input.id = id; input.value = i;
      const lab = document.createElement("label");
      lab.setAttribute("for", id); lab.textContent = i;
      div.appendChild(input); div.appendChild(lab);
    }
  });

  // (Opcional) indicadores de estado en sección 7
  const s7map = {
    "trayectoria_influye": { el: document.getElementById("trayectoria_influye_text"), dict: S7_TRAYECTORIA },
    "trayectoria_conocimiento": { el: document.getElementById("trayectoria_conocimiento_text"), dict: S7_CONOCIMIENTO },
    "vp_importancia": { el: document.getElementById("vp_importancia_text"), dict: S7_VP },
  };
  Object.keys(s7map).forEach(name => {
    document.addEventListener("change", (evt) => {
      if (evt.target && evt.target.name === name && evt.target.checked) {
        const m = s7map[name];
        if (m && m.el) m.el.textContent = m.dict[evt.target.value] || "";
      }
    });
  });

  // ====== VALIDACIÓN ESTRICTA SOLO JS (bloqueante) ======
  const form = document.getElementById("encuestaForm");

  // Helpers
  const mustSelect = (id, labelText) => {
    const el = document.getElementById(id);
    if (!el || isHidden(el)) return null;
    const val = (el.value || "").trim();
    if (!val) return {el, msg:`Seleccione una opción en "${labelText}".`};
    return null;
  };
  const mustFill = (id, labelText) => {
    const el = document.getElementById(id);
    if (!el || isHidden(el)) return null;
    const val = (el.value || "").trim();
    if (!val) return {el, msg:`Complete el campo "${labelText}".`};
    return null;
  };
  const groupChecked = (name, labelText) => {
    const nodes = Array.from(document.querySelectorAll(`input[type="radio"][name="${name}"]`))
      .filter(r => !isHidden(r));
    if (!nodes.length) return null; // grupo no visible
    if (!nodes.some(r => r.checked)) {
      return {el: nodes[0], msg:`Seleccione una opción en "${labelText}".`};
    }
    return null;
  };
  const atLeastOneChecked = (name, labelText) => {
    const nodes = Array.from(document.querySelectorAll(`input[type="checkbox"][name="${name}"]`))
      .filter(c => !isHidden(c));
    if (nodes.length && !nodes.some(c => c.checked)) {
      return {el: nodes[0], msg:`Seleccione al menos una opción en "${labelText}".`};
    }
    return null;
  };

  form.addEventListener("submit", (e) => {
    // 1) SELECTS / TEXTOS requeridos (visibles)
    const checks = [];

    // Sección 1
    checks.push(mustSelect("edad","Edad"));
    checks.push(mustSelect("genero","Género"));
    checks.push(mustSelect("departamento","Departamento"));
    checks.push(mustSelect("provincia","Provincia / Localidad"));
    checks.push(mustSelect("situacion","Situación Educativa"));
    // condicionales:
    const sitVal = (document.getElementById("situacion")?.value || "");
    if (sitVal === "estudiante") {
      checks.push(mustFill("carrera_est","Carrera (estudiante)"));
    }
    if (sitVal === "profesional") {
      checks.push(mustFill("carrera_prof","Carrera (profesional)"));
      checks.push(mustSelect("area_prof","Área profesional"));
    }
    checks.push(mustSelect("estrato","Estrato Socioeconómico"));
    checks.push(mustSelect("estatus_laboral","Estatus Laboral"));

    // Sliders (tienen hidden que se llena en bindSlider)
    checks.push(mustFill("internet_value","Tiempo de conexión a internet por día"));

    // Servicios básicos (al menos uno)
    checks.push(atLeastOneChecked("servicios","Acceso a servicios básicos"));

    // Sección 2
    checks.push(mustSelect("intencion_voto","Si las elecciones fueran mañana, ¿por quién votarías?"));
    checks.push(mustFill("seguridad_value","¿Qué tan seguro estás de tu elección?"));
    checks.push(mustSelect("evento_det","Evento determinante"));
    if (document.getElementById("evento_det")?.value === "Otro (Especificar)") {
      checks.push(mustFill("evento_otro","Evento determinante (otro, especificar)"));
    }
    checks.push(mustFill("interes_value","Interés por la política nacional"));
    checks.push(mustFill("frecuencia_value","Frecuencia con la que conversas sobre política"));
    checks.push(mustSelect("alineamiento","Alineamiento ideológico personal"));

    // Sección 3 (temas generales)
    const s3 = [
      ["s3_economia","Economía"],
      ["s3_educacion","Educación"],
      ["s3_corrupcion_justicia","Corrupción y Justicia"],
      ["s3_servicios","Servicios Públicos"],
      ["s3_seguridad","Seguridad Ciudadana"],
      ["s3_medioambiente","Medio Ambiente"],
      ["s3_derechos","Derechos Sociales"],
      ["s3_modelo_desarrollo","Modelo de Desarrollo"]
    ];
    s3.forEach(([name, label]) => checks.push(groupChecked(name, `Factores de decisión: ${label}`)));

    // Sección 4 (atributos candidato: 10 + 10) + Medio de influencia
    for (let i=1;i<=10;i++){
      checks.push(groupChecked(`attr_rodrigo_${i}`, `Atributo "${i}" - Rodrigo Paz`));
      checks.push(groupChecked(`attr_tuto_${i}`, `Atributo "${i}" - Tuto Quiroga`));
    }
    checks.push(atLeastOneChecked("medio_influencia","Medio de influencia"));

    // Sección 5 (3 grupos tipo pill + 1 select ya validado arriba)
    checks.push(groupChecked("cond_oportunidades","Oportunidades para jóvenes"));
    checks.push(groupChecked("cond_demanda_carrera","Demanda de mi carrera"));
    checks.push(groupChecked("cond_acceso_formal","Acceso a empleos formales"));

    // Sección 6 (problemáticas)
    const probs = [
      ["prob_crisis","Crisis y desempleo"],
      ["prob_combustible","Combustible y energía"],
      ["prob_transporte","Transporte público"],
      ["prob_corrupcion","Corrupción/Desconfianza"],
      ["prob_seguridad","Seguridad ciudadana"],
      ["prob_salud_educacion","Salud y educación"],
      ["prob_medioambiente","Medio ambiente"]
    ];
    probs.forEach(([name,label]) => checks.push(groupChecked(name, `Problemática: ${label}`)));

    // Sección 7 (3 likert)
    checks.push(groupChecked("trayectoria_influye","Influencia del pasado del candidato"));
    checks.push(groupChecked("trayectoria_conocimiento","Conocimiento del historial de candidatos"));
    checks.push(groupChecked("vp_importancia","Importancia del rol del vicepresidente"));

    // Primer error
    const firstError = checks.find(x => x && x.msg);
    if (firstError) {
      e.preventDefault();
      alert(firstError.msg);
      firstError.el.scrollIntoView({behavior:"smooth", block:"center"});
      firstError.el.focus();
      return;
    }
  });
});
