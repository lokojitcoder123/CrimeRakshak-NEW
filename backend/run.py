import os
import uvicorn

if __name__ == "__main__":
    # Zoho Catalyst tells the app which port to bind to via X_ZOHO_CATALYST_LISTEN_PORT or PORT
    port_str = os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT") or os.environ.get("PORT") or "9000"
    port = int(port_str)
    print(f"Starting CrimeRakshak API server on 0.0.0.0:{port}...", flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
