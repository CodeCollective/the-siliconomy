docker run -it --rm \
  -p 5173:5173 \
  -v "$(pwd)":/app \
  -v /app/node_modules \
  -w /app \
  -e VITE_SSL_KEY=/certs/localhost-key.pem \
  -e VITE_SSL_CERT=/certs/localhost-cert.pem \
  -v "$(pwd)/certs":/certs:ro \
  node:23 \
  sh -c "npm update && echo 'Packages upgraded to latest allowed by package.json' && exit"
