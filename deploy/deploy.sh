#!/bin/bash

# Script de Deploy Automatizado - KMZ System
# Usage: ./deploy.sh

set -e

echo "==================================="
echo "KMZ System - Deploy Automatizado"
echo "==================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variaveis
PROJECT_DIR="/var/www/kmz"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log/kmz"

# Funcao para imprimir com cor
print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Verificar se esta no diretorio correto
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Diretorio $PROJECT_DIR nao encontrado!"
    exit 1
fi

cd $PROJECT_DIR
print_success "Mudado para diretorio: $PROJECT_DIR"

# Backup do banco de dados (se SQLite)
if [ -f "db.sqlite3" ]; then
    BACKUP_FILE="db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"
    cp db.sqlite3 $BACKUP_FILE
    print_success "Backup do banco criado: $BACKUP_FILE"
fi

# Git pull
echo ""
echo "Baixando ultimas alteracoes do GitHub..."
git fetch origin
git pull origin main
print_success "Codigo atualizado com sucesso"

# Ativar virtualenv
echo ""
echo "Ativando ambiente virtual..."
source $VENV_DIR/bin/activate
print_success "Virtualenv ativado"

# Atualizar dependencias
echo ""
echo "Instalando/atualizando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
print_success "Dependencias instaladas"

# Executar migracoes
echo ""
echo "Executando migracoes do banco de dados..."
python manage.py migrate --noinput
print_success "Migracoes executadas"

# Coletar arquivos estaticos
echo ""
echo "Coletando arquivos estaticos..."
python manage.py collectstatic --noinput -c
print_success "Arquivos estaticos coletados"

# Verificar permissoes de diretórios
echo ""
echo "Verificando permissoes..."
sudo chown -R ubuntu:www-data $PROJECT_DIR/media
sudo chmod -R 775 $PROJECT_DIR/media
sudo chown -R ubuntu:www-data $PROJECT_DIR/staticfiles
sudo chmod -R 755 $PROJECT_DIR/staticfiles
print_success "Permissoes ajustadas"

# Reiniciar servico Supervisor
echo ""
echo "Reiniciando aplicacao..."
sudo supervisorctl restart kmz
sleep 2

# Verificar status
STATUS=$(sudo supervisorctl status kmz | awk '{print $2}')
if [ "$STATUS" = "RUNNING" ]; then
    print_success "Aplicacao reiniciada com sucesso!"
else
    print_error "Falha ao reiniciar aplicacao. Status: $STATUS"
    echo ""
    echo "Logs de erro:"
    sudo supervisorctl tail kmz stderr
    exit 1
fi

# Recarregar Nginx
echo ""
echo "Recarregando Nginx..."
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    print_success "Nginx recarregado"
else
    print_error "Erro na configuracao do Nginx"
    exit 1
fi

# Verificar se a aplicacao esta respondendo
echo ""
echo "Testando aplicacao..."
sleep 2
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/)
if [ "$RESPONSE" = "200" ]; then
    print_success "Aplicacao respondendo corretamente (HTTP $RESPONSE)"
else
    print_warning "Aplicacao retornou HTTP $RESPONSE"
fi

# Resumo final
echo ""
echo "==================================="
echo "Deploy concluido com sucesso!"
echo "==================================="
echo ""
echo "Verificacoes adicionais:"
echo "- Status Supervisor: sudo supervisorctl status kmz"
echo "- Logs aplicacao: sudo supervisorctl tail -f kmz"
echo "- Logs Nginx: sudo tail -f /var/log/nginx/kmz_error.log"
echo "- Testar site: https://kmz.perplan.tech"
echo ""
