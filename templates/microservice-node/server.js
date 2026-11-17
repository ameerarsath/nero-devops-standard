const http = require('http');

const PORT = process.env.PORT || 8080;

const server = http.createServer((req, res) => {
  const url = req.url;
  if (url === '/health' || url === '/actuator/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'UP', service: 'sample-node-service', timestamp: new Date().toISOString() }));
  } else if (url === '/api/info') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ name: 'sample-node-service', version: '1.0.0', runtime: process.version }));
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[sample-node-service] Server listening on port ${PORT}`);
});

process.on('SIGTERM', () => {
  console.log('[sample-node-service] Received SIGTERM, shutting down gracefully');
  server.close(() => process.exit(0));
});
