import pandas as pd
import simplekml
import requests
import polyline
import re
import hashlib

# Configurações
GOOGLE_API_KEY = "AIzaSyCwVA3TO6jgTx1wcs3zIaZ0-L5c_Lk6SDA"
INPUT_FILE = "input/lista_obras.xlsx"
OUTPUT_FILE = "Obras.kml"

# Cores por tipo de obra
CORES_POR_TIPO = {
    "Duplicação": "ff000080",
    "Duplicações": "ff000080",
    "Faixa Adicional": "ff00ffff",
    "Obras de Contorno": "ff804000",
    "Travessias Urbanas": "ff4080ff",
    "Vias Marginais": "ff008040",
    "Correções de traçado": "ff808080",
    "Interseções": "ff400080",
    "Retornos": "ff0080ff",
    "Passarelas": "ffff8000",
    "OAEs": "ff804080",
    "Áreas de Escape": "ff808040",
    "Ciclovias": "ff408040",
}


def parse_coordinate(coord_str):
    """Converte coordenadas DMS para decimal"""

    # Armazenar valor e tipo originais para debug
    original_value = coord_str
    original_type = type(coord_str).__name__

    # Verificar se é NaN/None
    if pd.isna(coord_str):
        print(f"DEBUG parse_coordinate: Coordenada é NaN/None (tipo: {original_type})")
        return None

    # Converter números (float, int) para string
    if isinstance(coord_str, (float, int)):
        # Converter para string preservando formato
        coord_str = str(coord_str)
        print(
            f"DEBUG parse_coordinate: Convertido {original_type} para string: {original_value} -> '{coord_str}'"
        )

    # Verificar se agora é string
    if not isinstance(coord_str, str):
        print(
            f"DEBUG parse_coordinate: Tipo não suportado: {original_type}, valor: {original_value}"
        )
        return None

    coord_str = coord_str.strip()

    # Tentar formato decimal primeiro (com sinal negativo)
    try:
        result = float(coord_str.replace(",", "."))
        print(f"DEBUG parse_coordinate: Decimal OK: '{coord_str}' -> {result}")
        return result
    except Exception as e:
        print(f"DEBUG parse_coordinate: Falha ao parsear decimal '{coord_str}': {e}")
        pass

    # Extrair números e direção do formato DMS (incluir sinal negativo)
    numbers = re.findall(r"-?\d+(?:[,\.]?\d+)?", coord_str)
    direction = re.search(r"[NSWO]", coord_str.upper())

    if len(numbers) >= 3:
        try:
            graus = float(numbers[0].replace(",", "."))
            minutos = float(numbers[1].replace(",", "."))
            segundos = float(numbers[2].replace(",", "."))

            decimal = graus + minutos / 60 + segundos / 3600

            # Se há direção explícita, usar ela
            if direction and direction.group() in ["S", "O", "W"]:
                decimal = -decimal
            # Se não há direção, assumir negativo para coordenadas brasileiras
            elif not direction:
                # Brasil: latitudes são negativas (Sul), longitudes são negativas (Oeste)
                decimal = -decimal

            print(f"DEBUG parse_coordinate: DMS OK: '{coord_str}' -> {decimal}")
            return decimal
        except Exception as e:
            print(f"DEBUG parse_coordinate: Falha ao parsear DMS '{coord_str}': {e}")
            pass

    print(f"DEBUG parse_coordinate: Não foi possível parsear: '{coord_str}'")
    return None


def validate_coordinates(lat, lon):
    """Validar se as coordenadas estão em território brasileiro"""
    if lat is None or lon is None:
        return False

    # Brasil: aproximadamente lat -35 a 5, lon -75 a -30
    if not (-35 <= lat <= 5 and -75 <= lon <= -30):
        return False

    return True


