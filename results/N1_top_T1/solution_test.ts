import server from "./solution.ts";
import { assertEquals } from "https://deno.land/std/assert/mod.ts";

Deno.test("Valid POST request with metrics and thresholds", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: 95, timestamp: "2023-01-01T00:00:00Z" },
      { name: "mem", value: 85, timestamp: "2023-01-01T00:00:00Z" },
      { name: "disk", value: 70, timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {
      cpu: { warn: 80, critical: 90 },
      mem: { warn: 75, critical: 85 },
    },
  };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.alerts.length, 3);
  assertEquals(data.alerts[0].status, "critical");
  assertEquals(data.alerts[0].threshold, 90);
  assertEquals(data.alerts[1].status, "warn");
  assertEquals(data.alerts[1].threshold, 75);
  assertEquals(data.alerts[2].status, "unknown");
  assertEquals(data.summary.total, 3);
  assertEquals(data.summary.critical, 1);
  assertEquals(data.summary.warn, 1);
  assertEquals(data.summary.unknown, 1);
  assertEquals(data.worst, "critical");
  const headers = res.headers;
  assertEquals(headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(headers.get("Access-Control-Allow-Headers"), "Content-Type");
  assertEquals(headers.get("Content-Type"), "application/json");
});

Deno.test("Empty body returns 400", async () => {
  const req = new Request("", { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 400);
  const error = await res.json();
  assertEquals(error.error, "Invalid JSON");
  const headers = res.headers;
  assertEquals(headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(headers.get("Content-Type"), "application/json");
});

Deno.test("Invalid metrics type returns 400", async () => {
  const body = { metrics: "not-array", thresholds: {} };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 400);
  const error = await res.json();
  assertEquals(error.error, "metrics must be an array");
  const headers = res.headers;
  assertEquals(headers.get("Access-Control-Allow-Origin"), "*");
});

Deno.test("Invalid metric format returns 400", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: 90 }, // missing timestamp
    ],
    thresholds: {},
  };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 400);
  const error = await res.json();
  assertEquals(error.error, "Invalid metric format");
  const headers = res.headers;
  assertEquals(headers.get("Access-Control-Allow-Origin"), "*");
});

Deno.test("Metric without threshold is unknown", async () => {
  const body = {
    metrics: [
      { name: "disk", value: 50, timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {},
  };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.alerts[0].status, "unknown");
  assertEquals(data.alerts[0].threshold, null);
  assertEquals(data.summary.unknown, 1);
  assertEquals(data.worst, "unknown");
});

Deno.test("Worst status calculation", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: 92, timestamp: "2023-01-01T00:00:00Z" }, // critical
      { name: "mem", value: 82, timestamp: "2023-01-01T00:00:00Z" }, // warn
      { name: "net", value: 60, timestamp: "2023-01-01T00:00:00Z" }, // ok
    ],
    thresholds: {
      cpu: { warn: 80, critical: 90 },
      mem: { warn: 80, critical: 85 },
    },
  };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.worst, "critical");
});

Deno.test("Worst status with multiple statuses", async () => {
  const body = {
    metrics: [
      { name: "a", value: 30, timestamp: "2023-01-01T00:00:00Z" }, // ok
      { name: "b", value: 85, timestamp: "2023-01-01T00:00:00Z" }, // warn
      { name: "c", value: 95, timestamp: "2023-01-01T00:00:00Z" }, // critical
    ],
    thresholds: {
      a: { warn: 40, critical: 50 },
      b: { warn: 80, critical: 90 },
      c: { warn: 80, critical: 90 },
    },
  };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.worst, "critical");
});

Deno.test("OPTIONS request returns 200 with CORS headers", async () => {
  const req = new Request("http://example.com", { method: "OPTIONS" });
  const res = await server.fetch(req);
  assertEquals(res.status, 200);
  const headers = res.headers;
  assertEquals(headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Non-POST method returns 405", async () => {
  const req = new Request("http://example.com", { method: "GET" });
  const res = await server.fetch(req);
  assertEquals(res.status, 405);
  const headers = res.headers;
  assertEquals(headers.get("Allow"), "POST, OPTIONS");
  assertEquals(headers.get("Access-Control-Allow-Origin"), "*");
});

Deno.test("Alert threshold value for ok status is warn", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: 70, timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {
      cpu: { warn: 80, critical: 90 },
    },
  };
  const req = new Request(JSON.stringify(body), { method: "POST" });
  const res = await server.fetch(req);
  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.alerts[0].status, "ok");
  assertEquals(data.alerts[0].threshold, 80);
});