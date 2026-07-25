// Server-side proxy: bridges the frontend chat UI to the FastAPI /chat backend.
//
// Because the current login UI is a prototype (no real token), this route logs
// in to the backend server-side with service credentials, caches the JWT, and
// forwards the user's message to POST /api/v1/chat. The real Gemini agent,
// DuckDB crime data, citations and Kannada support all live in that backend.
//
// Optional: if the Next.js app needs to override the local FastAPI URL
//   BACKEND_URL=http://127.0.0.1:8001
import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { auth } from "@clerk/nextjs/server";

const getBackendUrl = () => {
  const url = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "https://crimerakshak-new.onrender.com";
  return url.replace(/\/api\/v1\/?$/, "");
};

const BACKEND_URL = getBackendUrl();

export async function POST(req: Request) {
  try {
    const { userId, getToken: getClerkToken } = await auth();
    if (!userId) {
      return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { message, conversation_id, language } = await req.json();
    if (!message || typeof message !== "string") {
      return Response.json({ error: "message is required" }, { status: 400 });
    }

    const token = await getClerkToken();

    let res: Response | null = null;
    let lastError: any = null;

    // Retry loop for Render cold starts (backend may take 30-50s to wake up from sleep)
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60000); // 60s timeout

        const candidate = await fetch(`${BACKEND_URL}/api/v1/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message,
            conversation_id: conversation_id ?? null,
            language: language ?? "en",
          }),
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (candidate.status >= 502 && candidate.status <= 504 && attempt < 3) {
          await new Promise((r) => setTimeout(r, 3000 * attempt));
          continue;
        }

        res = candidate;
        break;
      } catch (err) {
        lastError = err;
        if (attempt < 3) {
          await new Promise((r) => setTimeout(r, 3000 * attempt));
        }
      }
    }

    if (!res) {
      return Response.json(
        {
          error: "Backend service unreachable",
          detail: "The AI backend service is currently unreachable or starting up. Please try again in a few seconds.",
        },
        { status: 503 }
      );
    }

    if (!res.ok) {
      const text = await res.text();
      const isHtml = text.trim().startsWith("<") || text.includes("<!DOCTYPE") || text.includes("<html");
      const detailMsg = isHtml
        ? `Backend service returned status ${res.status} ${res.statusText || ""}. The service may be starting up or temporarily offline.`
        : text;
      return Response.json(
        { error: `backend error ${res.status}`, detail: detailMsg },
        { status: res.status }
      );
    }
    const data = await res.json();
    return Response.json(data);
  } catch (err) {
    return Response.json(
      { error: "proxy failure", detail: String(err) },
      { status: 500 }
    );
  }
}
