/* ---------------------- Generic fetch helper ---------------------- */
async function fetchJson(url) {
  const res = await fetch(url);
  try {
    return await res.json();
  } catch (e) {
    console.error('Failed to parse JSON from', url, e);
    return { success: false, error: 'Invalid JSON' };
  }
}

/* ---------------------- API callers (current blueprint routes) ---------------------- */
async function fetchPrices(commodity, state) {
  const q = new URLSearchParams();
  if (commodity) q.append('commodity', commodity);
  if (state) q.append('state', state);
  q.append('limit', '1000'); // fetch more records to improve chart coverage
  const url = '/market/api/prices?' + q.toString();
  return fetchJson(url);
}

async function fetchStates() {
  return fetchJson('/market/api/states');
}

async function fetchCommodities(state) {
  const url = state ? `/market/api/commodities?state=${encodeURIComponent(state)}` : '/market/api/commodities';
  return fetchJson(url);
}

/* ---------------------- HTML escaping & table rendering ---------------------- */
function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m]);
}

function renderTable(records) {
  if (!records || records.length === 0) return '<div class="text-muted p-3">No results</div>';

  const rows = records.map(r => `
    <tr>
      <td>${r.reported_date || ''}</td>
      <td>${escapeHtml(r.state || '')}</td>
      <td>${escapeHtml(r.market || '')}</td>
      <td>${escapeHtml(r.commodity || '')}</td>
      <td>${r.modal_price || ''}</td>
    </tr>
  `).join('');

  return `
    <table class="table table-striped table-sm mb-0">
      <thead class="table-dark">
        <tr>
          <th>Date</th>
          <th>State</th>
          <th>Market</th>
          <th>Commodity</th>
          <th>Modal Price (₹/kg)</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

/* ---------------------- Price parsing & aggregation helpers ---------------------- */

// parse modal price strings like "1,234", "₹ 1,234.00" into a Number
function parsePrice(val) {
  if (val === null || val === undefined) return NaN;
  let s = String(val).trim();
  s = s.replace(/[^\d.,-]/g, ''); // remove currency symbols/spaces
  s = s.replace(/,/g, '');        // normalize thousands comma
  const n = Number(s);
  return isFinite(n) ? n : NaN;
}

// aggregate records by date (reported_date) -> average modal_price per date
function aggregateByDate(records) {
  const map = new Map();
  for (const r of (records || [])) {
    if (!r || !r.reported_date) continue;
    const date = r.reported_date;
    const p = parsePrice(r.modal_price);
    if (Number.isNaN(p)) continue;
    if (!map.has(date)) map.set(date, { sum: 0, count: 0 });
    const cur = map.get(date);
    cur.sum += p;
    cur.count += 1;
  }
  const items = Array.from(map.entries()).map(([date, obj]) => ({ date, avg: obj.sum / obj.count }));
  // Try date-aware sort
  items.sort((a, b) => {
    const da = new Date(a.date);
    const db = new Date(b.date);
    if (!isNaN(da) && !isNaN(db)) return da - db;
    return a.date > b.date ? 1 : -1;
  });
  return items;
}

// compute simple moving average on numeric array
function movingAverage(values, windowSize) {
  if (!values || values.length === 0) return [];
  const out = [];
  const w = Math.max(1, Math.floor(windowSize));
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= w) sum -= values[i - w];
    if (i >= w - 1) out.push( +(sum / w).toFixed(2) );
    else out.push(null);
  }
  return out;
}

// format currency with ₹ and thousands separators
function formatCurrency(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-';
  const parts = Number(n).toFixed(2).split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return '₹' + parts.join('.');
}

/* ---------------------- Chart: aggregated avg + 7-day MA ---------------------- */

let chart = null;

function renderChart(records) {
  const canvas = document.getElementById('priceChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Try to aggregate by reported_date
  const aggregated = aggregateByDate(records);

  let labels = [];
  let data = [];
  let ma7 = [];

  if (aggregated.length > 0) {
    // Normal case: data has dates
    labels = aggregated.map(x => x.date);
    data = aggregated.map(x => +(x.avg.toFixed(2)));
    ma7 = movingAverage(data, 7);
  } else {
    // Fallback: plot by index if no reported_date exists
    const numericRecords = records
      .map((r, i) => ({ idx: i + 1, price: parsePrice(r.modal_price) }))
      .filter(x => !Number.isNaN(x.price));

    if (numericRecords.length === 0) {
      if (chart) chart.destroy();
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const rect = canvas.getBoundingClientRect();
      ctx.font = '16px Arial';
      ctx.fillStyle = '#666';
      ctx.textAlign = 'center';
      ctx.fillText('No numeric price data available', rect.width / 2, rect.height / 2);
      return;
    }

    labels = numericRecords.map(x => `Record ${x.idx}`);
    data = numericRecords.map(x => x.price);
    ma7 = movingAverage(data, 7);
  }

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Modal Price (₹/kg)',
          data,
          borderColor: '#1976d2',
          backgroundColor: 'rgba(25,118,210,0.08)',
          tension: 0.2,
          pointRadius: 2,
        },
        {
          label: '7-day MA (₹/kg)',
          data: ma7,
          borderColor: '#2e7d32',
          backgroundColor: 'rgba(46,125,50,0.06)',
          borderDash: [6,4],
          tension: 0.25,
          pointRadius: 0,
        }
      ]
    },
    options: {
      maintainAspectRatio: false,
      responsive: true,
      scales: {
        y: {
          title: { display: true, text: 'Price (₹/kg)' },
          ticks: {
            callback: v => formatCurrency(v)
          }
        }
      }
    }
  });
}


/* ---------------------- Dropdown loaders & event wiring ---------------------- */

async function loadStates() {
  const stateSelect = document.getElementById('state');
  if (!stateSelect) return;
  stateSelect.disabled = true;
  try {
    const payload = await fetchStates();
    if (!payload || payload.success === false) throw new Error(payload && payload.error ? payload.error : 'Failed to load states');
    const states = payload.states || (Array.isArray(payload) ? payload : []);
    stateSelect.innerHTML = '<option value="">State (optional)</option>';
    states.forEach(s => {
      if (!s) return;
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      stateSelect.appendChild(opt);
    });
    console.log('Loaded states:', states.length);
  } catch (err) {
    console.error('Error loading states:', err);
    stateSelect.innerHTML = '<option value="">State (optional)</option>';
  } finally {
    stateSelect.disabled = false;
  }
}

async function loadCommodities(state) {
  const commoditySelect = document.getElementById('commodity');
  if (!commoditySelect) return;
  commoditySelect.disabled = true;
  try {
    const payload = await fetchCommodities(state);
    if (!payload || payload.success === false) throw new Error(payload && payload.error ? payload.error : 'Failed to load commodities');
    const comms = payload.commodities || (Array.isArray(payload) ? payload : []);
    commoditySelect.innerHTML = '<option value="">Commodity (select)</option>';
    comms.forEach(c => {
      if (!c) return;
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      commoditySelect.appendChild(opt);
    });
    console.log('Loaded commodities:', comms.length);
    // auto-select first commodity (helpful for quick initial search)
    if (comms.length > 0) commoditySelect.value = comms[0];
  } catch (err) {
    console.error('Error loading commodities:', err);
    commoditySelect.innerHTML = '<option value="">Commodity (select)</option>';
  } finally {
    commoditySelect.disabled = false;
  }
}

/* ---------------------- Main DOM logic ---------------------- */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('searchForm');
  const tableContainer = document.getElementById('tableContainer');
  const searchBtn = document.getElementById('searchBtn');
  const stateSelect = document.getElementById('state');
  const commoditySelect = document.getElementById('commodity');

  // Load states then commodities
  loadStates().then(() => loadCommodities());

  // When state changes, reload commodities filtered by state
  if (stateSelect) {
    stateSelect.addEventListener('change', () => {
      const s = stateSelect.value;
      loadCommodities(s);
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const commodity = commoditySelect ? commoditySelect.value || '' : '';
      const state = stateSelect ? stateSelect.value || '' : '';

      if (!commodity) {
        tableContainer.innerHTML = '<div class="text-warning p-3">Please select a commodity.</div>';
        renderChart([]);
        return;
      }

      tableContainer.innerHTML = '<div class="text-center py-4">Loading...</div>';
      searchBtn.disabled = true;

      try {
        const res = await fetchPrices(commodity, state);

        // DEBUG: first records (open DevTools console)
        if (res && res.records) console.debug('DEBUG /market/api/prices sample:', res.records.slice(0,10));
        else console.debug('DEBUG /market/api/prices raw response:', res);

        if (!res || res.success === false) {
          tableContainer.innerHTML = `<div class="text-danger p-3">Error: ${escapeHtml(res && res.error ? res.error : 'unknown')}</div>`;
          renderChart([]);
          return;
        }

        const records = res.records || [];
        tableContainer.innerHTML = renderTable(records);
        renderChart(records);

      } catch (err) {
        tableContainer.innerHTML = `<div class="text-danger p-3">${escapeHtml(err.message)}</div>`;
        renderChart([]);
      } finally {
        searchBtn.disabled = false;
      }
    });
  }

  // Optional: choose first commodity automatically after load (user can change)
  setTimeout(() => {
    if (!commoditySelect) return;
    const firstOpt = Array.from(commoditySelect.options).find(o => o.value);
    if (firstOpt) commoditySelect.value = firstOpt.value;
  }, 900);
});
