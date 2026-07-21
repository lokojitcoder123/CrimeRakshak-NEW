import os
import uvicorn

if __name__ == "__main__":
    # Zoho Catalyst tells the app which port to bind to via X_ZOHO_CATALYST_LISTEN_PORT
    port = int(os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT", 9000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
