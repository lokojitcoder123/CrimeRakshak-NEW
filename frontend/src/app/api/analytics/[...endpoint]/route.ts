// Server-side proxy: bridges the frontend analytics UI to the FastAPI /analytics backend.
//
// Automatically acquires & caches a backend Bearer token and forwards any GET/POST
// queries to live DuckDB telemetry endpoints over the KSP dataset.

import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const getBackendUrl = () => {
  const url = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "https://crimerakshak-new.onrender.com";
  return url.replace(/\/api\/v1\/?$/, "");
};

const BACKEND_URL = getBackendUrl();


export async function GET(
  req: NextRequest,
  context: { params: Promise<{ endpoint: string[] }> }
) {
  try {
    const { userId, getToken: getClerkToken } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const params = await context.params;
    const path = params.endpoint.join("/");
    const searchParams = req.nextUrl.searchParams.toString();
    const targetUrl = `${BACKEND_URL}/api/v1/analytics/${path}${
      searchParams ? `?${searchParams}` : ""
    }`;

    const token = await getClerkToken();
    let res: Response | null = null;
    let lastError: any = null;

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60000);

        const candidate = await fetch(targetUrl, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          cache: "no-store",
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (candidate.status >= 502 && candidate.status <= 504 && attempt < 3) {
          await new Promise((r) => setTimeout(r, 2500 * attempt));
          continue;
        }
        res = candidate;
        break;
      } catch (err) {
        lastError = err;
        if (attempt < 3) {
          await new Promise((r) => setTimeout(r, 2500 * attempt));
        }
      }
    }

    if (!res) {
      return NextResponse.json(
        { error: "analytics proxy failure", detail: "Backend analytics service unreachable or starting up." },
        { status: 503 }
      );
    }

    if (!res.ok) {
      const text = await res.text();
      const isHtml = text.trim().startsWith("<") || text.includes("<!DOCTYPE") || text.includes("<html");
      const detailMsg = isHtml
        ? `Backend analytics returned ${res.status} ${res.statusText || ""}. Service may be waking up.`
        : text;
      return NextResponse.json(
        { error: `backend error ${res.status}`, detail: detailMsg },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "analytics proxy failure", detail: String(err) },
      { status: 500 }
    );
  }
}

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ endpoint: string[] }> }
) {
  try {
    const { userId, getToken: getClerkToken } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const params = await context.params;
    const path = params.endpoint.join("/");
    const targetUrl = `${BACKEND_URL}/api/v1/analytics/${path}`;
    const body = await req.json();

    const token = await getClerkToken();
    let res: Response | null = null;
    let lastError: any = null;

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60000);

        const candidate = await fetch(targetUrl, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (candidate.status >= 502 && candidate.status <= 504 && attempt < 3) {
          await new Promise((r) => setTimeout(r, 2500 * attempt));
          continue;
        }
        res = candidate;
        break;
      } catch (err) {
        lastError = err;
        if (attempt < 3) {
          await new Promise((r) => setTimeout(r, 2500 * attempt));
        }
      }
    }

    if (!res) {
      return NextResponse.json(
        { error: "analytics proxy failure", detail: "Backend analytics service unreachable or starting up." },
        { status: 503 }
      );
    }

    if (!res.ok) {
      const text = await res.text();
      const isHtml = text.trim().startsWith("<") || text.includes("<!DOCTYPE") || text.includes("<html");
      const detailMsg = isHtml
        ? `Backend analytics returned ${res.status} ${res.statusText || ""}. Service may be waking up.`
        : text;
      return NextResponse.json(
        { error: `backend error ${res.status}`, detail: detailMsg },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "analytics proxy POST failure", detail: String(err) },
      { status: 500 }
    );
  }
}
