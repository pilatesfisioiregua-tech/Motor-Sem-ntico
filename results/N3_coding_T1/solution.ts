const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
} as const;

const STATUS_PRIORITY = {
  unknown: 0,
  ok: 1,
  warn: 2,
  critical: 3,
} as const;

type Status = keyof typeof STATUS_PRIORITY;

interface Metric {
  name: string;
  value: number;
  timestamp: string;
}

interface Thresholds {
  [metricName: string]: {
    warn: number;
    critical: number;
  };
}

interface Alert {
  name: string;
  value: number;
  status: "critical" | "warn" | "ok" | "unknown";
  threshold: number | null;
}

interface Summary {
  total: number;
  critical: number;
  warn: number;
  ok: number;
  unknown: number;
}

interface ResponseBody {
  alerts: Alert[];
  summary: Summary;
  worst: "critical" | "warn" | "ok" | "unknown";
}

class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

export default {
  async fetch(req: Request): Promise<Response> {
    if (req.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (req.method !== "POST") {
      return createErrorResponse("Method Not Allowed", 405);
    }

    const contentType = req.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return createErrorResponse("Content-Type must be application/json", 400);
    }

    try {
      const bodyText = await req.text();
      if (bodyText === "") {
        throw new ValidationError("Request body cannot be empty");
      }
      const body = JSON.parse(bodyText);
      const { metrics, thresholds } = validateRequestBody(body);

      const alerts = metrics.map(metric => {
        const { status, threshold } = evaluateMetric(metric, thresholds);
        return {
          name: metric.name,
          value: metric.value,
          status,
          threshold,
        };
      });

      const summary = calculateSummary(alerts);
      const worst = determineWorstStatus(alerts);

      return createJsonResponse({ alerts, summary, worst });
    } catch (error) {
      if (error instanceof ValidationError) {
        return createErrorResponse(error.message, 400);
      }
      console.error("Unexpected error:", error);
      return createErrorResponse("Internal Server Error", 500);
    }
  },
};

function validateRequestBody(body: unknown): { metrics: Metric[]; thresholds: Thresholds } {
  if (!body || typeof body !== "object") {
    throw new ValidationError("Request body cannot be empty");
  }

  const { metrics, thresholds } = body as { metrics: unknown; thresholds: unknown };

  if (!Array.isArray(metrics)) {
    throw new ValidationError("'metrics' must be an array");
  }

  for (const metric of metrics) {
    if (
      typeof metric !== "object" ||
      metric === null ||
      typeof metric.name !== "string" ||
      typeof metric.value !== "number" ||
      typeof metric.timestamp !== "string"
    ) {
      throw new ValidationError("Invalid metric format");
    }
  }

  if (typeof thresholds !== "object" || thresholds === null) {
    throw new ValidationError("'thresholds' must be an object");
  }

  // Validate thresholds structure
  for (const [metricName, threshold] of Object.entries(thresholds)) {
    if (typeof metricName !== "string") {
      throw new ValidationError("Threshold keys must be strings");
    }
    if (
      typeof threshold !== "object" ||
      threshold === null ||
      typeof threshold.warn !== "number" ||
      typeof threshold.critical !== "number"
    ) {
      throw new ValidationError(`Invalid threshold format for metric ${metricName}`);
    }
  }

  return { metrics: metrics as Metric[], thresholds: thresholds as Thresholds };
}

function evaluateMetric(
  metric: Metric,
  thresholds: Thresholds
): { status: Alert["status"]; threshold: number | null } {
  const metricThresholds = thresholds[metric.name];

  if (!metricThresholds) {
    return { status: "unknown", threshold: null };
  }

  const { warn, critical } = metricThresholds;

  if (metric.value > critical) {
    return { status: "critical", threshold: critical };
  }
  if (metric.value > warn) {
    return { status: "warn", threshold: warn };
  }
  return { status: "ok", threshold: warn };
}

function calculateSummary(alerts: Alert[]): Summary {
  return alerts.reduce(
    (summary, alert) => {
      summary.total++;
      summary[alert.status]++;
      return summary;
    },
    { total: 0, critical: 0, warn: 0, ok: 0, unknown: 0 } as Summary
  );
}

function determineWorstStatus(alerts: Alert[]): ResponseBody["worst"] {
  if (alerts.length === 0) return "unknown";

  let worst: Status = "unknown";
  for (const alert of alerts) {
    if (STATUS_PRIORITY[alert.status] > STATUS_PRIORITY[worst]) {
      worst = alert.status;
    }
  }
  return worst;
}

function createJsonResponse(body: ResponseBody, status: number = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...CORS_HEADERS,
      "Content-Type": "application/json",
    },
  });
}

function createErrorResponse(message: string, status: number = 400): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      ...CORS_HEADERS,
      "Content-Type": "application/json",
    },
  });
}