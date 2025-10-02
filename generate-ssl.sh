#!/bin/bash

# Create SSL directory
mkdir -p /etc/nginx/ssl

# Generate self-signed SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "✅ SSL certificates generated successfully"
echo "📍 Certificate: /etc/nginx/ssl/cert.pem"
echo "🔑 Private Key: /etc/nginx/ssl/key.pem"
