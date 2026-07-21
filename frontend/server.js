// Custom Next.js server to handle Zoho Catalyst dynamic port binding
const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const app = next({ dev: false });
const handle = app.getRequestHandler();

const port = parseInt(process.env.X_ZOHO_CATALYST_LISTEN_PORT || process.env.PORT || '9000', 10);

app.prepare().then(() => {
  createServer((req, res) => {
    const parsedUrl = parse(req.url, true);
    handle(req, res, parsedUrl);
  }).listen(port, '0.0.0.0', (err) => {
    if (err) throw err;
    console.log(`> Server listening on port ${port}`);
  });
});
