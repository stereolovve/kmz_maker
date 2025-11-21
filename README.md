# Lista de Obras - Gerador de KML

Sistema para conversão de planilhas Excel de obras rodoviárias em arquivos KML para visualização no Google Earth.

## 📋 Preparação da Base de Dados Excel

### Estrutura da Planilha

#### Para processamento COM ROTAS (kmz_maker.py)
Arquivo: `input/lista_obras.xlsx` - Sheet: `lista`

| Coluna | Obrigatório | Descrição | Exemplo |
|--------|-------------|-----------|---------|
| `tipo` | ✅ Sim | Tipo da obra | "Duplicação", "Faixa Adicional", "Interseções" |
| `ano` | ✅ Sim | Ano da obra | "2024", "2025" |
| `kmi` | ✅ Sim | Quilômetro inicial | "123.5", "45" |
| `kmf` | ⚠️ Condicional* | Quilômetro final | "125.8", "47" |
| `lati` | ✅ Sim | Latitude inicial | Ver formatos abaixo |
| `longi` | ✅ Sim | Longitude inicial | Ver formatos abaixo |
| `latf` | ⚠️ Condicional* | Latitude final | Ver formatos abaixo |
| `longf` | ⚠️ Condicional* | Longitude final | Ver formatos abaixo |
| `sentido` | ❌ Não | Sentido da obra | "Norte", "Sul", "Crescente" |

*\* Necessário para criar rotas. Se ausente, apenas o ponto inicial será plotado.*

#### Para processamento SIMPLES (lista_simples.py)
Arquivo: `input/lista_simples.xlsx` - Sheet: `lista_simples`

| Coluna | Obrigatório | Descrição | Exemplo |
|--------|-------------|-----------|---------|
| `tipo` | ✅ Sim | Tipo da obra | "Duplicação", "OAEs" |
| `ano` | ✅ Sim | Ano da obra | "2024" |
| `kmi` | ✅ Sim | Quilômetro | "123.5" |
| `lati` | ✅ Sim | Latitude | Ver formatos abaixo |
| `longi` | ✅ Sim | Longitude | Ver formatos abaixo |
| `sentido` | ❌ Não | Sentido da obra | "Norte" |

*Nota: Este modo gera apenas marcadores pontuais, sem rotas.*

### 📍 Formatos de Coordenadas Aceitos

O sistema aceita coordenadas nos seguintes formatos:

#### 1. Formato Decimal (Recomendado)
```
Latitude:  -23.550520
Longitude: -46.633308
```
- Use ponto (.) ou vírgula (,) como separador decimal
- Latitudes sul e longitudes oeste devem ser negativas
- Para o Brasil: latitudes entre -35 e 5, longitudes entre -75 e -30

#### 2. Formato DMS (Graus, Minutos, Segundos)
```
Latitude:  23°33'1.87"S  ou  23 33 1.87 S
Longitude: 46°37'59.91"W ou  46 37 59.91 W
```
- O sistema reconhece automaticamente o formato
- Use S/O/W para sul/oeste, ou N/E/L para norte/leste
- Separadores aceitos: °, ', ", espaços

#### 3. Formato DMS sem direção (Brasil)
```
23 33 1.87
46 37 59.91
```
- Se não houver direção (S/N/W/E), o sistema assume coordenadas brasileiras (negativas)

### ✅ Validações Automáticas

O sistema valida automaticamente:

1. **Coordenadas obrigatórias**: Linhas sem `lati` ou `longi` são ignoradas
2. **Limites geográficos**: Verifica se está dentro do território brasileiro
3. **Formato válido**: Tenta converter DMS → Decimal automaticamente
4. **Duplicatas**: Remove itens duplicados (mesma coordenada + tipo)

### 🎨 Tipos de Obra Suportados

O sistema reconhece os seguintes tipos (cores automáticas):

- Duplicação / Duplicações
- Faixa Adicional
- Obras de Contorno
- Travessias Urbanas
- Vias Marginais
- Correções de traçado
- Interseções
- Retornos
- Passarelas
- OAEs
- Áreas de Escape
- Ciclovias

*Outros tipos serão aceitos e receberão cores geradas automaticamente.*

### 📝 Exemplos Práticos

#### Exemplo 1: Duplicação com rotas
```
tipo: Duplicação
ano: 2024
kmi: 120.5
kmf: 125.8
lati: -23.550520
longi: -46.633308
latf: -23.560000
longf: -46.640000
sentido: Norte
```

#### Exemplo 2: Interseção simples (apenas ponto)
```
tipo: Interseções
ano: 2025
kmi: 45.2
lati: -15.793889
longi: -47.882778
```

#### Exemplo 3: Formato DMS
```
tipo: OAEs
ano: 2024
kmi: 67.3
lati: 23°33'1.87"S
longi: 46°37'59.91"W
```

### 🚨 Erros Comuns

| Problema | Solução |
|----------|---------|
| "Coordenada é NaN/None" | Célula vazia - preencha a coordenada |
| "Coordenadas inválidas" | Fora do Brasil - verifique os valores |
| "Falha ao parsear" | Formato não reconhecido - use decimal ou DMS |
| Item duplicado | Mesma coordenada já existe - será ignorado automaticamente |

### 🔧 API REST (Em Desenvolvimento)

Quando implantado como API, os endpoints serão:

- `POST /api/kml/process/` - Upload Excel + modo (rotas/simples)
- `GET /api/kml/jobs/{id}/` - Consultar status
- `GET /api/kml/jobs/{id}/download/` - Baixar KML gerado

Documentação Swagger disponível em `/swagger/`

---

## 🚀 Uso dos Scripts Standalone

### Script com Rotas (Google Maps API)
```bash
python kmz_maker.py
```
- Gera arquivo: `Obras.kml`
- Cria rotas usando Google Maps Directions API
- Organiza por Ano > Tipo

### Script Simples (Apenas Pontos)
```bash
python lista_simples.py
```
- Gera arquivo: `output_simple.kml`
- Apenas marcadores pontuais
- Mais rápido, sem chamadas à API

### Requisitos
```bash
pip install pandas openpyxl simplekml requests polyline
```

---

## 📦 Saída Gerada

Arquivo KML organizado em hierarquia:
```
📁 2024
  📁 Duplicação
    📍 Duplicação 001
    📍 Fim Duplicação 001
    🛣️ Rota Duplicação 001
  📁 Interseções
    📍 Interseções 002
📁 2025
  📁 OAEs
    📍 OAEs 003
```

Cada item recebe cor única para fácil identificação no Google Earth.

---

## 🔑 Configuração (Scripts Standalone)

### Google Maps API Key
Edite `kmz_maker.py` linha 9:
```python
GOOGLE_API_KEY = "sua-chave-aqui"
```

Para obter uma chave: https://developers.google.com/maps/documentation/directions/get-api-key

---

## 📞 Suporte

Para dúvidas sobre preparação dos dados ou erros de processamento, verifique:
1. Formato das coordenadas
2. Colunas obrigatórias preenchidas
3. Mensagens de debug no console durante execução
