import server from "./solution.ts";
import { assertEquals } from "https://deno.land/std/assert/mod.ts";

Deno.test("Valid POST request processes metrics correctly", async () => {
  const metrics = [
    { name: "cpu", value: 95, timestamp: "2023-01-01T00:00:00Z" },
    { name: "mem", value: 80, timestamp: "2023-01-01T00:00:00Z" },
    { name: "disk", value: 40, timestamp: "2023-01-01T00:00:00Z" },
  ];
  const thresholds = {
    cpu: { warn: 80, critical: 90 },
    mem: { warn: 70, critical: 85 },
  };
  const body = { metrics, thresholds };
  const request = new Request("https://api.example.com/detect", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });
  const response = await server.fetch(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(response.headers.get("Access-Control-Allow-Headers"), "Content-Type");

  const expectedAlerts = [
    { name: "cpu", value: 95, status: "critical", threshold: 90 },
    { name: "mem", value: 80, status: "warn", threshold: 70 },
    { name: "disk", value: 40, status: "unknown", threshold: null },
  ];
  assertEquals(data.alerts, expectedAlerts);

  const expectedSummary = {
    total: 3,
    critical: 1,
    warn: 1,
    ok: 0,
    unknown: 1,
  };
  assertEquals(data.summary, expectedSummary);

  assertEquals(data.worst, "critical");
});

Deno.test("Empty body returns 400 error", async () => {
  const request = new Request("https://api.example.com/detect", {
    method: "POST",
  });
  const response = await server.fetch(request);
  const data = await response.json();

  assertEquals(response.status, 400);
  assertEquals(data.error, "Empty or invalid request body");
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(response.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Metrics not an array returns 400 error", async () => {
  const body = {
    metrics: "not an array",
    thresholds: {},
  };
  const request = new Request("https://api.example.com/detect", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });
  const response = await server.fetch(request);
  const data = await response.json();

  assertEquals(response.status, 400);
  assertEquals(data.error, "metrics must be an array");
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(response.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Metric without threshold has status unknown", async () => {
  const metrics = [
    { name: "unknown_metric", value: 50, timestamp: "2023-01-01T00:00:00Z" },
  ];
  const thresholds = {};
  const body = { metrics, thresholds };
  const request = new Request("https://api.example.com/detect", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });
  const response = await server.fetch(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts[0].status, "unknown");
  assertEquals(data.alerts[0].threshold, null);
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(response.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Worst status is correctly determined", async () => {
  // All ok
  {
    const metrics = [
      { name: "ok1", value: 10, timestamp: "2023-01-01T00:00:00Z" },
      { name: "ok2", value: 20, timestamp: "2023-01-01T00:00:00Z" },
    ];
    const thresholds = {
      ok1: { warn: 30, critical: 40 },
      ok2: { warn: 30, critical: 40 },
    };
    const body = { metrics, thresholds };
    const request = new Request("https://api.example.com/detect", {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
    const response = await server.fetch(request);
    const data = await response.json();
    assertEquals(data.worst, "none");
  }

  // Mix of statuses
  {
    const metrics = [
      { name: "critical", value: 100, timestamp: "2023-01-01T00:00:00Z" },
      { name: "warn", value: 80, timestamp: "2023-01-01T00:00:00Z" },
      { name: "ok", value: 50, timestamp: "2023-01-01T00:00:00Z" },
    ];
    const thresholds = {
      critical: { warn: 80, critical: 90 },
      warn: { warn: 70, critical: 85 },
      ok: { warn: 40, critical: 50 },
    };
    const body = { metrics, thresholds };
    const request = new Request("https://api.example.com/detect", {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
    const response = await server.fetch(request);
    const data = await response.json();
    assertEquals(data.worst, "critical");
  }

  // All unknown
  {
    const metrics = [
      { name: "unknown1", value: 100, timestamp: "2023-01-01T00:00:00Z" },
      { name: "unknown2", value: 200, timestamp: "2023-01-01T00:00:00Z" },
    ];
    const thresholds = {};
    const body = { metrics, thresholds };
    const request = new Request("https://api.example.com/detect", {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
    const response = await server.fetch(request);
    const data = await response.json();
    assertEquals(data.worst, "unknown");
  }
});

Deno.test("OPTIONS request returns 204 with CORS headers", async () => {
  const request = new Request("https://api.example.com/detect", {
    method: "OPTIONS",
  });
  const response = await server.fetch(request);

  assertEquals(response.status, 204);
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(response.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});

Deno.test("Invalid JSON body returns 400 error", async () => {
  const request = new Request("https://api.example.com/detect", {
    method: "POST",
    body: "Invalid JSON",
    headers: { "Content-Type": "application/json" },
  });
  const response = await server.fetch(request);
  const data = await response.json();

  assertEquals(response.status, 400);
  assertEquals(data.error, "Invalid JSON");
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assertEquals(response.headers.get("Access-Control-Allow-Headers"), "Content-Type");
});