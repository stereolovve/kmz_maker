# Guia de Deploy - AWS EC2

Guia completo para deploy da API REST Lista de Obras na AWS EC2.

## 📋 Pré-requisitos

- Instância EC2 (Ubuntu 20.04 ou 22.04 recomendado)
- Acesso SSH à instância
- Domínio ou IP público configurado
- Google Maps API Key (se usar processamento com rotas)

---

## 🚀 Passo a Passo

### 1. Conectar à EC2

```bash
ssh -i sua-chave.pem ubuntu@seu-ip-ec2
```

### 2. Atualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Instalar Dependências do Sistema

```bash
# Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# PostgreSQL (recomendado)
sudo apt install postgresql postgresql-contrib -y

# Nginx (servidor web)
sudo apt install nginx -y

# Supervisor (gerenciador de processos)
sudo apt install supervisor -y

# Git
sudo apt install git -y
```

### 4. Configurar PostgreSQL

```bash
# Acessar PostgreSQL
sudo -u postgres psql

# Criar banco e usuário
CREATE DATABASE lista_obras_db;
CREATE USER lista_obras_user WITH PASSWORD 'senha_forte_aqui';
ALTER ROLE lista_obras_user SET client_encoding TO 'utf8';
ALTER ROLE lista_obras_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE lista_obras_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE lista_obras_db TO lista_obras_user;

# Sair
\q
```

### 5. Clonar/Copiar Projeto

```bash
# Criar diretório
sudo mkdir -p /var/www/lista_obras
sudo chown $USER:$USER /var/www/lista_obras

# Copiar projeto (via git ou scp)
cd /var/www/lista_obras
# git clone seu-repositorio.git .
# OU copie os arquivos via scp
```

### 6. Configurar Ambiente Virtual

```bash
cd /var/www/lista_obras
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
nano .env
```

Cole o seguinte conteúdo (ajuste os valores):

```env
# Django Settings
SECRET_KEY=gere-uma-chave-secreta-forte-aqui-use-django-secret-key-generator
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,seu-ip-ec2

# Database PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=lista_obras_db
DB_USER=lista_obras_user
DB_PASSWORD=senha_forte_aqui
DB_HOST=localhost
DB_PORT=5432

# Google Maps API
GOOGLE_MAPS_API_KEY=sua-api-key-aqui
```

**Gerar SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 8. Executar Migrações

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Criar usuário admin
```

### 9. Configurar Gunicorn

Criar arquivo de configuração:

```bash
sudo nano /etc/supervisor/conf.d/lista_obras.conf
```

Cole:

```ini
[program:lista_obras]
directory=/var/www/lista_obras
command=/var/www/lista_obras/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/lista_obras/gunicorn.log
stderr_logfile=/var/log/lista_obras/gunicorn_error.log
```

Criar diretório de logs:

```bash
sudo mkdir -p /var/log/lista_obras
sudo chown ubuntu:ubuntu /var/log/lista_obras
```

Iniciar Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start lista_obras
sudo supervisorctl status
```

### 10. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/lista_obras
```

Cole:

```nginx
server {
    listen 80;
    server_name seu-dominio.com seu-ip-ec2;

    client_max_body_size 20M;

    location /static/ {
        alias /var/www/lista_obras/staticfiles/;
    }

    location /media/ {
        alias /var/www/lista_obras/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Ativar site:

```bash
sudo ln -s /etc/nginx/sites-available/lista_obras /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 11. Configurar Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 12. Configurar Permissões de Arquivos

```bash
sudo chown -R ubuntu:www-data /var/www/lista_obras/media
sudo chmod -R 775 /var/www/lista_obras/media
```

---

## 🔧 Manutenção

### Atualizar Código

```bash
cd /var/www/lista_obras
source venv/bin/activate

# Atualizar código (git pull ou copiar arquivos)

# Reinstalar dependências se necessário
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar aplicação
sudo supervisorctl restart lista_obras
```

### Ver Logs

```bash
# Logs do Gunicorn
tail -f /var/log/lista_obras/gunicorn.log

# Logs do Nginx
sudo tail -f /var/nginx/error.log

# Logs do Supervisor
sudo tail -f /var/log/supervisor/supervisord.log
```

### Restart Serviços

```bash
# Restart aplicação
sudo supervisorctl restart lista_obras

# Restart Nginx
sudo systemctl restart nginx
```

---

## 🔒 Configurar HTTPS (Opcional mas Recomendado)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com

# Renovação automática já está configurada
```

---

## 📊 Monitoramento

### Verificar Status

```bash
# Status da aplicação
sudo supervisorctl status lista_obras

# Status do Nginx
sudo systemctl status nginx

# Conexões PostgreSQL
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='lista_obras_db';"
```

### Backup do Banco de Dados

```bash
# Criar backup
sudo -u postgres pg_dump lista_obras_db > backup_$(date +%Y%m%d).sql

# Restaurar backup
sudo -u postgres psql lista_obras_db < backup_20240101.sql
```

---

## 🧪 Testar Deploy

Após o deploy, acesse:

- **API Swagger**: `http://seu-dominio.com/swagger/`
- **API ReDoc**: `http://seu-dominio.com/redoc/`
- **Django Admin**: `http://seu-dominio.com/admin/`

Teste os endpoints:

```bash
# Listar jobs
curl http://seu-dominio.com/api/kml/jobs/

# Upload arquivo (via Swagger UI é mais fácil)
# Acesse http://seu-dominio.com/swagger/
```

---

## ⚠️ Troubleshooting

### Aplicação não inicia

```bash
# Ver logs detalhados
sudo supervisorctl tail -f lista_obras stderr

# Verificar se porta 8000 está em uso
sudo netstat -tulpn | grep 8000
```

### Erro de permissão em media/uploads

```bash
sudo chown -R ubuntu:www-data /var/www/lista_obras/media
sudo chmod -R 775 /var/www/lista_obras/media
```

### Nginx 502 Bad Gateway

```bash
# Verificar se Gunicorn está rodando
sudo supervisorctl status lista_obras

# Restart
sudo supervisorctl restart lista_obras
sudo systemctl restart nginx
```

### Erro de conexão com banco de dados

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
sudo -u postgres psql lista_obras_db -c "SELECT 1;"
```

---

## 🔗 Integração com Sistema Existente

Para integrar com sistema Django existente:

1. **Adicione ao requirements.txt do sistema principal**:
   ```bash
   # No sistema existente
   pip install -r /caminho/lista_obras/requirements.txt
   ```

2. **Inclua o app `obras` no INSTALLED_APPS**:
   ```python
   # settings.py do sistema existente
   INSTALLED_APPS = [
       # ... apps existentes
       'obras',
   ]
   ```

3. **Inclua as URLs**:
   ```python
   # urls.py do sistema existente
   urlpatterns = [
       # ... urls existentes
       path('api/kml/', include('obras.urls')),
   ]
   ```

4. **Execute migrações**:
   ```bash
   python manage.py migrate obras
   ```

---

## 📝 Checklist Pós-Deploy

- [ ] Aplicação acessível via navegador
- [ ] Swagger funcionando
- [ ] Upload de arquivo Excel funciona
- [ ] Download de KML funciona
- [ ] Django Admin acessível
- [ ] Logs sendo gerados corretamente
- [ ] Backup de banco configurado
- [ ] HTTPS configurado (se aplicável)
- [ ] Firewall configurado
- [ ] Monitoramento configurado

---

## 📞 Suporte

Para problemas específicos, verifique:
1. Logs da aplicação
2. Logs do Nginx
3. Status do PostgreSQL
4. Permissões de arquivos/diretórios
