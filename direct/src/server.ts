import express from 'express';
import path from 'path';
import fs from 'fs';
import https from 'https';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const port = 3000;

// CORS middleware
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// Serve static files
app.use(express.static(path.join(__dirname, '../public')));

// Set up routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// HTTPS options
const options = {
    key: fs.readFileSync(path.join(__dirname, '../certs/localhost-key.pem')),
    cert: fs.readFileSync(path.join(__dirname, '../certs/localhost-cert.pem'))
};

https.createServer(options, app).listen(port, () => {
    console.log(`Server running at https://localhost:${port}`);
});
