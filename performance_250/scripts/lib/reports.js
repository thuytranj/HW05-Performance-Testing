function escape(value) { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function values(data, name) { return data.metrics[name] ? data.metrics[name].values : null; }
function fmt(val, digits = 3) { return val !== undefined && val !== null && Number.isFinite(Number(val)) ? Number(val).toFixed(digits) : 'N/A'; }

export function formatConsoleSummary(data, scenarioName) {
  const httpDur = values(data, 'http_req_duration');
  const httpReqs = values(data, 'http_reqs');
  const httpFail = values(data, 'http_req_failed');
  const flowSuc = values(data, 'flow_success');
  const flowComp = values(data, 'flow_completed');
  const flowProc = values(data, 'flow_processing_ms');
  const checks = values(data, 'checks');
  const lines = [
    `\n=== ${scenarioName} Summary ===`,
    `http_reqs: ${httpReqs ? httpReqs.count : 'N/A'} (${fmt(httpReqs && httpReqs.rate, 2)}/s)`,
    `http_req_duration (ms): avg=${fmt(httpDur && httpDur.avg)} med=${fmt(httpDur && httpDur.med)} p(95)=${fmt(httpDur && httpDur['p(95)'])} p(99)=${fmt(httpDur && httpDur['p(99)'])} max=${fmt(httpDur && httpDur.max)}`,
    `http_req_failed: ${httpFail ? `${(httpFail.rate * 100).toFixed(2)}%` : 'N/A'} | checks: ${checks ? `${(checks.rate * 100).toFixed(2)}%` : 'N/A'}`,
    `flow_completed: ${flowComp ? flowComp.count : 'N/A'} | flow_success: ${flowSuc ? `${(flowSuc.rate * 100).toFixed(2)}%` : 'N/A'} | flow_processing p(95): ${fmt(flowProc && flowProc['p(95)'])} ms`,
  ];
  return lines.join('\n') + '\n';
}

export function spikeReport(data) {
  const columns = ['min', 'avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'];
  const groups = [
    ['01_auth_login', 'login'],
    ['02_read_search', 'search'],
    ['03_read_detail', 'detail'],
    ['04_transaction_cart', 'cart'],
    ['05_transaction_checkout', 'checkout'],
  ];

  const checkStats = {};
  function visit(group) {
    for (const c of Object.values(group.checks || {})) {
      checkStats[c.name] = { passes: c.passes, fails: c.fails };
    }
    for (const child of Object.values(group.groups || {})) visit(child);
  }
  visit(data.root_group || {});

  const table = groups.map(([groupName, metric]) => {
    const v = values(data, `step_${metric}_ms`);
    const cs = checkStats[`${metric}: HTTP and business result`];
    const checkCol = cs ? `${cs.passes} / ${cs.fails}` : 'N/A';
    return `<tr><th>${escape(groupName)} (<code>step_${escape(metric)}_ms</code>)</th>${columns.map(c => `<td>${fmt(v && v[c])}</td>`).join('')}<td>${escape(checkCol)}</td></tr>`;
  }).join('');

  const statusMetrics = ['0', '200', '201', '400', '401', '403', '404', '500', 'other'];
  const statusRows = statusMetrics.map(code => {
    const v = values(data, `http_status_${code}`);
    const count = v ? v.count : 0;
    if (!count) return '';
    const category = code === '0'
      ? 'Network / Timeout error (status 0)'
      : code === 'other'
        ? 'Other HTTP status'
        : Number(code) >= 500
          ? 'Server error (5xx)'
          : Number(code) >= 400
            ? 'Client / Auth error (4xx)'
            : 'Success response (2xx)';
    return `<tr><td>${escape(code)}</td><td>${count}</td><td>${escape(category)}</td></tr>`;
  }).filter(Boolean).join('');

  const baseline = values(data, 'http_req_duration{phase:baseline}');
  const spike = values(data, 'http_req_duration{phase:spike}');
  const recovery = values(data, 'http_req_duration{phase:recovery}');
  const phaseRows = [
    ['Baseline (initial load)', baseline],
    ['Spike (peak load)', spike],
    ['Recovery (post-spike)', recovery],
  ].map(([label, v]) => `<tr><th>${escape(label)}</th>${columns.map(c => `<td>${fmt(v && v[c])}</td>`).join('')}</tr>`).join('');

  const locked = values(data, 'auth_locked_errors');
  const priceStr = values(data, 'price_string_anomalies');

  return `<!doctype html><html lang="en"><meta charset="utf-8"><title>EShop Spike Breakdown</title>
<style>body{font:16px system-ui;max-width:1180px;margin:40px auto;color:#172033}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{padding:10px 12px;border:1px solid #cbd5e1;text-align:right}th:first-child,td:first-child{text-align:left}h1{color:#175e75}code{background:#f1f5f9;padding:2px 5px;border-radius:4px}</style>
<h1>EShop Spike: step HTTP timing, phase comparison and status breakdown</h1>
<p>Durations are milliseconds (HTTP request timing from <code>step_*_ms</code>, excluding think-time). Missing observations are N/A, never zero.</p>
<h2>Step HTTP timing &amp; business checks</h2>
<table><tr><th>Step / Group</th>${columns.map(c => `<th>${escape(c)}</th>`).join('')}<th>Pass / Fail</th></tr>${table}</table>
<h2>Phase latency comparison</h2>
<table><tr><th>Phase</th>${columns.map(c => `<th>${escape(c)}</th>`).join('')}</tr>${phaseRows}</table>
<h2>Exact HTTP status counts across VUs</h2>
<table><tr><th>Status</th><th>Requests</th><th>Category</th></tr>${statusRows || '<tr><td colspan="3">No observations</td></tr>'}</table>
<h2>Business outcome &amp; SUT anomaly counters</h2>
<pre>${escape(JSON.stringify({
    flow_success: values(data, 'flow_success'),
    flow_completed: values(data, 'flow_completed'),
    flow_processing_ms: values(data, 'flow_processing_ms'),
    auth_locked_errors: locked ? locked.count : 0,
    price_string_anomalies: priceStr ? priceStr.count : 0,
  }, null, 2))}</pre>
<p>Raw CSV and independently recomputed analysis remain the evidence for AI verification.</p></html>`;
}
