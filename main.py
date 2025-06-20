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
    parser = argparse.ArgumentParser(description="Generar configuración Nginx + SSL Certbot para Reflex.")
    
    # Orden deseado
    parser.add_argument("--email", required=True, help="Email para Let's Encrypt (certbot)")
    parser.add_argument("--server", required=True, help="Dominio principal (ej: server-demo.lat)")
    parser.add_argument("--subdomain", action="store_true", help="Indica si se usará un subdominio")
    parser.add_argument("--name_subdomain", help="Nombre del subdominio (ej: app)")

    args = parser.parse_args()

    email = args.email
    server_name = args.server
    subdomain = args.subdomain
    name_subdomain = args.name_subdomain

    if subdomain and not name_subdomain:
        print("❌ Error: Si usas --subdomain, debes especificar --name_subdomain")
        sys.exit(1)

    config = generate_nginx_config(server_name, subdomain, name_subdomain)
    filename = f"/etc/nginx/sites-available/{server_name if not subdomain else name_subdomain + '.' + server_name}"

    with open(filename, "w") as f:
        f.write(config)
    print(f"✔️ Archivo generado: {filename}")

    symlink = f"/etc/nginx/sites-enabled/{os.path.basename(filename)}"
    if not os.path.exists(symlink):
        os.symlink(filename, symlink)
        print(f"🔗 Symlink creado: {symlink}")
    else:
        print(f"🔁 Symlink ya existe: {symlink}")

    print("🔍 Verificando configuración de Nginx...")
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        subprocess.run(["systemctl", "reload", "nginx"])
        print("✅ Nginx recargado.")
    else:
        print("❌ Error en configuración. Nginx no recargado.")
        print(result.stderr)
        sys.exit(1)

    print("🔐 Ejecutando Certbot...")
    if subdomain:
        domain = f"{name_subdomain}.{server_name}.com"
        certbot_cmd = [
            "certbot", "certonly", "--nginx",
            "--non-interactive", "--agree-tos",
            "--email", email,
            "-d", domain
        ]
    else:
        certbot_cmd = [
            "certbot", "certonly", "--nginx",
            "--non-interactive", "--agree-tos",
            "--email", email,
            "-d", f"{server_name}.com",
            "-d", f"www.{server_name}.com"
        ]

    subprocess.run(certbot_cmd)
    print("✅ Certbot ejecutado.")

    print("🛠️  Configurando auto-renovación de certificados...")
    cron_job = "0 0,12 * * * /usr/bin/certbot renew --quiet"
    cron_file = "/etc/cron.d/certbot-renew"

    with open(cron_file, "w") as f:
        f.write(f"{cron_job}\n")

    subprocess.run(["chmod", "644", cron_file])
    print("✅ Auto-renovación configurada con cron.")

if __name__ == "__main__":
    main()