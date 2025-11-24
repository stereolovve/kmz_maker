# Guia Completo de Deploy - kmz.perplan.tech na EC2

Deploy completo do sistema KML como subdomínio em servidor EC2 compartilhado com o sistema principal Perplan.

## 📁 Arquivos de Configuração Prontos

Este repositório inclui templates prontos na pasta `deploy/`:
- `kmz.conf` - Configuração Supervisor
- `kmz.perplan.tech.conf` - Configuração Nginx
- `deploy.sh` - Script de deploy automatizado
- `README.md` - Documentação dos arquivos

Consulte `deploy/README.md` para mais detalhes sobre cada arquivo.

---

## 📋 Pré-requisitos

- ✅ Servidor EC2 já configurado (rodando perplan.tech)
- ✅ Nginx instalado
- ✅ Supervisor instalado
- ✅ Python 3.10+ instalado
- ✅ PostgreSQL instalado (ou usar SQLite)
- ✅ Acesso SSH à EC2
- ✅ Domínio perplan.tech configurado na Hostinger
- ✅ Certbot instalado (para SSL)

---

## 🚀 PARTE 1: Criar Repositório no GitHub

### 1.1. Criar Novo Repositório

```bash
# No seu computador local (onde está o projeto)
cd C:\Users\lucas.melo\lista_obras

# Inicializar git (se ainda não foi)
git init

# Criar repositório no GitHub
# Acesse: https://github.com/new
# Nome: lista-obras-kmz
# Descrição: Sistema de geração de KML para obras rodoviárias
# Visibilidade: Private (ou Public)
# NÃO marque "Initialize with README"
```

### 1.2. Preparar Arquivos para Commit

```bash
# Adicionar arquivos
git add .

# Fazer commit inicial
git commit -m "Initial commit: Sistema KML gerador"

# Adicionar remote (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/lista-obras-kmz.git

# Push para GitHub
git branch -M main
git push -u origin main
```

### 1.3. Verificar

Acesse `https://github.com/SEU_USUARIO/lista-obras-kmz` e confir me que todos os arquivos estão lá.

---

## 🖥️ PARTE 2: Configurar na EC2

### 2.1. Conectar via SSH

```bash
# Substitua pelo seu IP e chave
ssh -i sua-chave.pem ubuntu@IP_DA_EC2

# Ou se já tem alias configurado
ssh perplan-ec2
```

### 2.2. Navegar e Clonar Repositório

```bash
# Ir para diretório de aplicações
cd /var/www

# Clonar repositório
sudo git clone https://github.com/SEU_USUARIO/lista-obras-kmz.git kmz

# Dar permissões ao usuário ubuntu
sudo chown -R ubuntu:ubuntu /var/www/kmz

# Entrar no diretório
cd /var/www/kmz
```

### 2.3. Criar Ambiente Virtual

```bash
# Criar virtualenv
python3 -m venv venv

# Ativar virtualenv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

### 2.4. Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
nano .env
```

Cole o seguinte conteúdo (ajuste os valores):

```env
# Django Settings
SECRET_KEY=GERE_UMA_CHAVE_SECRETA_FORTE_AQUI
DEBUG=False
ALLOWED_HOSTS=kmz.perplan.tech,IP_DA_EC2

# Database (usar PostgreSQL do Perplan ou SQLite)
# Opção 1: PostgreSQL (compartilhado)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=kmz_db
DB_USER=kmz_user
DB_PASSWORD=senha_forte_aqui
DB_HOST=localhost
DB_PORT=5432

# Opção 2: SQLite (mais simples)
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=/var/www/kmz/db.sqlite3

# Google Maps API
GOOGLE_MAPS_API_KEY=sua-api-key-aqui
```

**Para gerar SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Salve com `Ctrl+O`, Enter, `Ctrl+X`.

### 2.5. Criar Banco de Dados (se PostgreSQL)

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar banco e usuário
CREATE DATABASE kmz_db;
CREATE USER kmz_user WITH PASSWORD 'senha_forte_aqui';
ALTER ROLE kmz_user SET client_encoding TO 'utf8';
ALTER ROLE kmz_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE kmz_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE kmz_db TO kmz_user;

