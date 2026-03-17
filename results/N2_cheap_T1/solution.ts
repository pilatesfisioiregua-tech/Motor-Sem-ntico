// solution.ts

// ============================================================================
// Types
// ============================================================================

interface Metric {
  name: string;
  value: number;
  timestamp: string;
}

interface ThresholdConfig {
  warn: number;
  critical: number;
}

interface Thresholds {
  [metricName: string]: ThresholdConfig;
}

interface DetectionRequest {
  metrics: Metric[];
  thresholds: Thresholds;
}

interface Alert {
  name: string;
  value: number;
  status: "ok" | "warn" | "critical" | "unknown";
  threshold: number | null;
}

interface Summary {
  total: number;
  critical: number;
  warn: number;
  ok: number;
  unknown: number;
}

interface DetectionResponse {
  alerts: Alert[];
  summary: Summary;
  worst: string;
}

interface ValidationResult {
  valid: boolean;
  error?: { status: number; message: string };
}

// ============================================================================
// Constants
// ============================================================================

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const STATUS_ORDER = ["critical", "warn", "unknown", "ok", "none"] as const;
type StatusKey = (typeof STATUS_ORDER)[number];

// ============================================================================
// Main Handler
// ============================================================================

export default {
  async fetch(req: Request): Promise<Response> {
    // Handle CORS preflight
    if (req.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: CORS_HEADERS,
      });
    }

    // Only POST is allowed
    if (req.method !== "POST") {
      return createErrorResponse(405, "Method Not Allowed");
    }

    // Parse and validate request
    const bodyText = await req.text();
    if (!bodyText) {
      return createErrorResponse(400, "Empty or invalid request body");
    }

    let body: unknown;
    try {
      body = JSON.parse(bodyText);
    } catch {
      return createErrorResponse(400, "Invalid JSON");
    }

    const validation = validateRequest(body);
    if (!validation.valid) {
      return createErrorResponse(
        validation.error!.status,
        validation.error!.message
      );
    }

    // Process the request
    const { metrics, thresholds } = body as DetectionRequest;
    const alerts = processMetrics(metrics, thresholds);
    const summary = calculateSummary(alerts);
    const worst = determineWorstStatus(alerts);

    // Return response
    return createJsonResponse({ alerts, summary, worst });
  },
};

// ============================================================================
// Validation Logic
// ============================================================================

function validateRequest(body: unknown): ValidationResult {
  if (!body || typeof body !== "object") {
    return {
      valid: false,
      error: { status: 400, message: "Empty or invalid request body" },
    };
  }

  const bodyObj = body as Record<string, unknown>;

  if (!("metrics" in bodyObj)) {
    return {
      valid: false,
      error: { status: 400, message: "Missing required field: metrics" },
    };
  }

  if (!Array.isArray(bodyObj.metrics)) {
    return {
      valid: false,
      error: { status: 400, message: "metrics must be an array" },
    };
  }

  // Optional: validate thresholds structure if present
  if ("thresholds" in bodyObj && typeof bodyObj.thresholds !== "object") {
    return {
      valid: false,
      error: { status: 400, message: "thresholds must be an object" },
    };
  }

  return { valid: true };
}

// ============================================================================
// Processing Logic
// ============================================================================

function processMetrics(
  metrics: Metric[],
  thresholds: Thresholds
): Alert[] {
  return metrics.map((metric) => {
    // Validate metric structure
    if (!metric || typeof metric !== "object" || !("name" in metric) || !("value" in metric)) {
      const unsafeMetric = metric as any;
      return {
        name: unsafeMetric?.name || "unknown",
        value: unsafeMetric?.value ?? NaN,
        status: "unknown" as const,
        threshold: null,
      };
    }

    const threshold = thresholds[metric.name];
    let status: Alert["status"] = "unknown";
    let thresholdValue: number | null = null;

    if (threshold && typeof metric.value === "number") {
      if (metric.value > threshold.critical) {
        status = "critical";
        thresholdValue = threshold.critical;
      } else if (metric.value > threshold.warn) {
        status = "warn";
        thresholdValue = threshold.warn;
      } else {
        status = "ok";
        thresholdValue = threshold.warn;
      }
    }

    return {
      name: metric.name,
      value: metric.value,
      status,
      threshold: thresholdValue,
    };
  });
}

function calculateSummary(alerts: Alert[]): Summary {
  const summary: Summary = {
    total: 0,
    critical: 0,
    warn: 0,
    ok: 0,
    unknown: 0,
  };

  for (const alert of alerts) {
    summary.total++;
    if (alert.status === "critical") summary.critical++;
    else if (alert.status === "warn") summary.warn++;
    else if (alert.status === "ok") summary.ok++;
    else if (alert.status === "unknown") summary.unknown++;
  }

  return summary;
}

