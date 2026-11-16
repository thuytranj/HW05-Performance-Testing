function escape(value) { return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function values(data, name) { return data.metrics[name] ? data.metrics[name].values : null; }

export function spikeReport(data) {
  const columns = ['min', 'avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'];
  const groups = [['01_auth_login','login'], ['02_read_search','search'], ['03_read_detail','detail'],
    ['04_transaction_cart','cart'], ['05_transaction_checkout','checkout']];
  const table = groups.map(([group, metric]) => {
    const v = values(data, `step_${metric}_ms`);
    return `<tr><th>${group}</th>${columns.map(c => `<td>${v && v[c] !== undefined ? Number(v[c]).toFixed(3) : 'N/A'}</td>`).join('')}</tr>`;
  }).join('');
  const statuses = {};
  function visit(group) {
    for (const c of Object.values(group.checks || {})) {
      const match = /^HTTP status (\d+)$/.exec(c.name);
      if (match) statuses[match[1]] = (statuses[match[1]] || 0) + c.passes + c.fails;
    }
    for (const child of Object.values(group.groups || {})) visit(child);
  }
  visit(data.root_group || {});
  const statusRows = Object.entries(statuses).sort().map(([status, n]) =>
    `<tr><td>${escape(status)}</td><td>${n}</td><td>${Number(status) === 0 || Number(status) >= 400 ? 'HTTP/network error' : 'Response'}</td></tr>`).join('');
  const recovery = values(data, 'http_req_duration{phase:recovery}');
  return `<!doctype html><html lang="en"><meta charset="utf-8"><title>EShop Spike Breakdown</title>
<style>body{font:16px system-ui;max-width:1100px;margin:40px auto;color:#172033}table{border-collapse:collapse;width:100%;margin:24px 0}td,th{padding:12px;border:1px solid #cbd5e1;text-align:right}th:first-child,td:first-child{text-align:left}h1{color:#175e75}</style>
<h1>EShop Spike: group and HTTP status breakdown</h1>
<p>Durations are milliseconds. Missing observations are N/A, never zero. HTTP 200 can still fail business checks.</p>
<table><tr><th>group()</th>${columns.map(c => `<th>${escape(c)}</th>`).join('')}</tr>${table}</table>
<h2>Exact HTTP status counts across VUs</h2><table><tr><th>Status</th><th>Requests</th><th>Category</th></tr>${statusRows || '<tr><td colspan="3">No observations</td></tr>'}</table>
<p>Post-spike recovery p95: ${recovery ? escape(recovery['p(95)']) + ' ms' : 'N/A (smoke or no recovery samples)'}</p>
<h2>Business outcome</h2><pre>${escape(JSON.stringify({flow_success: values(data, 'flow_success'), flow_completed: values(data, 'flow_completed')}, null, 2))}</pre>
<p>Raw CSV and independently recomputed analysis remain the evidence for AI verification.</p></html>`;
}
