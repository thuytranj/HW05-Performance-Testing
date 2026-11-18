// Generated for HW05 on 2026-11-16T20:17:37.393499+07:00
import workflow, { makeOptions } from './lib/workflow.js';
import { htmlReport } from './lib/vendor/k6-reporter.js';
import { formatConsoleSummary } from './lib/reports.js';
export const options = makeOptions('Stress');
export { setup, teardown } from './lib/workflow.js';
export default workflow;

export function handleSummary(data) {
  return {
    stdout: formatConsoleSummary(data, 'EShop Stress'),
    [__ENV.REPORT_PATH || 'reports/stress/stress_summary.html']: htmlReport(data, { title: 'EShop Stress Summary', theme: 'classic' }),
  };
}