# Sair
\q
```

### 2.6. Executar Migrações

```bash
# Certificar que está no venv
source /var/www/kmz/venv/bin/activate

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar superusuário (opcional)
python manage.py createsuperuser
```

### 2.7. Configurar Permissões de Diretórios

```bash
# Criar diretórios de media
sudo mkdir -p /var/www/kmz/media/{uploads,outputs,logs}

# Permissões corretas
sudo chown -R ubuntu:www-data /var/www/kmz/media
sudo chmod -R 775 /var/www/kmz/media

# Permissões de static
sudo chown -R ubuntu:www-data /var/www/kmz/staticfiles
sudo chmod -R 755 /var/www/kmz/staticfiles
```

### 2.8. Testar Localmente

```bash
# Testar se funciona
python manage.py runserver 0.0.0.0:8001

# Em outro terminal, teste
curl http://localhost:8001

# Se funcionar, pressione Ctrl+C para parar
```

---

## 📦 PARTE 3: Configurar Supervisor

### 3.1. Criar Arquivo de Configuração

**Opção A: Copiar do repositório (recomendado)**

```bash
# Copiar template do repositório
sudo cp /var/www/kmz/deploy/kmz.conf /etc/supervisor/conf.d/
```

**Opção B: Criar manualmente**

```bash
sudo nano /etc/supervisor/conf.d/kmz.conf
```

Cole o seguinte conteúdo:

```ini
[program:kmz]
directory=/var/www/kmz
command=/var/www/kmz/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8001 --workers 2 --timeout 120 --access-logfile /var/log/kmz/access.log --error-logfile /var/log/kmz/error.log
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/kmz/gunicorn.log
stderr_logfile=/var/log/kmz/gunicorn_error.log
environment=PATH="/var/www/kmz/venv/bin"
```

Salve com `Ctrl+O`, Enter, `Ctrl+X`.

### 3.2. Criar Diretório de Logs

```bash
sudo mkdir -p /var/log/kmz
sudo chown ubuntu:ubuntu /var/log/kmz
```

### 3.3. Iniciar Serviço

```bash
# Reler configurações
sudo supervisorctl reread

# Atualizar supervisor
sudo supervisorctl update

# Iniciar serviço
sudo supervisorctl start kmz

# Verificar status
sudo supervisorctl status kmz

