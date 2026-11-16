// Generated for HW05 on 2026-11-16T20:17:37.393593+07:00
import workflow, { makeOptions } from './lib/workflow.js';
import { spikeReport } from './lib/reports.js';
export const options = makeOptions('Spike');
export { setup, teardown } from './lib/workflow.js';
export default workflow;

export function handleSummary(data) { return { [__ENV.REPORT_PATH || 'reports/spike/spike_breakdown.html']: spikeReport(data) }; }
