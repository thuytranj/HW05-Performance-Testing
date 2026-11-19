// Generated for HW05 on 2026-11-19T17:30:17.435807+07:00
// Requires Built-in Web Dashboard env (set automatically by ./scripts/run.sh Soak):
// K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_PORT=-1 K6_WEB_DASHBOARD_EXPORT=reports/soak/soak_dashboard.html
import workflow, { makeOptions } from './lib/workflow.js';
export const options = makeOptions('Soak');
export { setup, teardown } from './lib/workflow.js';
export default workflow;
