import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { SharedArray } from 'k6/data';
import { Counter, Gauge, Rate, Trend } from 'k6/metrics';
import exec from 'k6/execution';
import { parseCSV } from './csv.js';

const rows = new SharedArray('eshop-e2e-csv', () => parseCSV(open('../../data/e2e_test_data.csv')));
const base = (__ENV.BASE_URL || 'http://127.0.0.1:3000').replace(/\/$/, '');
const smoke = __ENV.SMOKE === '1';
const peak = Number(__ENV.PEAK_VUS || 40);
const normal = Number(__ENV.LOAD_VUS || 10);
const soakVUs = Number(__ENV.SOAK_VUS || normal);
const soakSeconds = Number(__ENV.SOAK_SECONDS || 600);
const think = smoke ? 0 : Number(__ENV.THINK_SECONDS || 1);
const latencyBudget = Number(__ENV.P95_MS || 1500);
const errorBudget = Number(__ENV.ERROR_RATE || 0.01);
const stepNames = ['login', 'search', 'detail', 'cart', 'checkout'];
const stepTrends = Object.fromEntries(stepNames.map(name => [name, new Trend(`step_${name}_ms`, true)]));
const flowDuration = new Trend('flow_duration_ms', true);
const flowAttempts = new Counter('flow_attempts');
const flowCompleted = new Counter('flow_completed');
const flowSuccess = new Rate('flow_success');
const recoveryRequests = new Counter('recovery_requests');
const startTime = new Gauge('run_start_ms');
const endTime = new Gauge('run_end_ms');
http.setResponseCallback(http.expectedStatuses(200, 201));

