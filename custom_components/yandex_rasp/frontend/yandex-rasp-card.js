/* Yandex Rasp departure board card — bundled with the yandex_rasp integration. */

const CARD_VERSION = "0.2.0";
const DEFAULTS = { hours: 1, rows: 6 };

const STYLE = `
  :host { display: block; }
  ha-card { overflow: hidden; }
  .head {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 16px 10px;
    border-bottom: 3px solid #e2001a;
  }
  .logo {
    flex: none; width: 34px; height: 34px; border-radius: 8px;
    display: grid; place-items: center;
    background: #e2001a; color: #fff;
  }
  .logo ha-icon { --mdc-icon-size: 22px; }
  .station { flex: 1; min-width: 0; }
  .station .label {
    font-size: 10px; letter-spacing: .14em; text-transform: uppercase;
    color: var(--secondary-text-color);
  }
  .station .name {
    font-size: 19px; font-weight: 700; letter-spacing: .03em; text-transform: uppercase;
    color: var(--primary-text-color);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .clock, .time, .eta b {
    font-family: "DejaVu Sans Mono", "Roboto Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
  .clock {
    font-size: 26px; font-weight: 700; color: #ffb000;
    text-shadow: 0 0 8px rgba(255,176,0,.4);
  }
  .clock .colon { animation: blink 1s steps(1) infinite; }
  @keyframes blink { 50% { opacity: .15; } }

  .cols { display: grid; grid-template-columns: 1fr 1fr; }
  .col { min-width: 0; }
  .col + .col { border-left: 1px solid var(--divider-color, rgba(127,127,127,.2)); }
  :host([size="stack"]) .cols { grid-template-columns: 1fr; }
  :host([size="stack"]) .col + .col {
    border-left: 0; border-top: 1px solid var(--divider-color, rgba(127,127,127,.2));
  }

  .dir {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 12px 6px;
    font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
    color: var(--secondary-text-color);
  }
  .dir span.t { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .dir ha-icon { --mdc-icon-size: 16px; color: #ffb000; flex: none; }
  .dir .count { margin-left: auto; font-weight: 500; letter-spacing: .04em; opacity: .7; }

  .row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center; gap: 2px 10px;
    padding: 6px 12px;
    border-top: 1px solid var(--divider-color, rgba(127,127,127,.15));
  }
  .time {
    font-size: 19px; font-weight: 700; color: #ffb000;
    text-shadow: 0 0 6px rgba(255,176,0,.3);
  }
  .route { min-width: 0; }
  .route .title {
    font-size: 13.5px; font-weight: 500; color: var(--primary-text-color);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .route .meta {
    display: flex; flex-wrap: wrap; align-items: center; gap: 3px 6px;
    margin-top: 2px; font-size: 11px; color: var(--secondary-text-color);
  }
  .chip {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 0 5px; border-radius: 4px; line-height: 16px;
    background: rgba(127,127,127,.15); color: var(--primary-text-color);
  }
  .chip i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
  .chip.express { background: #e2001a; color: #fff; font-weight: 700; letter-spacing: .05em; }
  .stops {
    grid-column: 1 / -1; font-size: 11px; color: #d9a441;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .eta { text-align: right; line-height: 1.05; }
  .eta b { display: block; font-size: 17px; font-weight: 700; color: #4cc35a; }
  .eta span {
    font-size: 9.5px; color: var(--secondary-text-color);
    text-transform: uppercase; letter-spacing: .06em;
  }
  .eta.soon b { color: #ff5a5a; }
  .eta.now b { color: #ff5a5a; animation: blink 1s steps(1) infinite; }

  .empty {
    padding: 12px; font-size: 12.5px; color: var(--secondary-text-color);
    border-top: 1px solid var(--divider-color, rgba(127,127,127,.15));
  }
  .more {
    padding: 4px 12px 8px; font-size: 11px; color: var(--secondary-text-color);
  }
  .foot {
    display: flex; justify-content: space-between; gap: 8px;
    padding: 7px 16px 9px; font-size: 10.5px; color: var(--secondary-text-color); opacity: .7;
    border-top: 1px solid var(--divider-color, rgba(127,127,127,.2));
  }
  /* Two narrow columns: time + eta on top, route below. */
  :host([size="compact"]) .row { grid-template-columns: 1fr auto; padding: 6px 10px; }
  :host([size="compact"]) .route { grid-column: 1 / -1; grid-row: 2; }
  :host([size="compact"]) .eta { display: flex; align-items: baseline; gap: 3px; }
  :host([size="compact"]) .eta b { display: inline; }
  :host([size="compact"]) .meta .num { display: none; }
  :host([size="compact"]) .dir { padding: 9px 10px 6px; }
  :host([size="compact"]) .head { padding: 10px 12px 8px; }
  :host([size="compact"]) .station .name { font-size: 17px; }
  :host([size="compact"]) .clock { font-size: 22px; }

  .warn { padding: 16px; color: var(--error-color, #ff5a5a); }
`;

