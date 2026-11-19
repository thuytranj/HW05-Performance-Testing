// Generated for HW05 on 2026-11-19T17:30:17.435277+07:00
import workflow, { makeOptions } from './lib/workflow.js';
import { spikeReport, formatConsoleSummary } from './lib/reports.js';
export const options = makeOptions('Spike');
export { setup, teardown } from './lib/workflow.js';
export default workflow;

export function handleSummary(data) {
  return {
    stdout: formatConsoleSummary(data, 'EShop Spike'),
    [__ENV.REPORT_PATH || 'reports/spike/spike_breakdown.html']: spikeReport(data),
  };
}
