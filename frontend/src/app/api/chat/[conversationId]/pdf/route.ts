// Server-side proxy for PDF export: authenticates to the FastAPI backend and
// streams back the generated conversation-transcript PDF.
import { NextRequest } from "next/server";
import { auth } from "@clerk/nextjs/server";

const getBackendUrl = () => {
  const url = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "https://crimerakshak-new.onrender.com";
  return url.replace(/\/api\/v1\/?$/, "");
};

const BACKEND_URL = getBackendUrl();

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ conversationId: string }> },
) {
  const { userId, getToken: getClerkToken } = await auth();
  if (!userId) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { conversationId } = await params;
  try {
    const token = await getClerkToken();
    let res: Response | null = null;

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60000);

        const candidate = await fetch(`${BACKEND_URL}/api/v1/chat/${conversationId}/pdf`, {
          headers: { Authorization: `Bearer ${token}` },
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
        if (attempt < 3) {
          await new Promise((r) => setTimeout(r, 2500 * attempt));
        }
      }
    }

    if (!res) {
      return Response.json({ error: "proxy failure", detail: "Backend PDF service unreachable or starting up." }, { status: 503 });
    }

    if (!res.ok) {
      const text = await res.text();
      const isHtml = text.trim().startsWith("<") || text.includes("<!DOCTYPE") || text.includes("<html");
      const detailMsg = isHtml
        ? `Backend PDF export returned status ${res.status}. Service may be waking up.`
        : text;
      return Response.json({ error: `backend ${res.status}`, detail: detailMsg }, { status: res.status });
    }
    const blob = await res.arrayBuffer();
    return new Response(blob, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="conversation_${conversationId}.pdf"`,
      },
    });
  } catch (err) {
    return Response.json({ error: "proxy failure", detail: String(err) }, { status: 500 });
  }
}
