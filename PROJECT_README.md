# Lista de Obras - Sistema Gerador de KML

**Sistema web para conversão de planilhas Excel de obras rodoviárias em arquivos KML para visualização no Google Earth.**

![Status](https://img.shields.io/badge/status-ativo-success)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Django](https://img.shields.io/badge/django-5.0-green)
![License](https://img.shields.io/badge/license-Proprietary-red)

---

## Visão Geral

O **Lista de Obras** é uma aplicação web Django que automatiza a conversão de dados de obras rodoviárias (armazenados em planilhas Excel) em arquivos KML georreferenciados, permitindo visualização interativa no Google Earth.

### Funcionalidades Principais

- Upload de arquivos Excel via interface web intuitiva
- Dois modos de processamento:
  - **Simples**: Gera apenas marcadores pontuais
  - **Com Rotas**: Gera rotas entre pontos usando Google Maps Directions API
- Parsing inteligente de coordenadas (suporta formatos decimais e DMS)
- Validação automática de coordenadas para território brasileiro
- Organização hierárquica por Ano > Tipo de Obra
- Cores únicas geradas automaticamente para cada item
- Geração de logs detalhados do processamento
- API REST completa com documentação Swagger
- Interface administrativa Django para gerenciamento

---

## Arquitetura do Sistema

### Fluxo de Processamento

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │
       │ 1. Upload Excel
       ↓
┌─────────────────────┐
│  Interface Web      │
│  (HTML/JS/CSS)      │
└──────┬──────────────┘
       │
       │ 2. POST /api/kml/jobs/process/
       ↓
┌─────────────────────┐
│  Django REST API    │
│  (views.py)         │
└──────┬──────────────┘
       │
       │ 3. Salva arquivo em media/uploads/
       ↓
┌─────────────────────┐
│  Services.py        │
│  (Processamento)    │
└──────┬──────────────┘
       │
       ├─ 4a. Parse coordenadas (DMS → Decimal)
       ├─ 4b. Validação geográfica (Brasil)
       ├─ 4c. Google Maps API (se modo rotas)
       └─ 4d. Geração KML + Log
       │
       ↓
┌─────────────────────┐
│  Banco de Dados     │
│  (SQLite/PostgreSQL)│
└──────┬──────────────┘
       │
       │ 5. Salva em media/outputs/ e media/logs/
       ↓
┌─────────────────────┐
│  Download KML + Log │
└─────────────────────┘
```

### Estrutura de Diretórios

```
lista_obras/
├── config/                 # Configurações Django
│   ├── settings.py        # Settings (dev/prod)
│   ├── urls.py            # URLs principais + Swagger
│   └── wsgi.py
├── obras/                 # App principal
│   ├── models.py          # KMLJob (rastreamento de processamento)
│   ├── views.py           # API ViewSets
│   ├── serializers.py     # DRF Serializers
│   ├── services.py        # Lógica de processamento KML
│   ├── admin.py           # Django Admin customizado
│   ├── templates/
│   │   ├── home.html      # Interface web principal
│   │   └── tutorial.html  # Página tutorial para usuários
│   └── migrations/
├── deploy/                # Arquivos de deploy
│   ├── kmz.conf           # Config Supervisor
│   ├── kmz.perplan.tech.conf  # Config Nginx
│   ├── deploy.sh          # Script deploy automatizado
│   └── README.md          # Documentação deploy
├── media/                 # Arquivos gerados
│   ├── uploads/           # Excel enviados
│   ├── outputs/           # KML gerados
│   └── logs/              # Logs de processamento
├── staticfiles/           # Arquivos estáticos coletados
├── PROJECT_README.md      # Documentação do sistema (este arquivo)
├── DEPLOY_SUBDOMAIN.md    # Guia completo de deploy EC2
├── requirements.txt       # Dependências Python
├── .env                   # Variáveis de ambiente (não versionado)
├── .gitignore
└── manage.py
```

---

## Tecnologias Utilizadas

### Backend
- **Django 5.0**: Framework web
- **Django REST Framework 3.14**: API REST
- **drf-yasg 1.21**: Documentação Swagger/OpenAPI
- **pandas 2.1**: Manipulação de dados Excel
- **openpyxl 3.1**: Leitura de arquivos .xlsx
- **simplekml 1.3**: Geração de arquivos KML
- **requests 2.31**: Chamadas HTTP (Google Maps API)
- **polyline 2.0**: Decodificação de rotas Google

### Frontend
- **HTML5 + CSS3**: Interface responsiva
- **JavaScript (Vanilla)**: Interatividade e chamadas AJAX
- **Fetch API**: Comunicação com backend

### Infraestrutura
- **Python 3.10+**
- **SQLite** (desenvolvimento) / **PostgreSQL** (produção)
- **Gunicorn**: WSGI server
- **Nginx**: Reverse proxy (produção)
- **AWS EC2**: Hospedagem (produção)

---

## Como Funciona

### 1. Preparação dos Dados Excel

#### Colunas Obrigatórias
- `tipo`: Tipo da obra (ex: "Duplicação", "Interseções")
- `ano`: Ano da obra (ex: "2024")
- `kmi`: Quilômetro inicial
- `lati`: Latitude inicial
- `longi`: Longitude inicial

#### Colunas Opcionais
- `kmf`: Quilômetro final (necessário para rotas)
- `latf`: Latitude final (necessário para rotas)
- `longf`: Longitude final (necessário para rotas)
- `sentido`: Sentido da obra

### 2. Formatos de Coordenadas Suportados

**Decimal** (Recomendado):
```
-23.550520, -46.633308
```

**DMS (Graus, Minutos, Segundos)**:
```
23°33'1.87"S, 46°37'59.91"W
ou
23 33 1.87 S, 46 37 59 91 W
```

**DMS sem direção** (assume Brasil):
```
23 33 1.87, 46 37 59.91
```

### 3. Processamento

#### Modo Simples
1. Lê primeira sheet do Excel
2. Parse de coordenadas (converte DMS → Decimal)
3. Validação geográfica (verifica se está no Brasil)
4. Cria marcadores KML organizados por Ano > Tipo
5. Gera arquivo KML + Log detalhado

#### Modo Com Rotas
1. Todos os passos do Modo Simples
2. Para itens com coordenadas inicial e final:
   - Consulta Google Maps Directions API
   - Decodifica polyline da rota
   - Adiciona linha de rota no KML

### 4. Validações Automáticas

- **Coordenadas ausentes**: Item ignorado
- **Coordenadas fora do Brasil**: Item ignorado
  - Limites: Lat -35 a 5, Lon -75 a -30
- **Formato inválido**: Item ignorado
- **Duplicatas**: Removidas automaticamente (coordenada + tipo)

### 5. Organização do KML Gerado

```
📁 2024
  📁 Duplicação
    📍 Duplicação 001 (ponto inicial)
    📍 Fim Duplicação 001 (ponto final)
    🛣️ Rota Duplicação 001
  📁 Interseções
    📍 Interseções 002
📁 2025
  📁 OAEs
    📍 OAEs 003
```

---

## API REST

### Endpoints Disponíveis

#### 1. Processar Arquivo
```http
POST /api/kml/jobs/process/
Content-Type: multipart/form-data

{
  "input_file": <arquivo.xlsx>,
  "process_type": "simples" | "rotas"
}
```

**Resposta**:
```json
{
  "id": "uuid",
  "process_type": "simples",
  "status": "completed",
  "total_items": 173,
  "processed_items": 170,
  "skipped_items": 3,
  "output_file": "/media/outputs/...",
  "log_file": "/media/logs/...",
  "created_at": "2025-01-21T15:30:00Z"
}
```

#### 2. Listar Jobs
```http
GET /api/kml/jobs/
```

#### 3. Detalhes de um Job
```http
GET /api/kml/jobs/{id}/
```

#### 4. Download KML
```http
GET /api/kml/jobs/{id}/download/
```

#### 5. Download Log
```http
GET /api/kml/jobs/{id}/download_log/
```

### Documentação Interativa

- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **OpenAPI JSON**: `http://localhost:8000/swagger.json`

---

## Instalação e Uso

### Requisitos
- Python 3.10+
- pip
- virtualenv (recomendado)

### Passo a Passo

```bash
# Clone o repositório
git clone <repo-url>
cd lista_obras

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Execute migrações
python manage.py migrate

# Crie superusuário (opcional)
python manage.py createsuperuser

# Inicie servidor de desenvolvimento
python manage.py runserver
```

Acesse: `http://localhost:8000/`

---

## Configuração

### Variáveis de Ambiente (.env)

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (opcional - padrão SQLite)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=lista_obras_db
DB_USER=postgres_user
DB_PASSWORD=senha
DB_HOST=localhost
DB_PORT=5432

# Google Maps API (necessário para modo 'rotas')
GOOGLE_MAPS_API_KEY=sua-api-key-aqui
```

### Obter Google Maps API Key

1. Acesse: https://console.cloud.google.com/
2. Crie um projeto
3. Ative a API "Directions API"
4. Crie credenciais (API Key)
5. Adicione ao `.env`

---

## Deploy em Produção

### Arquivos de Deploy Prontos

Este repositório inclui templates prontos na pasta `deploy/`:
- **kmz.conf**: Configuração Supervisor (gerenciamento de processo)
- **kmz.perplan.tech.conf**: Configuração Nginx (proxy reverso)
- **deploy.sh**: Script de deploy automatizado
- **deploy/README.md**: Documentação completa dos arquivos

### Guia Completo de Deploy

Consulte `DEPLOY_SUBDOMAIN.md` para instruções passo-a-passo de deploy na AWS EC2 com:
- Criação de repositório GitHub
- Setup na EC2 (virtualenv, dependências, migrations)
- Configuração Supervisor (porta 8001)
- Configuração Nginx (proxy reverso)
- DNS na Hostinger (kmz.perplan.tech)
- SSL com Let's Encrypt (HTTPS)
- Script de deploy automatizado para atualizações futuras

### Deploy Rápido (Atualizações)

Após o setup inicial, atualizações são simples:

```bash
# SSH na EC2
ssh -i sua-chave.pem ubuntu@IP_DA_EC2

# Navegar e executar script
cd /var/www/kmz
./deploy/deploy.sh
```

O script automaticamente:
- Faz backup do banco
- Puxa alterações do GitHub
- Instala dependências
- Executa migrações
- Coleta arquivos estáticos
- Reinicia aplicação
- Verifica saúde do sistema

---

## Logs de Processamento

Cada processamento gera um arquivo `.txt` com:

- Data/hora do processamento
- Arquivo de entrada processado
- Colunas encontradas no Excel
- Detalhes de cada item processado
- Itens ignorados (com motivo)
- Rotas criadas (se aplicável)
- Resumo final com estatísticas

**Exemplo de Log**:
```
=== PROCESSAMENTO SIMPLES - 2025-01-21 15:30:00 ===
Arquivo: /media/uploads/2025/01/21/arquivo.xlsx
Total de registros no Excel: 173
Colunas encontradas: tipo, ano, kmi, lati, longi

[OK] Linha 0: Duplicação - Km 120.5 - Coord: (-23.550520, -46.633308)
[IGNORADO] Linha 5: Coordenadas iniciais ausentes (tipo: Interseções, km: 45.2)
[PROCESSADO] Duplicação 001 - Coord: (-23.550520, -46.633308)

=== RESUMO ===
Total de itens: 173
Processados: 170
Ignorados: 3
Duplicados: 0

Arquivo KML gerado: output_uuid.kml
Processamento concluído em: 2025-01-21 15:30:15
```

---

## Casos de Uso

1. **Planejamento de Obras**: Visualizar distribuição geográfica de obras planejadas
2. **Relatórios**: Gerar visualizações para stakeholders
3. **Monitoramento**: Acompanhar progresso de obras em diferentes regiões
4. **Análise Espacial**: Identificar padrões geográficos nas obras
5. **Integração GIS**: Importar para sistemas GIS profissionais

---

## Limitações Conhecidas

- Processamento síncrono (não recomendado para > 1000 itens simultâneos)
- Google Maps API tem limites de uso gratuito
- Validação geográfica limitada ao território brasileiro
- Suporte apenas para arquivos Excel (.xlsx, .xls)

---

## Roadmap Futuro

- [ ] Processamento assíncrono com Celery
- [ ] WebSockets para progresso em tempo real
- [ ] Suporte a múltiplos países
- [ ] Export para outros formatos (GeoJSON, Shapefile)
- [ ] Dashboard de estatísticas
- [ ] Autenticação e permissões por usuário
- [ ] API de consulta espacial

---

## Suporte

Para problemas ou dúvidas:

1. Consulte `README.md` para instruções de uso do Excel
2. Consulte `DEPLOY.md` para problemas de deploy
3. Verifique logs de processamento (arquivo `.txt`)
4. Acesse Django Admin em `/admin/` para debug

---

## Licença

Proprietary - Uso interno da empresa

---

## Créditos

Desenvolvido com Claude Code (Anthropic)

**Tecnologias Open Source Utilizadas**:
- Django & Django REST Framework
- SimpleKML
- Pandas
- E outras listadas em `requirements.txt`

---

*Última atualização: Janeiro 2025*