const isMoscow = (title) => /москв/i.test(title);

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
};

const findEntity = (hass) =>
  Object.keys(hass.states).find(
    (id) => id.startsWith("sensor.") && hass.states[id].attributes.station_code &&
      Array.isArray(hass.states[id].attributes.departures));

class YandexRaspCard extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULTS, ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const entity = this._config.entity || findEntity(hass);
    const st = hass.states[entity];
    if (entity !== this._entity || st !== this._lastState) {
      this._entity = entity;
      this._lastState = st;
      this._render();
    }
  }

  connectedCallback() {
    // Countdown and clock tick without waiting for a state change.
    this._timer = setInterval(() => this._render(), 15000);
    this._resize = new ResizeObserver(([e]) => {
      const w = e.contentRect.width;
      const size = w < 300 ? "stack" : w < 560 ? "compact" : "wide";
      if (this.getAttribute("size") !== size) this.setAttribute("size", size);
    });
    this._resize.observe(this);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
    this._resize?.disconnect();
  }

  getCardSize() {
    return 2 + Number(this._config?.rows || DEFAULTS.rows);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  static getConfigElement() {
    return document.createElement("yandex-rasp-card-editor");
  }

  static getStubConfig(hass) {
    return { entity: findEntity(hass), ...DEFAULTS };
  }

  _clock() {
    const tz = this._hass?.config?.time_zone;
    const parts = new Intl.DateTimeFormat("ru-RU", {
      hour: "2-digit", minute: "2-digit", hour12: false, ...(tz ? { timeZone: tz } : {}),
    }).formatToParts(new Date());
    const h = parts.find((p) => p.type === "hour")?.value ?? "--";
    const m = parts.find((p) => p.type === "minute")?.value ?? "--";
    return `${h}<span class="colon">:</span>${m}`;
  }

  _row(d, now) {
    const mins = Math.floor((Date.parse(d.departure) - now) / 60000);
    const etaCls = mins <= 1 ? "now" : mins <= 5 ? "soon" : "";
    const eta = mins <= 0 ? "сейчас" : `${mins}`;
    const unit = mins <= 0 ? "" : "мин";
    const meta = [];
    if (d.express) meta.push(`<span class="chip express">ЭКСПРЕСС</span>`);
    if (d.subtype) {
      const dot = d.color ? `<i style="background:${esc(d.color)}"></i>` : "";
      meta.push(`<span class="chip">${dot}${esc(d.subtype)}</span>`);
    }
    if (d.number) meta.push(`<span class="num">№ ${esc(d.number)}</span>`);
    if (d.platform) meta.push(`<span>${esc(d.platform)}</span>`);
    const stops = d.stops && d.stops !== "везде"
      ? `<div class="stops" title="${esc(d.stops)}">${esc(d.stops)}</div>` : "";
    return `
      <div class="row">
        <div class="time">${esc(d.departure.slice(11, 16))}</div>
        <div class="route">
          <div class="title" title="${esc(d.title)}">${esc(d.title)}</div>
          <div class="meta">${meta.join("")}</div>
        </div>
        <div class="eta ${etaCls}"><b>${eta}</b><span>${unit}</span></div>
        ${stops}
      </div>`;
  }

  _column(title, list, now, rows, hoursText) {
    const shown = list.slice(0, rows);
    const body = shown.length
      ? shown.map((d) => this._row(d, now)).join("")
      : `<div class="empty">В ${hoursText} электричек нет</div>`;
    const more = list.length > shown.length
      ? `<div class="more">и ещё ${list.length - shown.length}</div>` : "";
    const icon = isMoscow(title) ? "mdi:arrow-right-bold" : "mdi:arrow-left-bold";
    return `
      <div class="col">
        <div class="dir"><ha-icon icon="${icon}"></ha-icon>
          <span class="t" title="${esc(title)}">${esc(title)}</span>
          <span class="count">${list.length || ""}</span></div>
        ${body}${more}
      </div>`;
  }

  _render() {
    if (!this.shadowRoot || !this._config || !this._hass) return;
    const st = this._hass.states[this._entity];
    if (!st) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="warn">
        Сущность ${esc(this._entity || "интеграции yandex_rasp")} не найдена</div></ha-card>`;
      return;
    }

    const a = st.attributes;
    const hours = Number(this._config.hours) || DEFAULTS.hours;
    const rows = Math.max(1, Number(this._config.rows) || DEFAULTS.rows);
    const now = Date.now();
    const until = now + hours * 3600000;
    const deps = (a.departures || []).filter((d) => {
      const t = Date.parse(d.departure);
      return t >= now - 30000 && t <= until;
    });

    // Left column: towards Moscow; right: every other direction.
    const dirs = [...(a.directions || [])];
    for (const d of deps) if (!dirs.includes(d.direction)) dirs.push(d.direction);
    const toMoscow = dirs.filter(isMoscow);
    const other = dirs.filter((t) => !isMoscow(t));
    const label = (list, fallback) => list.length ? list.join(" / ") : fallback;

    const hoursText = hours === 1
      ? "ближайший час"
      : `ближайшие ${hours} ${plural(hours, "час", "часа", "часов")}`;

    const columns = [
      this._column(label(toMoscow, "на Москву"),
        deps.filter((d) => isMoscow(d.direction)), now, rows, hoursText),
      this._column(label(other, "из Москвы"),
        deps.filter((d) => !isMoscow(d.direction)), now, rows, hoursText),
    ].join("");

    const tz = this._hass.config?.time_zone;
    const upd = a.updated ? new Date(a.updated).toLocaleTimeString("ru-RU",
      { hour: "2-digit", minute: "2-digit", ...(tz ? { timeZone: tz } : {}) }) : "—";
    const name = this._config.title || a.station || a.friendly_name;

    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card>
        <div class="head">
          <div class="logo"><ha-icon icon="mdi:train"></ha-icon></div>
          <div class="station">
            <div class="label">Электрички · ${esc(hoursText)}</div>
            <div class="name">${esc(name)}</div>
          </div>
          <div class="clock">${this._clock()}</div>
        </div>
        <div class="cols">${columns}</div>
        <div class="foot"><span>Яндекс.Расписания</span><span>обновлено ${upd}</span></div>
      </ha-card>`;
  }
}

