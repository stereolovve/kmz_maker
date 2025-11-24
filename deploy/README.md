# Deploy - Arquivos de Configuracao

Esta pasta contem os arquivos de configuracao necessarios para o deploy do sistema KMZ na EC2.

## Arquivos Disponiveis

### 1. kmz.conf
**Arquivo de configuracao do Supervisor**

Este arquivo gerencia o processo Gunicorn que roda a aplicacao Django.

**Como usar:**
```bash
# Copiar para diretorio do Supervisor
sudo cp deploy/kmz.conf /etc/supervisor/conf.d/

# Recarregar configuracoes
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar servico
sudo supervisorctl start kmz
```

**Portas:**
- Gunicorn escuta em: `127.0.0.1:8001`

---

### 2. kmz.perplan.tech.conf
**Arquivo de configuracao do Nginx**

Configura o proxy reverso do Nginx para o subdominio kmz.perplan.tech.

**Como usar:**
```bash
# Copiar para sites-available do Nginx
sudo cp deploy/kmz.perplan.tech.conf /etc/nginx/sites-available/

# Criar link simbolico
sudo ln -s /etc/nginx/sites-available/kmz.perplan.tech.conf /etc/nginx/sites-enabled/

# Testar configuracao
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

**Nota:** Apos configurar SSL com Certbot, este arquivo sera automaticamente modificado para incluir configuracoes HTTPS.

---

### 3. deploy.sh
**Script de deploy automatizado**

Automatiza o processo de atualizacao da aplicacao em producao.

**Funcionalidades:**
- Backup automatico do banco de dados
- Git pull das ultimas alteracoes
- Instalacao de novas dependencias
- Execucao de migracoes
- Coleta de arquivos estaticos
- Reinicio do servico Supervisor
- Recarga do Nginx
- Verificacao de saude da aplicacao

**Como usar:**
```bash
# Dar permissao de execucao (primeira vez)
chmod +x deploy/deploy.sh

# Executar deploy
cd /var/www/kmz
./deploy/deploy.sh
```

**Saida esperada:**
```
===================================
KMZ System - Deploy Automatizado
===================================

[OK] Mudado para diretorio: /var/www/kmz
[OK] Backup do banco criado: db.sqlite3.backup.20250121_143022
[OK] Codigo atualizado com sucesso
[OK] Virtualenv ativado
[OK] Dependencias instaladas
[OK] Migracoes executadas
[OK] Arquivos estaticos coletados
[OK] Permissoes ajustadas
[OK] Aplicacao reiniciada com sucesso!
[OK] Nginx recarregado
[OK] Aplicacao respondendo corretamente (HTTP 200)

===================================
Deploy concluido com sucesso!
===================================
```

---

## Workflow de Deploy Completo

### Deploy Inicial (primeira vez)

Siga o guia completo em: `DEPLOY_SUBDOMAIN.md`

### Deploy de Atualizacoes (apos setup inicial)

```bash
# 1. SSH na EC2
ssh -i sua-chave.pem ubuntu@IP_DA_EC2

# 2. Navegar para o projeto
cd /var/www/kmz

# 3. Executar script de deploy
./deploy/deploy.sh

# 4. Verificar
curl https://kmz.perplan.tech
```

---

## Estrutura de Diretorios na EC2

```
/var/www/kmz/
├── config/              # Configuracoes Django
├── obras/               # App principal
├── deploy/              # Arquivos de deploy (esta pasta)
│   ├── kmz.conf
│   ├── kmz.perplan.tech.conf
│   ├── deploy.sh
│   └── README.md
├── media/               # Arquivos de upload
│   ├── uploads/
│   ├── outputs/
│   └── logs/
├── staticfiles/         # Arquivos estaticos coletados
├── venv/                # Virtualenv Python
├── manage.py
├── requirements.txt
└── .env                 # Variaveis de ambiente

/var/log/kmz/
├── access.log           # Logs de acesso Gunicorn
├── error.log            # Logs de erro Gunicorn
├── gunicorn.log         # Logs stdout Gunicorn
└── gunicorn_error.log   # Logs stderr Gunicorn

/var/log/nginx/
├── kmz_access.log       # Logs de acesso Nginx
└── kmz_error.log        # Logs de erro Nginx

/etc/supervisor/conf.d/
└── kmz.conf             # Configuracao Supervisor

/etc/nginx/sites-available/
└── kmz.perplan.tech.conf # Configuracao Nginx

/etc/nginx/sites-enabled/
└── kmz.perplan.tech.conf -> /etc/nginx/sites-available/kmz.perplan.tech.conf
```

---

## Troubleshooting

### Script deploy.sh falha

**Verificar logs:**
```bash
# Ver ultimas linhas de erro
sudo supervisorctl tail kmz stderr

# Logs completos
sudo tail -f /var/log/kmz/gunicorn_error.log
```

**Problemas comuns:**
- Permissoes incorretas: Execute `sudo chown -R ubuntu:ubuntu /var/www/kmz`
- Virtualenv nao ativado: O script ativa automaticamente
- Porta 8001 em uso: `sudo netstat -tulpn | grep 8001`

### Nginx retorna 502

**Causa:** Gunicorn nao esta rodando

**Solucao:**
```bash
# Verificar status
sudo supervisorctl status kmz

# Se nao estiver RUNNING:
sudo supervisorctl start kmz

# Ver logs
sudo supervisorctl tail -f kmz stderr
```

### Mudancas nao aparecem no site

**Cache do navegador:**
- Limpe o cache (Ctrl+Shift+R)
- Teste em aba anonima

**Arquivos estaticos:**
```bash
python manage.py collectstatic --noinput -c
sudo systemctl reload nginx
```

---

## Variaveis de Ambiente (.env)

O arquivo `.env` deve estar em `/var/www/kmz/.env` e conter:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=kmz.perplan.tech,IP_DA_EC2

DB_ENGINE=django.db.backends.postgresql
DB_NAME=kmz_db
DB_USER=kmz_user
DB_PASSWORD=senha-forte-aqui
DB_HOST=localhost
DB_PORT=5432

GOOGLE_MAPS_API_KEY=sua-api-key-aqui
```

**Gerar SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Comandos Uteis

```bash
# Ver status de todos os servicos
sudo supervisorctl status

# Reiniciar apenas a aplicacao
sudo supervisorctl restart kmz

# Ver logs em tempo real
sudo supervisorctl tail -f kmz

# Testar configuracao Nginx
sudo nginx -t

# Verificar se porta 8001 esta escutando
sudo netstat -tulpn | grep 8001

# Verificar processos Python
ps aux | grep gunicorn

# Verificar uso de memoria
free -h

# Verificar espaco em disco
df -h
```

---

## Seguranca

- Nunca commite o arquivo `.env` no Git
- Mantenha `.env` apenas no servidor
- Use senhas fortes para banco de dados
- Mantenha `DEBUG=False` em producao
- Configure ALLOWED_HOSTS corretamente
- Renove certificados SSL automaticamente (Certbot faz isso)

---

## Suporte

Para mais detalhes, consulte:
- `DEPLOY_SUBDOMAIN.md` - Guia completo de deploy inicial
- `PROJECT_README.md` - Documentacao do sistema
- `obras/templates/tutorial.html` - Tutorial para usuarios finais
