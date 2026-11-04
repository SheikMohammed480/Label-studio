import { registerAnalytics } from "@humansignal/core";
registerAnalytics();

import "./app/App";
import "./utils/service-worker";


fetch('/api', {
  method: 'GET',
  credentials: 'include',
});