# Deve mostrar: kmz RUNNING pid XXXXX, uptime X:XX:XX
```

### 3.4. Ver Logs (se houver problemas)

```bash
sudo supervisorctl tail -f kmz stderr
# ou
sudo tail -f /var/log/kmz/gunicorn_error.log
```

---

## 🌐 PARTE 4: Configurar Nginx

### 4.1. Criar Configuração do Site

**Opção A: Copiar do repositório (recomendado)**

```bash
# Copiar template do repositório
sudo cp /var/www/kmz/deploy/kmz.perplan.tech.conf /etc/nginx/sites-available/kmz.perplan.tech
```

**Opção B: Criar manualmente**

```bash
sudo nano /etc/nginx/sites-available/kmz.perplan.tech
```

Cole o seguinte conteúdo:

```nginx
server {
    listen 80;
    server_name kmz.perplan.tech;

    client_max_body_size 20M;

    # Logs
    access_log /var/log/nginx/kmz_access.log;
    error_log /var/log/nginx/kmz_error.log;

    # Arquivos estáticos
    location /static/ {
        alias /var/www/kmz/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Arquivos de media (uploads, outputs, logs)
    location /media/ {
        alias /var/www/kmz/media/;
        expires 1d;
    }

    # Proxy para Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

Salve com `Ctrl+O`, Enter, `Ctrl+X`.

### 4.2. Habilitar Site

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/kmz.perplan.tech /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Deve mostrar: syntax is ok
#              test is successful

# Recarregar Nginx
sudo systemctl reload nginx
```

### 4.3. Verificar Nginx Status

```bash
sudo systemctl status nginx

# Deve mostrar: active (running)
```

---

## 🌍 PARTE 5: Configurar DNS na Hostinger

### 5.1. Acessar Painel Hostinger

1. Acesse: https://hpanel.hostinger.com/
2. Login com suas credenciais
3. Vá em **Domínios**
4. Clique em **perplan.tech**

### 5.2. Adicionar Registro DNS

1. Clique em **DNS / Registros DNS**
2. Role até **Adicionar Registro**
3. Preencha:

```
Tipo: A
Nome: kmz
Aponta para: IP_DA_SUA_EC2
TTL: 3600 (ou deixe padrão)
```

4. Clique em **Adicionar Registro**

### 5.3. Aguardar Propagação

```bash
# No seu computador local, teste (aguarde 5-30 minutos)
nslookup kmz.perplan.tech

# Deve retornar o IP da EC2

# Ou use
dig kmz.perplan.tech

# Teste no navegador (sem SSL ainda)
http://kmz.perplan.tech
```

---

## 🔒 PARTE 6: Configurar SSL (HTTPS)

### 6.1. Instalar Certbot (se não estiver instalado)

```bash
# Verificar se já está instalado
certbot --version

# Se não estiver, instalar
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### 6.2. Obter Certificado SSL

```bash
# Gerar certificado
sudo certbot --nginx -d kmz.perplan.tech

# Siga as instruções:
# 1. Digite seu email
# 2. Aceite os termos (Y)
# 3. Compartilhar email com EFF (opcional)
# 4. Certbot vai automaticamente configurar o Nginx

# Teste a renovação automática
sudo certbot renew --dry-run
```

### 6.3. Verificar Configuração HTTPS

```bash
# Nginx foi atualizado automaticamente pelo Certbot
# Verificar
sudo nano /etc/nginx/sites-available/kmz.perplan.tech

# Deve ter blocos para porta 443 (HTTPS) adicionados

# Recarregar Nginx
sudo systemctl reload nginx
```

### 6.4. Testar HTTPS

Acesse no navegador:
```
https://kmz.perplan.tech
```

Deve carregar com cadeado verde!

---

## ✅ PARTE 7: Verificação Final

### 7.1. Checklist de Testes

```bash
# 1. Verificar se aplicação está rodando
sudo supervisorctl status kmz
# Deve estar: RUNNING

# 2. Verificar Nginx
sudo nginx -t
sudo systemctl status nginx
# Deve estar: active (running)

# 3. Verificar logs
sudo tail -f /var/log/kmz/gunicorn.log
# Não deve ter erros

# 4. Teste de conectividade
curl https://kmz.perplan.tech
# Deve retornar HTML

# 5. Verificar DNS
nslookup kmz.perplan.tech
# Deve retornar IP correto
```

### 7.2. Testar no Navegador

1. **Acesse:** `https://kmz.perplan.tech`
2. **Teste Upload:**
   - Selecione um arquivo Excel
   - Escolha modo "Simples"
   - Clique "Processar Arquivo"
   - Aguarde processamento
3. **Teste Download:**
   - Download KML
   - Download Log
4. **Teste API Docs:**
   - Acesse: `https://kmz.perplan.tech/swagger/`
   - Deve carregar interface Swagger
5. **Teste Admin:**
   - Acesse: `https://kmz.perplan.tech/admin/`
   - Faça login
   - Veja lista de jobs

### 7.3. Monitoramento

```bash
# Ver logs em tempo real
sudo supervisorctl tail -f kmz

# Ver logs do Nginx
sudo tail -f /var/log/nginx/kmz_access.log
sudo tail -f /var/log/nginx/kmz_error.log

# Ver status de processos
sudo supervisorctl status

# Ver uso de porta
sudo netstat -tulpn | grep 8001
```

---

## 🔄 Atualizações Futuras

### Deploy de Novas Versões

**Opção A: Script Automatizado (recomendado)**

```bash
# SSH na EC2
ssh -i sua-chave.pem ubuntu@IP_DA_EC2

# Navegar para o projeto
cd /var/www/kmz

# Dar permissão de execução (primeira vez apenas)
chmod +x deploy/deploy.sh

# Executar deploy automatizado
./deploy/deploy.sh
```

O script automaticamente:
- Faz backup do banco de dados
- Pull das alterações do GitHub
- Instala/atualiza dependências
- Executa migrações
- Coleta arquivos estáticos
- Ajusta permissões
- Reinicia aplicação
- Recarrega Nginx
- Verifica saúde da aplicação

**Opção B: Deploy Manual**

```bash
# SSH na EC2
ssh -i sua-chave.pem ubuntu@IP_DA_EC2

# Ir para diretório
cd /var/www/kmz

# Fazer backup do banco (se SQLite)
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# Pull das alterações
git pull origin main

# Ativar venv
source venv/bin/activate

# Instalar novas dependências (se houver)
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar estáticos
python manage.py collectstatic --noinput

# Reiniciar aplicação
sudo supervisorctl restart kmz

# Verificar
sudo supervisorctl status kmz
```

---

## 🚨 Troubleshooting

### Problema: Supervisor não inicia

```bash
# Ver logs detalhados
sudo supervisorctl tail -f kmz stderr

# Verificar permissões
ls -la /var/www/kmz

# Verificar se venv existe
ls -la /var/www/kmz/venv/bin/gunicorn

# Reiniciar Supervisor
sudo systemctl restart supervisor
```

### Problema: Nginx 502 Bad Gateway

```bash
# Verificar se Gunicorn está rodando
sudo supervisorctl status kmz

# Verificar se porta 8001 está aberta
sudo netstat -tulpn | grep 8001

# Ver logs do Nginx
sudo tail -f /var/log/nginx/kmz_error.log

# Reiniciar tudo
sudo supervisorctl restart kmz
sudo systemctl reload nginx
```

### Problema: Erro de permissão em media/

```bash
# Corrigir permissões
sudo chown -R ubuntu:www-data /var/www/kmz/media
sudo chmod -R 775 /var/www/kmz/media

# Reiniciar
sudo supervisorctl restart kmz
```

### Problema: DNS não propaga

```bash
# Verificar registro na Hostinger
# Aguardar até 30 minutos

# Limpar cache DNS local
# Windows:
ipconfig /flushdns

# Linux/Mac:
sudo systemd-resolve --flush-caches

# Testar DNS
nslookup kmz.perplan.tech 8.8.8.8
```

### Problema: SSL não funciona

```bash
# Ver configuração do Certbot
sudo certbot certificates

# Forçar renovação
sudo certbot --nginx -d kmz.perplan.tech --force-renewal

# Verificar Nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 Comandos Úteis

```bash
# Ver status de todos os serviços
sudo supervisorctl status

# Reiniciar aplicação
sudo supervisorctl restart kmz

# Parar aplicação
sudo supervisorctl stop kmz

# Iniciar aplicação
sudo supervisorctl start kmz

# Ver logs em tempo real
sudo supervisorctl tail -f kmz

# Recarregar Nginx
sudo systemctl reload nginx

# Testar config Nginx
sudo nginx -t

# Ver processos Python
ps aux | grep python

# Ver uso de memória
free -h

# Ver disco
df -h
```

---

## 🎯 Resumo do Deploy

```
1. ✅ Repositório criado no GitHub
2. ✅ Código clonado em /var/www/kmz/
3. ✅ Virtualenv criado e dependências instaladas
4. ✅ .env configurado
5. ✅ Banco de dados criado e migrado
6. ✅ Supervisor configurado (porta 8001)
7. ✅ Nginx configurado (proxy reverso)
8. ✅ DNS configurado na Hostinger (kmz.perplan.tech)
9. ✅ SSL configurado com Let's Encrypt
10. ✅ Testes realizados e sistema funcionando
```

---

## 📞 Próximos Passos

- Configure backups automáticos do banco de dados
- Configure monitoramento (Uptime Robot, etc)
- Documente processos para a equipe
- Configure alertas de erro (Sentry, etc)

**Sistema pronto em:** `https://kmz.perplan.tech` 🚀