def generate_color_for_item(item_name):
    """Gerar cor única e vibrante baseada no nome do item"""
    hash_obj = hashlib.md5(item_name.encode())
    hash_hex = hash_obj.hexdigest()

    # Cores vibrantes predefinidas (ABGR format)
    vibrant_colors = [
        "ff0000ff",  # Vermelho vibrante
        "ff00ff00",  # Verde vibrante
        "ffff0000",  # Azul vibrante
        "ff00ffff",  # Amarelo vibrante
        "ffff00ff",  # Magenta vibrante
        "ffffff00",  # Ciano vibrante
        "ff8000ff",  # Laranja vibrante
        "ff0080ff",  # Rosa vibrante
        "ff80ff00",  # Verde-lima vibrante
        "ffff8000",  # Azul-céu vibrante
        "ff4000ff",  # Vermelho-escuro vibrante
        "ff00ff80",  # Verde-água vibrante
    ]

    # Usar hash para selecionar cor da lista
    color_index = int(hash_hex[:2], 16) % len(vibrant_colors)
    return vibrant_colors[color_index]


def get_google_route(lat1, lon1, lat2, lon2):
    """Obter rota do Google Maps API"""
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={lat1},{lon1}&destination={lat2},{lon2}&mode=driving&key={GOOGLE_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") == "OK":
            overview_polyline = data["routes"][0]["overview_polyline"]["points"]
            coords = polyline.decode(overview_polyline)
            return [(lon, lat) for lat, lon in coords]
        else:
            print(f"API Google error: {data.get('status')}")
    except Exception as e:
        print(f"Route error: {e}")

    return None


def main():
    print("=== Processador de Coordenadas Inicio-Fim ===")
    print("Carregando dados...")

    # Carregar dados
    try:
        df = pd.read_excel(INPUT_FILE, sheet_name="lista", dtype=str)
        df.columns = df.columns.str.strip()

        # Renomear coluna
        if "Long" in df.columns:
            df = df.rename(columns={"Long": "Longf"})

        print(f"Total de registros: {len(df)}")

    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return

    # Criar KML
    kml = simplekml.Kml()

    # Contadores
    processed = 0
    skipped = 0
    routes_created = 0

    # Primeiro, coletar todos os dados e ordenar por latitude (norte para sul)
    dados_para_processar = []

    for idx, row in df.iterrows():
        # Extrair dados básicos
        tipo = str(row.get("tipo", "Sem Tipo")).strip()
        kmi = str(row.get("kmi", "0")).strip()
        kmf = str(row.get("kmf", kmi)).strip()
        ano = (
            str(row.get("ano", "Sem Ano")).strip()
            if pd.notna(row.get("ano"))
            else "Sem Ano"
        )
        sentido = (
            str(row.get("sentido", "")).strip()
            if pd.notna(row.get("sentido"))
            else None
        )

        # Processar coordenadas
        print(f"\n--- DEBUG Item {idx} ---")
        print(
            f"DEBUG: lati bruto = {row.get('lati')} (tipo: {type(row.get('lati')).__name__})"
        )
        print(
            f"DEBUG: longi bruto = {row.get('longi')} (tipo: {type(row.get('longi')).__name__})"
        )
        print(
            f"DEBUG: latf bruto = {row.get('latf')} (tipo: {type(row.get('latf')).__name__})"
        )
        print(
            f"DEBUG: longf bruto = {row.get('longf')} (tipo: {type(row.get('longf')).__name__})"
        )

        lati = parse_coordinate(row.get("lati"))
        longi = parse_coordinate(row.get("longi"))
        latf = parse_coordinate(row.get("latf"))
        longf = parse_coordinate(row.get("longf"))

        print(
            f"DEBUG: Coordenadas parseadas -> lati={lati}, longi={longi}, latf={latf}, longf={longf}"
        )

        # Pular se não há coordenadas iniciais
        if lati is None or longi is None:
            print(f"DEBUG: Pulando item {idx} - coordenadas iniciais ausentes")
            skipped += 1
            continue

        # Validar coordenadas iniciais
        if not validate_coordinates(lati, longi):
            print(f"DEBUG: Coordenadas de {idx} inválidas: lat={lati}, lon={longi}")
            skipped += 1
            continue

        # Adicionar aos dados para processar
        dados_para_processar.append(
            {
                "tipo": tipo,
                "kmi": kmi,
                "kmf": kmf,
                "ano": ano,
                "sentido": sentido,
                "lati": lati,
                "longi": longi,
                "latf": latf,
                "longf": longf,
                "idx_original": idx,
            }
        )

    # Ordenar por latitude decrescente (norte para sul)
    dados_para_processar.sort(key=lambda x: x["lati"], reverse=True)

    # Organizar por Ano > Tipo
    ano_folders = {}

    # Processar dados ordenados
    for contador, dados in enumerate(dados_para_processar, 1):
        tipo = dados["tipo"]
        kmi = dados["kmi"]
        kmf = dados["kmf"]
        ano = dados["ano"]
        sentido = dados["sentido"]
        lati = dados["lati"]
        longi = dados["longi"]
        latf = dados["latf"]
        longf = dados["longf"]

        print(f"DEBUG: Processando item {contador:03d} - {tipo}: ({lati}, {longi})")

        # Criar hierarquia Ano > Tipo
        if ano not in ano_folders:
            ano_folders[ano] = kml.newfolder(name=ano)

        ano_folder = ano_folders[ano]

        # Criar pasta do tipo dentro do ano
        tipo_key = f"{ano}_{tipo}"
        if tipo_key not in ano_folders:
            tipo_folder = ano_folder.newfolder(name=tipo)
            ano_folders[tipo_key] = tipo_folder
        else:
            tipo_folder = ano_folders[tipo_key]

        folder = tipo_folder

        # Nome do item usando apenas o tipo e número sequencial
        nome_base = f"{tipo} {contador:03d}"
        nome_inicio = f"Inicio {nome_base} Kmi: {kmi}"

        # Criar ponto inicial
        ponto_inicial = folder.newpoint(name=nome_inicio, coords=[(longi, lati)])

        # Configurar estilo com cor única por item
        cor = generate_color_for_item(nome_base)
        ponto_inicial.style.iconstyle.color = cor
        ponto_inicial.style.iconstyle.scale = 1.2

        processed += 1

        # Criar ponto final e rota se houver coordenadas válidas
        if latf is not None and longf is not None and kmi != kmf:

            # Validar coordenadas finais
            if not validate_coordinates(latf, longf):
                print(f"DEBUG: Coordenadas finais inválidas: lat={latf}, lon={longf}")
            else:
                print(
                    f"DEBUG: Processando fim do item {contador:03d} - {tipo}: ({latf}, {longf})"
                )

                # Ponto final
                nome_fim = f"Fim {nome_base} Km: {kmf}"
                ponto_final = folder.newpoint(name=nome_fim, coords=[(longf, latf)])
                ponto_final.style.iconstyle.color = cor
                ponto_final.style.iconstyle.scale = 1.0

                # Criar rota
                print(
                    f"DEBUG: Criando rota de {nome_base} ({lati},{longi}) para ({latf},{longf})"
                )
                route_coords = get_google_route(lati, longi, latf, longf)
                if route_coords:
                    rota = folder.newlinestring(name=f"Rota {nome_base} {kmi} a {kmf}")
                    rota.coords = route_coords
                    rota.style.linestyle.color = cor
                    rota.style.linestyle.width = 3
                    routes_created += 1
                    print(f"DEBUG: Rota criada com {len(route_coords)} pontos")
                else:
                    print(f"DEBUG: Falha ao criar rota para {nome_base}")

        # Progress update
        if processed % 25 == 0:
            print(
                f"Processados: {processed}, Ignorados: {skipped}, Rotas: {routes_created}"
            )

    # Salvar arquivo
    try:
        kml.save(OUTPUT_FILE)
        print("\\n=== CONCLUIDO ===")
        print(f"Itens processados: {processed}")
        print(f"Itens ignorados: {skipped}")
        print(f"Rotas criadas: {routes_created}")
        print(f"Arquivo gerado: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Erro ao salvar: {e}")


if __name__ == "__main__":
    main()