const EDITOR_SCHEMA = [
  { name: "entity", selector: { entity: { domain: "sensor", integration: "yandex_rasp" } } },
  { name: "title", selector: { text: {} } },
  {
    type: "grid", name: "", schema: [
      { name: "rows", selector: { number: { min: 1, max: 30, mode: "box" } } },
      { name: "hours", selector: { number: { min: 1, max: 3, mode: "box", unit_of_measurement: "ч" } } },
    ],
  },
];

const EDITOR_LABELS = {
  entity: "Сенсор станции",
  title: "Заголовок (по умолчанию — название станции)",
  rows: "Строк в каждом столбце",
  hours: "Окно, часов",
};

class YandexRaspCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULTS, ...config };
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  _update() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => EDITOR_LABELS[s.name] ?? s.name;
      this._form.addEventListener("value-changed", (ev) => {
        const config = { ...ev.detail.value };
        for (const k of Object.keys(config)) if (config[k] === "" || config[k] == null) delete config[k];
        this._config = config;
        this.dispatchEvent(new CustomEvent("config-changed",
          { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = EDITOR_SCHEMA;
    this._form.data = this._config;
  }
}

if (!customElements.get("yandex-rasp-card")) {
  customElements.define("yandex-rasp-card", YandexRaspCard);
}
if (!customElements.get("yandex-rasp-card-editor")) {
  customElements.define("yandex-rasp-card-editor", YandexRaspCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "yandex-rasp-card")) window.customCards.push({
  type: "yandex-rasp-card",
  name: "Табло электричек",
  description: "Расписание электричек по станции (интеграция Яндекс.Расписания)",
  preview: true,
});

console.info(`%c YANDEX-RASP-CARD %c ${CARD_VERSION} `,
  "background:#e2001a;color:#fff;font-weight:700", "background:#12306b;color:#fff");
