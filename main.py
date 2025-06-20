import sys
import os
import argparse
import subprocess

def generate_nginx_config(server_name: str, subdomain: bool = False, name_subdomain: str = None):
    return f"""server {{
    listen 80;
    {f"server_name {name_subdomain}.{server_name}.com;" if subdomain else f"server_name {server_name}.com www.{server_name}.com;"}

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
}}"""

def main():
    parser = argparse.ArgumentParser(description="Generar archivo de configuración Nginx para Reflex.")
    parser.add_argument("--server", required=True, help="Nombre base del dominio (ej: myapp)")
    parser.add_argument("--subdomain", action="store_true", help="Indica si se está usando subdominio")
    parser.add_argument("--name_subdomain", help="Nombre del subdominio (ej: admin)")

    args = parser.parse_args()

    server_name = args.server
    subdomain = args.subdomain
    name_subdomain = args.name_subdomain

    if subdomain and not name_subdomain:
        print("Error: Si usas --subdomain, debes especificar --name_subdomain")
        sys.exit(1)

    config = generate_nginx_config(server_name, subdomain, name_subdomain)
    filename = f"/etc/nginx/sites-available/{server_name if not subdomain else name_subdomain + '.' + server_name}"

    # Escribir archivo
    with open(filename, "w") as f:
        f.write(config)
    print(f"✔️ Archivo generado: {filename}")

    # Crear symlink
    symlink = f"/etc/nginx/sites-enabled/{os.path.basename(filename)}"
    if not os.path.exists(symlink):
        os.symlink(filename, symlink)
        print(f"🔗 Symlink creado: {symlink}")
    else:
        print(f"🔁 Symlink ya existe: {symlink}")

    # Verificar y recargar Nginx
    print("🔍 Verificando configuración de Nginx...")
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        subprocess.run(["systemctl", "reload", "nginx"])
        print("✅ Nginx recargado.")
    else:
        print("❌ Error en configuración. Nginx no recargado.")
        print(result.stderr)

if __name__ == "__main__":
    main()
# This script generates an Nginx configuration file for a Reflex application.
# It supports both main domain and subdomain configurations.
# It also creates a symlink in the sites-enabled directory and checks the Nginx configuration before reloading it.
# Usage:
# python main.py --server myapp --subdomain --name_subdomain admin
# Ensure you run this script with appropriate permissions to write to /etc/nginx
# and create symlinks in /etc/nginx/sites-enabled.
# Make sure to have Nginx installed and running on your system.
# Note: This script assumes you have the necessary permissions to write to /etc/nginx.
# Ensure you run this script with appropriate permissions to write to /etc/nginx
# and create symlinks in /etc/nginx/sites-enabled.
# Make sure to have Nginx installed and running on your system.
