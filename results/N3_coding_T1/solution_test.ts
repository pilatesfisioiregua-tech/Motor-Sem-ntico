import server from "./solution.ts";
import { assertEquals } from "https://deno.land/std/assert/mod.ts";

Deno.test("Valid POST request with metrics and thresholds", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: 85, timestamp: "2023-01-01T00:00:00Z" },
      { name: "memory", value: 70, timestamp: "2023-01-01T00:00:00Z" },
      { name: "disk", value: 95, timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {
      cpu: { warn: 80, critical: 90 },
      memory: { warn: 75, critical: 90 },
    },
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.alerts.length, 3);
  assertEquals(data.alerts[0].status, "warn");
  assertEquals(data.alerts[1].status, "ok");
  assertEquals(data.alerts[2].status, "unknown");
  assertEquals(data.summary, { total: 3, critical: 0, warn: 1, ok: 1, unknown: 1 });
  assertEquals(data.worst, "warn");
});

Deno.test("Empty body returns 400", async () => {
  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "",
  }));

  assertEquals(res.status, 400);
  const data = await res.json();
  assertEquals(data.error, "Request body cannot be empty");
});

Deno.test("Invalid metrics (not array) returns 400", async () => {
  const body = {
    metrics: "not an array",
    thresholds: {},
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.status, 400);
  const data = await res.json();
  assertEquals(data.error, "'metrics' must be an array");
});

Deno.test("Unknown thresholds return 'unknown' status", async () => {
  const body = {
    metrics: [
      { name: "unknown_metric", value: 100, timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {
      cpu: { warn: 80, critical: 90 },
    },
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.alerts[0].status, "unknown");
  assertEquals(data.alerts[0].threshold, null);
});

Deno.test("CORS headers are present in responses", async () => {
  const body = {
    metrics: [],
    thresholds: {},
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(res.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(res.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Worst status calculation", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: 95, timestamp: "2023-01-01T00:00:00Z" },
      { name: "memory", value: 85, timestamp: "2023-01-01T00:00:00Z" },
      { name: "disk", value: 70, timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {
      cpu: { warn: 80, critical: 90 },
      memory: { warn: 80, critical: 90 },
      disk: { warn: 75, critical: 90 },
    },
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.status, 200);
  const data = await res.json();
  assertEquals(data.worst, "critical");
});

Deno.test("OPTIONS request returns CORS headers", async () => {
  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "OPTIONS",
  }));

  assertEquals(res.status, 200);
  assertEquals(res.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(res.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(res.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Non-JSON Content-Type returns 400", async () => {
  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: "not json",
  }));

  assertEquals(res.status, 400);
  const data = await res.json();
  assertEquals(data.error, "Content-Type must be application/json");
});

Deno.test("Invalid metric format returns 400", async () => {
  const body = {
    metrics: [
      { name: "cpu", value: "not a number", timestamp: "2023-01-01T00:00:00Z" },
    ],
    thresholds: {},
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.status, 400);
  const data = await res.json();
  assertEquals(data.error, "Invalid metric format");
});

Deno.test("Invalid threshold format returns 400", async () => {
  const body = {
    metrics: [],
    thresholds: {
      cpu: { warn: "not a number", critical: 90 },
    },
  };

  const res = await server.fetch(new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));

  assertEquals(res.status, 400);
  const data = await res.json();
  assertEquals(data.error, "Invalid threshold format for metric cpu");
});