function determineWorstStatus(alerts: Alert[]): string {
  if (alerts.length === 0) return "none";

  // Use a Set for O(1) lookup
  const statuses = new Set(alerts.map((a) => a.status));

  for (const status of STATUS_ORDER) {
    if (status !== "none" && statuses.has(status)) {
      return status;
    }
  }

  return "none";
}

// ============================================================================
// Response Helpers
// ============================================================================

function createJsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...CORS_HEADERS,
      "Content-Type": "application/json",
    },
  });
}

function createErrorResponse(status: number, message: string): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      ...CORS_HEADERS,
      "Content-Type": "application/json",
    },
  });
}

// ============================================================================
// Tests
// ============================================================================

Deno.test("POST /detect - basic functionality", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [
        { name: "cpu", value: 85, timestamp: "2024-01-01T00:00:00Z" },
        { name: "memory", value: 45, timestamp: "2024-01-01T00:00:00Z" },
      ],
      thresholds: {
        cpu: { warn: 80, critical: 90 },
        memory: { warn: 50, critical: 70 },
      },
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts.length, 2);
  assertEquals(data.alerts[0].status, "warn");
  assertEquals(data.alerts[1].status, "ok");
  assertEquals(data.summary.total, 2);
  assertEquals(data.summary.warn, 1);
  assertEquals(data.summary.ok, 1);
  assertEquals(data.worst, "warn");
});

Deno.test("POST /detect - critical alert", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [
        { name: "cpu", value: 95, timestamp: "2024-01-01T00:00:00Z" },
      ],
      thresholds: {
        cpu: { warn: 80, critical: 90 },
      },
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts[0].status, "critical");
  assertEquals(data.summary.critical, 1);
  assertEquals(data.worst, "critical");
});

Deno.test("POST /detect - unknown status (no threshold)", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [
        { name: "disk", value: 50, timestamp: "2024-01-01T00:00:00Z" },
      ],
      thresholds: {
        cpu: { warn: 80, critical: 90 },
      },
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts[0].status, "unknown");
  assertEquals(data.summary.unknown, 1);
  assertEquals(data.worst, "unknown");
});

Deno.test("POST /detect - empty metrics array", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [],
      thresholds: {},
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts.length, 0);
  assertEquals(data.summary.total, 0);
  assertEquals(data.worst, "none");
});

Deno.test("POST /detect - empty body", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "",
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 400);
  assertEquals(data.error, "Empty or invalid request body");
});

Deno.test("POST /detect - invalid JSON", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{ invalid json }",
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 400);
  assertEquals(data.error, "Invalid JSON");
});

Deno.test("POST /detect - metrics not array", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: "not an array",
      thresholds: {},
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 400);
  assertEquals(data.error, "metrics must be an array");
});

Deno.test("POST /detect - method not allowed", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "GET",
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 405);
  assertEquals(data.error, "Method Not Allowed");
});

Deno.test("OPTIONS /detect - CORS preflight", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "OPTIONS",
  });

  const response = await handler(request);

  assertEquals(response.status, 204);
  assertEquals(response.headers.get("Access-Control-Allow-Origin"), "*");
  assertEquals(response.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
});

Deno.test("POST /detect - malformed metric object", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [
        { name: "cpu", value: 85, timestamp: "2024-01-01T00:00:00Z" },
        { name: "memory" }, // missing value
      ],
      thresholds: {
        cpu: { warn: 80, critical: 90 },
      },
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts[0].status, "warn");
  assertEquals(data.alerts[1].status, "unknown");
  assertEquals(data.summary.unknown, 1);
});

Deno.test("POST /detect - non-numeric value", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [
        { name: "cpu", value: "not a number", timestamp: "2024-01-01T00:00:00Z" },
      ],
      thresholds: {
        cpu: { warn: 80, critical: 90 },
      },
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts[0].status, "unknown");
  assertEquals(data.summary.unknown, 1);
});

Deno.test("POST /detect - thresholds not provided", async () => {
  const handler = (globalThis as any).default || (globalThis as any).fetch;
  
  const request = new Request("http://localhost/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      metrics: [
        { name: "cpu", value: 85, timestamp: "2024-01-01T00:00:00Z" },
      ],
    }),
  });

  const response = await handler(request);
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.alerts[0].status, "unknown");
  assertEquals(data.summary.unknown, 1);
});

// Helper function for assertions (since Deno.test doesn't provide assertEquals by default)
function assertEquals(actual: unknown, expected: unknown, msg?: string) {
  if (actual !== expected) {
    throw new Error(
      msg || `Assertion failed: ${JSON.stringify(actual)} !== ${JSON.stringify(expected)}`
    );
  }
}