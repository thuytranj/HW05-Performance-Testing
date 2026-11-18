// Generated for HW05 on 2026-11-16T20:17:37.393394+07:00
// Requires Built-in Web Dashboard env (set automatically by ./scripts/run.sh Load):
// K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_PORT=-1 K6_WEB_DASHBOARD_EXPORT=reports/load/load_dashboard.html
import workflow, { makeOptions } from './lib/workflow.js';
export const options = makeOptions('Load');
export { setup, teardown } from './lib/workflow.js';
export default workflow;
