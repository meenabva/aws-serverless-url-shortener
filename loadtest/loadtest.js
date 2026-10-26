// Usage: k6 run -e API=https://<api-id>.execute-api.<region>.amazonaws.com loadtest.js
import http from "k6/http";
import { check } from "k6";

const API = __ENV.API;
const PEAK = Number(__ENV.VUS || 50);

export const options = {
  stages: [
    { duration: "30s", target: Math.ceil(PEAK / 5) },
    { duration: "1m",  target: PEAK },
    { duration: "1m",  target: PEAK },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export function setup() {
  const codes = [];
  for (let i = 0; i < 20; i++) {
    const res = http.post(
      `${API}/shorten`,
      JSON.stringify({ url: `https://example.com/page/${i}` }),
      { headers: { "Content-Type": "application/json" } }
    );
    codes.push(res.json("code"));
  }
  return { codes };
}

export default function (data) {
  const code = data.codes[Math.floor(Math.random() * data.codes.length)];
  const res = http.get(`${API}/${code}`, { redirects: 0 });
  check(res, { "status is 301": (r) => r.status === 301 });
  // Print the first few failures per virtual user to see the actual status code.
  if (res.status !== 301 && __ITER < 3) console.log(res.status, res.body);
}
