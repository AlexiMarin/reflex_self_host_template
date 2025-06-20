
import sys

def generate_nginx_config(server_name):
    return f"""server {{
    listen 80;
    server_name {server_name}.com www.{server_name}.com;

    # Rutas internas de Reflex que deben ir al backend
    location /_event/ {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
    location /_upload/ {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
    location /ping {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
    # Sirve el frontend desde el servidor que corre en 3000
    location / {{
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""

if len(sys.argv) < 2:
    # print("Uso: python3 main.py <server_name>")
    sys.exit(1)

server_name = sys.argv[1]
filename = f"/etc/nginx/sites-available/{server_name}"

config = generate_nginx_config(server_name)

# Escribir con permisos (requiere sudo)
with open(filename, "w") as f:
    f.write(config)

print(f"Archivo generado: {filename}")


# Usage example:
# sudo python3 main.py myserver

# This script generates an Nginx configuration file for a given server name.
# The generated file is saved in /etc/nginx/sites-available/<server_name>
# and should be linked to /etc/nginx/sites-enabled/<server_name> for it to take effect.
# After running this script, you may need to run:
# sudo ln -s /etc/nginx/sites-available/<server_name> /etc/nginx/sites-enabled/
# sudo systemctl restart nginx
# Ensure you have the necessary permissions to write to /etc/nginx/sites-available/
# and to restart the Nginx service.
# Note: This script assumes you have Python 3 installed and that you run it with appropriate permissions.
# Ensure you have the necessary permissions to write to /etc/nginx/sites-available/
# and to restart the Nginx service.