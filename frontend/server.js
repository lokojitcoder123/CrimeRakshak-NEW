// Custom Next.js server to handle Zoho Catalyst dynamic port binding
const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const dev = process.env.NODE_ENV === 'development';
const app = next({ dev });
const handle = app.getRequestHandler();

const rawPort = process.env.X_ZOHO_CATALYST_LISTEN_PORT || process.env.PORT || '9000';
const port = parseInt(rawPort, 10);

console.log(`[Catalyst AppSail] Starting server on port: ${port} (raw env: X_ZOHO_CATALYST_LISTEN_PORT=${process.env.X_ZOHO_CATALYST_LISTEN_PORT}, PORT=${process.env.PORT})`);

app.prepare()
  .then(() => {
    const server = createServer((req, res) => {
      const parsedUrl = parse(req.url, true);
      handle(req, res, parsedUrl);
    });

    server.listen(port, '0.0.0.0', (err) => {
      if (err) {
        console.error('[Catalyst AppSail] Error listening on port:', err);
        process.exit(1);
      }
      console.log(`> Catalyst AppSail Server listening on http://0.0.0.0:${port}`);
    });

    server.on('error', (err) => {
      console.error('[Catalyst AppSail] Server error:', err);
    });
  })
  .catch((err) => {
    console.error('[Catalyst AppSail] Error during Next.js app.prepare():', err);
    process.exit(1);
  });
