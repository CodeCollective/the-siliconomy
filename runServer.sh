docker run -d --restart always --name siliconomy-nginx \
  -p 8000:8000 \
  -v "$(pwd)":/app \
  -v "$(pwd)/nginx.conf":/etc/nginx/nginx.conf:ro \
  -v "$(pwd)/ssl":/certs \
  nginx
