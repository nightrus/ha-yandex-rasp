/* Yandex Rasp departure board card — bundled with the yandex_rasp integration. */

const CARD_VERSION = "0.1.0";

const STYLE = `
  :host { display: block; }
  ha-card {
    overflow: hidden;
    border-radius: var(--ha-card-border-radius, 12px);
    background:
      repeating-linear-gradient(0deg, rgba(255,255,255,.018) 0 1px, transparent 1px 3px),
      linear-gradient(180deg, #0d1422 0%, #080b12 100%);
    color: #e8ecf3;
    border: 1px solid #1c2638;
    font-family: var(--paper-font-body1_-_font-family, Roboto, "Segoe UI", sans-serif);
  }
  .head {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 16px;
    background: linear-gradient(90deg, #12306b, #0e2350);
    border-bottom: 3px solid #e2001a;
  }
  .logo {
    flex: none; width: 36px; height: 36px; border-radius: 8px;
    display: grid; place-items: center;
    background: #e2001a; color: #fff;
  }
  .logo ha-icon { --mdc-icon-size: 22px; }
  .station { flex: 1; min-width: 0; }
  .station .label {
    font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: #9fb4dc;
  }
  .station .name {
    font-size: 19px; font-weight: 700; letter-spacing: .03em; text-transform: uppercase;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .clock, .time, .eta b {
    font-family: "DejaVu Sans Mono", "Roboto Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
  .clock {
    font-size: 26px; font-weight: 700; color: #ffb000;
    text-shadow: 0 0 8px rgba(255,176,0,.45);
  }
  .clock .colon { animation: blink 1s steps(1) infinite; }
  @keyframes blink { 50% { opacity: .15; } }

  .dir {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 16px 5px;
    font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: #7f93b8;
  }
  .dir ha-icon { --mdc-icon-size: 16px; color: #ffb000; }
  .dir .count { margin-left: auto; font-weight: 500; letter-spacing: .04em; color: #56688a; }

  .row {
    display: grid;
    grid-template-columns: 58px 1fr auto;
    align-items: center; gap: 12px;
    padding: 5px 16px;
    border-top: 1px solid rgba(255,255,255,.05);
  }
  .row:nth-child(even) { background: rgba(255,255,255,.02); }
  .time {
    font-size: 20px; font-weight: 700; color: #ffb000;
    text-shadow: 0 0 6px rgba(255,176,0,.35);
  }
  .route { min-width: 0; }
  .route .title {
    font-size: 14.5px; font-weight: 500;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .route .meta {
    display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px;
    margin-top: 2px; font-size: 11.5px; color: #8494b3;
  }
  .chip {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 0 6px; border-radius: 4px; line-height: 17px;
    background: rgba(255,255,255,.06); color: #c9d3e6;
  }
  .chip i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
  .chip.express { background: #e2001a; color: #fff; font-weight: 700; letter-spacing: .05em; }
  .stops { color: #d9a441; }
  .eta { text-align: right; line-height: 1.05; }
  .eta b { display: block; font-size: 19px; font-weight: 700; color: #7ee08a; }
  .eta span { font-size: 10px; color: #6c7c9c; text-transform: uppercase; letter-spacing: .08em; }
  .eta.soon b { color: #ff5a5a; }
  .eta.now b { color: #ff5a5a; animation: blink 1s steps(1) infinite; }

  .empty {
    padding: 14px 16px; font-size: 13px; color: #6c7c9c;
    border-top: 1px solid rgba(255,255,255,.05);
  }
  .foot {
    display: flex; justify-content: space-between; gap: 8px;
    padding: 7px 16px 9px; font-size: 10.5px; color: #4f5f80;
    border-top: 1px solid #1c2638;
  }
  .warn { padding: 16px; color: #ff8a80; }
`;

const DIR_ICON = (title) =>
  /москв/i.test(title) ? "mdi:arrow-right-bold" : "mdi:arrow-left-bold";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
};

class YandexRaspCard extends HTMLElement {
  setConfig(config) {
    this._config = { hours: 1, ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config.entity) {
      this._config.entity = Object.keys(hass.states).find(
        (id) => id.startsWith("sensor.") && hass.states[id].attributes.station_code &&
          Array.isArray(hass.states[id].attributes.departures));
    }
    const st = hass.states[this._config.entity];
    if (st !== this._lastState) {
      this._lastState = st;
      this._render();
    }
  }

  connectedCallback() {
    // Countdown and clock tick without waiting for a state change.
    this._timer = setInterval(() => this._render(), 15000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (id) => id.startsWith("sensor.") && hass.states[id].attributes.station_code);
    return { entity, hours: 1 };
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
    const unit = mins <= 0 ? "" : plural(mins, "минута", "минуты", "минут");
    const meta = [];
    if (d.express) meta.push(`<span class="chip express">ЭКСПРЕСС</span>`);
    if (d.subtype) {
      const dot = d.color ? `<i style="background:${esc(d.color)}"></i>` : "";
      meta.push(`<span class="chip">${dot}${esc(d.subtype)}</span>`);
    }
    if (d.number) meta.push(`<span>№ ${esc(d.number)}</span>`);
    if (d.platform) meta.push(`<span>${esc(d.platform)}</span>`);
    if (d.stops && d.stops !== "везде") meta.push(`<span class="stops">${esc(d.stops)}</span>`);
    return `
      <div class="row">
        <div class="time">${esc(d.departure.slice(11, 16))}</div>
        <div class="route">
          <div class="title">${esc(d.title)}</div>
          <div class="meta">${meta.join("")}</div>
        </div>
        <div class="eta ${etaCls}"><b>${eta}</b><span>${unit}</span></div>
      </div>`;
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    const st = this._hass?.states?.[this._config.entity];
    if (!this._hass) return;
    if (!st) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="warn">
        Сущность ${esc(this._config.entity || "интеграции yandex_rasp")} не найдена</div></ha-card>`;
      return;
    }

    const a = st.attributes;
    const now = Date.now();
    const until = now + this._config.hours * 3600000;
    const deps = (a.departures || []).filter((d) => {
      const t = Date.parse(d.departure);
      return t >= now - 30000 && t <= until;
    });
    const directions = [...(a.directions || [])];
    for (const d of deps) if (!directions.includes(d.direction)) directions.push(d.direction);

    const hoursText = this._config.hours === 1
      ? "ближайший час"
      : `ближайшие ${this._config.hours} ${plural(this._config.hours, "час", "часа", "часов")}`;

    const sections = directions.map((dir) => {
      const list = deps.filter((d) => d.direction === dir);
      const rows = list.length
        ? list.map((d) => this._row(d, now)).join("")
        : `<div class="empty">В ${hoursText} электричек нет</div>`;
      return `
        <div class="dir"><ha-icon icon="${DIR_ICON(dir)}"></ha-icon>${esc(dir)}
          <span class="count">${list.length || ""}</span></div>
        ${rows}`;
    }).join("");

    const tz = this._hass.config?.time_zone;
    const upd = a.updated ? new Date(a.updated).toLocaleTimeString("ru-RU",
      { hour: "2-digit", minute: "2-digit", ...(tz ? { timeZone: tz } : {}) }) : "—";
    const name = this._config.title || a.station || st.attributes.friendly_name;

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
        ${sections || `<div class="empty">В ${hoursText} электричек нет</div>`}
        <div class="foot"><span>Яндекс.Расписания</span><span>обновлено ${upd}</span></div>
      </ha-card>`;
  }
}

if (!customElements.get("yandex-rasp-card")) {
  customElements.define("yandex-rasp-card", YandexRaspCard);
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
