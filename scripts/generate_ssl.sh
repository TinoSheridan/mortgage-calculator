#!/bin/bash

# Configuration
DOMAIN="mortgagecalc.example.com"  # Replace with your domain
COUNTRY="US"
STATE="California"
LOCALITY="San Francisco"
ORGANIZATION="Your Company"
ORGANIZATIONAL_UNIT="IT"
EMAIL="admin@example.com"
SSL_DIR="/etc/ssl"
DAYS_VALID=365

# Create directories if they don't exist
sudo mkdir -p "$SSL_DIR/private"
sudo mkdir -p "$SSL_DIR/certs"

# Generate strong DH parameters (2048 bits)
echo "Generating DH parameters (this may take a while)..."
sudo openssl dhparam -out "$SSL_DIR/certs/dhparam.pem" 2048

# Generate private key
echo "Generating private key..."
sudo openssl genrsa -out "$SSL_DIR/private/$DOMAIN.key" 2048
sudo chmod 600 "$SSL_DIR/private/$DOMAIN.key"

# Generate CSR
echo "Generating Certificate Signing Request..."
sudo openssl req -new -key "$SSL_DIR/private/$DOMAIN.key" -out "$SSL_DIR/certs/$DOMAIN.csr" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$LOCALITY/O=$ORGANIZATION/OU=$ORGANIZATIONAL_UNIT/CN=$DOMAIN/emailAddress=$EMAIL"

# Generate self-signed certificate
echo "Generating self-signed certificate..."
sudo openssl x509 -req -days $DAYS_VALID \
    -in "$SSL_DIR/certs/$DOMAIN.csr" \
    -signkey "$SSL_DIR/private/$DOMAIN.key" \
    -out "$SSL_DIR/certs/$DOMAIN.crt"

# Create symbolic links for nginx
sudo ln -sf "$SSL_DIR/certs/$DOMAIN.crt" "$SSL_DIR/certs/mortgage_calc.crt"
sudo ln -sf "$SSL_DIR/private/$DOMAIN.key" "$SSL_DIR/private/mortgage_calc.key"

# Set proper permissions
sudo chown -R root:root "$SSL_DIR/certs" "$SSL_DIR/private"
sudo chmod -R 644 "$SSL_DIR/certs"
sudo chmod -R 600 "$SSL_DIR/private"

echo "SSL certificate generation complete!"
echo "Certificate: $SSL_DIR/certs/$DOMAIN.crt"
echo "Private Key: $SSL_DIR/private/$DOMAIN.key"
echo "DH Parameters: $SSL_DIR/certs/dhparam.pem"

# Print certificate information
echo -e "\nCertificate Information:"
openssl x509 -in "$SSL_DIR/certs/$DOMAIN.crt" -text -noout | grep -A 2 "Validity"