export function makeOptions(kind) {
  if (![peak, normal, soakVUs].every(n => Number.isSafeInteger(n) && n >= 1)) throw new Error('VU counts must be positive integers');
  if (!Number.isFinite(think) || think < 0 || !Number.isFinite(latencyBudget) || latencyBudget <= 0 || !(errorBudget >= 0 && errorBudget < 1)) throw new Error('Invalid pacing/threshold config');
  const maxVUs = smoke ? 1 : kind === 'Load' ? normal : kind === 'Soak' ? soakVUs : peak;
  if (rows.length < 40 || rows.length < maxVUs) throw new Error(`Need >= max(40, peak VUs) unique accounts; have ${rows.length}, require ${maxVUs}`);
  if (kind === 'Soak' && !smoke && (!Number.isInteger(soakSeconds) || soakSeconds < 600 || soakSeconds > 900)) throw new Error('HW05 soak must sustain load for 600..900 seconds');
  const thresholds = {http_req_failed: [`rate<=${smoke ? 0 : errorBudget}`],
    checks: [smoke ? 'rate==1' : `rate>=${1 - errorBudget}`],
    flow_success: [smoke ? 'rate==1' : `rate>=${1 - errorBudget}`],
    flow_completed: ['count>0'], http_req_duration: [`p(95)<${latencyBudget}`]};
  for (const name of stepNames) thresholds[`step_${name}_ms`] = [`p(95)<${latencyBudget}`];
  if (kind === 'Spike' && !smoke) {
    thresholds['http_req_duration{phase:recovery}'] = [`p(95)<${latencyBudget}`];
    thresholds.recovery_requests = ['count>0'];
  }
  let scenario;
  if (smoke) scenario = {executor: 'shared-iterations', vus: 1, iterations: 1, maxDuration: '30s'};
  else if (kind === 'Load') scenario = {executor: 'ramping-vus', startVUs: 0, stages: [
    {duration: '30s', target: normal}, {duration: '2m', target: normal}, {duration: '30s', target: 0}]};
  else if (kind === 'Stress') scenario = {executor: 'ramping-vus', startVUs: 0, stages: [
    {duration: '30s', target: Math.max(1, Math.floor(peak / 4))},
    {duration: '1m', target: Math.max(1, Math.floor(peak / 2))},
    {duration: '1m', target: peak}, {duration: '1m', target: peak}, {duration: '30s', target: 0}]};
  else if (kind === 'Spike') scenario = {executor: 'ramping-vus', startVUs: 0, stages: [
    {duration: '30s', target: Math.min(normal, peak)}, {duration: '1s', target: peak},
    {duration: '1m', target: peak}, {duration: '1s', target: Math.min(normal, peak)},
    {duration: '1m', target: Math.min(normal, peak)}, {duration: '10s', target: 0}]};
  else if (kind === 'Soak') scenario = {executor: 'constant-vus', vus: soakVUs, duration: `${soakSeconds}s`};
  else throw new Error(`Unknown scenario ${kind}`);
  scenario.gracefulStop = '10s';
  if (scenario.executor === 'ramping-vus') scenario.gracefulRampDown = '10s';
  return {scenarios: {[kind.toLowerCase()]: scenario}, thresholds,
    summaryTrendStats: ['min', 'avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
    systemTags: ['status', 'method', 'name', 'group', 'scenario', 'check', 'error', 'error_code', 'expected_response'],
    discardResponseBodies: false};
}

export function setup() { startTime.add(Date.now()); recoveryRequests.add(0); }
export function teardown() { endTime.add(Date.now()); }

function phase() {
  if (__ENV.SCENARIO_TYPE !== 'Spike' || smoke) return 'main';
  const elapsed = (Date.now() - exec.scenario.startTime) / 1000;
  return elapsed >= 92 ? 'recovery' : elapsed >= 30 ? 'spike' : 'baseline';
}

function request(name, method, uri, payload, token, predicate) {
  const currentPhase = phase();
  const response = http.request(method, base + uri, payload === null ? null : JSON.stringify(payload), {
    headers: {'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {})},
    tags: {name, phase: currentPhase}, timeout: '10s', redirects: 0,
  });
  if (currentPhase === 'recovery') recoveryRequests.add(1);
  stepTrends[name].add(response.timings.duration);
  // Dynamic check names are aggregated by k6 across all VUs; JS globals are not shared.
  check(response, {[`HTTP status ${response.status}`]: r => r.status === 200 || r.status === 201});
  let body = null;
  try { body = response.json(); } catch (_) { /* check below records malformed/HTML bodies */ }
  const okay = check(response, {[`${name}: HTTP and business result`]: r =>
    (r.status === 200 || r.status === 201) && body !== null && predicate(body)});
  if (!okay) throw new Error(`${name} failed: status=${response.status}; response bodies and tokens are not logged`);
  return body;
}

export default function workflow() {
  // Never modulo accounts: modulo would silently share carts when peak exceeds data.
  const row = rows[__VU - 1];
  if (!row) throw new Error(`Missing independent account for VU ${__VU}`);
  flowAttempts.add(1); flowCompleted.add(0);
  const started = Date.now();
  let okay = false;
  try {
    let login, product;
    group('01_auth_login', () => {
      login = request('login', 'POST', '/api/login', {email: row.email, password: row.password}, null,
        b => typeof b.token === 'string' && b.token.length > 0 && b.user && b.user.email === row.email);
    });
    if (think) sleep(think);
    group('02_read_search', () => {
      request('search', 'GET', `/api/products?search=${encodeURIComponent(row.keyword)}`, null, login.token,
        b => Array.isArray(b) && b.some(p => Number(p.id) === row.productId));
    });
    if (think) sleep(think);
    group('03_read_detail', () => {
      product = request('detail', 'GET', `/api/products/${row.productId}`, null, login.token,
        b => Number(b.id) === row.productId && Number.isFinite(Number(b.price)) && Number(b.price) > 0 && typeof b.name === 'string');
    });
    if (think) sleep(think);
    group('04_transaction_cart', () => {
      request('cart', 'POST', '/api/cart', {id: product.id, name: product.name, price: Number(product.price), quantity: row.quantity},
        login.token, b => b.message === 'Added to cart');
    });
    if (think) sleep(think);
    group('05_transaction_checkout', () => {
      request('checkout', 'POST', '/api/checkout', {total_amount: Number(product.price) * row.quantity, shipping_address: row.shippingAddress},
        login.token, b => Number.isSafeInteger(b.orderId) && b.orderId > 0 && b.message === 'Checkout successful');
    });
    okay = true; flowCompleted.add(1);
  } catch (error) {
    // Bound failure output; wrong login never retries in an iteration.
    if (__ITER === 0) console.error(error.message);
  } finally {
    flowSuccess.add(okay);
    flowDuration.add(Date.now() - started);
  }
  if (think) sleep(think);
}
