// k6 load test for the chart API (US-53): 50 requests per second for 2 minutes,
// every request a different birth moment so the snapshot cache does not help.
// Pass when 95% of requests finish within 300 ms and fewer than 1% fail.
//
//   k6 run -e BASE_URL=https://staging.example.com/api tools/load/chart.js
//
// Run it against staging with IP_RATE_LIMITS=false, never against production.
import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    charts: { executor: "constant-arrival-rate", rate: 50, timeUnit: "1s", duration: "2m", preAllocatedVUs: 50, maxVUs: 200 },
  },
  thresholds: { http_req_duration: ["p(95)<300"], http_req_failed: ["rate<0.01"] },
};

const BASE = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const i = __ITER + __VU * 100000;
  const day = new Date(Date.UTC(1950, 0, 1) + (i % 30000) * 86400000).toISOString().slice(0, 10);
  const body = JSON.stringify({
    birth: {
      birth_date: day,
      birth_time: `${String(i % 24).padStart(2, "0")}:${String((i * 7) % 60).padStart(2, "0")}`,
      latitude: 8 + (i % 25),
      longitude: 68 + (i % 29),
      tz_name: "Asia/Kolkata",
    },
    vargas: ["D1", "D9"],
  });
  const res = http.post(`${BASE}/v1/charts`, body, { headers: { "content-type": "application/json", "X-CSRF": "1" } });
  check(res, { "status 200": (r) => r.status === 200 });
}
