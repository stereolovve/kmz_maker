"""
Serviços para processamento de arquivos Excel e geração de KML
Refatoração dos scripts kmz_maker.py e lista_simples.py
"""
import pandas as pd
import simplekml
import requests
import polyline
import re
import hashlib
from typing import Optional, Tuple, List
from django.conf import settings
from datetime import datetime


def parse_coordinate(coord_str) -> Optional[float]:
    """Converte coordenadas DMS para decimal"""

    if pd.isna(coord_str):
        return None

    if isinstance(coord_str, (float, int)):
        coord_str = str(coord_str)

    if not isinstance(coord_str, str):
        return None

    coord_str = coord_str.strip()

    # Tentar formato decimal primeiro
    try:
        result = float(coord_str.replace(",", "."))

        # Detectar coordenadas sem ponto decimal (ex: -2777789 deve ser -27.77789)
        # Se o valor absoluto for maior que 360 (fora do range de coordenadas válidas)
        # e tiver 6 ou mais dígitos, adicionar ponto decimal
        if abs(result) > 360:
            result_str = str(int(result))
            is_negative = result < 0

            # Remove sinal para trabalhar apenas com dígitos
            if is_negative:
                result_str = result_str[1:]

            # Normalizar para 7 dígitos (2 de grau + 5 decimais)
            # Se tiver 6 dígitos, adicionar zero no final
            if len(result_str) == 6:
                result_str = result_str + '0'

            # Adicionar ponto antes dos últimos 5 dígitos
            if len(result_str) >= 7:
                result = float(result_str[:-5] + '.' + result_str[-5:])
                if is_negative:
                    result = -result

        return result
    except:
        pass

    # Extrair números e direção do formato DMS
    numbers = re.findall(r'-?\d+(?:[,\.]?\d+)?', coord_str)
    direction = re.search(r'[NSWO]', coord_str.upper())

    if len(numbers) >= 3:
        try:
            graus = float(numbers[0].replace(",", "."))
            minutos = float(numbers[1].replace(",", "."))
            segundos = float(numbers[2].replace(",", "."))

            decimal = graus + minutos/60 + segundos/3600

            if direction and direction.group() in ['S', 'O', 'W']:
                decimal = -decimal
            elif not direction:
                decimal = -decimal

            return decimal
        except:
            pass

    return None


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validar se as coordenadas estão em território brasileiro"""
    if lat is None or lon is None:
        return False

    # Brasil: aproximadamente lat -35 a 5, lon -75 a -30
    if not (-35 <= lat <= 5 and -75 <= lon <= -30):
        return False

    return True


def generate_color_for_item(item_name: str) -> str:
    """Gerar cor única e vibrante baseada no nome do item"""
    hash_obj = hashlib.md5(item_name.encode())
    hash_hex = hash_obj.hexdigest()

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

    color_index = int(hash_hex[:2], 16) % len(vibrant_colors)
    return vibrant_colors[color_index]


def get_google_route(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[List[Tuple[float, float]]]:
    """Obter rota do Google Maps API"""
    google_api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

    if not google_api_key:
        return None

    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={lat1},{lon1}&destination={lat2},{lon2}&mode=driving&key={google_api_key}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") == "OK":
            overview_polyline = data['routes'][0]['overview_polyline']['points']
            coords = polyline.decode(overview_polyline)
            return [(lon, lat) for lat, lon in coords]
    except Exception as e:
        print(f"Route error: {e}")

    return None


def process_excel_com_rotas(file_path: str, output_path: str, log_path: str = None) -> dict:
    """
    Processa Excel e gera KML com rotas usando Google Maps API
    Retorna estatísticas do processamento
    """

    # Iniciar log
    log_lines = []
    log_lines.append(f"=== PROCESSAMENTO COM ROTAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    log_lines.append(f"Arquivo: {file_path}\n")

    # Carregar dados - usa primeira sheet disponível
    df = pd.read_excel(file_path, sheet_name=0, dtype=str)
    df.columns = df.columns.str.strip()

    log_lines.append(f"Total de registros no Excel: {len(df)}\n")
    log_lines.append(f"Colunas encontradas: {', '.join(df.columns)}\n\n")

    # Renomear coluna se necessário
    if 'Long' in df.columns:
        df = df.rename(columns={'Long': 'Longf'})
        log_lines.append("Coluna 'Long' renomeada para 'Longf'\n")

    kml = simplekml.Kml()

    # Contadores
    stats = {
        'processed': 0,
        'skipped': 0,
        'routes_created': 0,
        'total': len(df)
    }

    # Coletar e ordenar dados
    dados_para_processar = []

    for idx, row in df.iterrows():
        tipo = str(row.get("tipo", "Sem Tipo")).strip()
        kmi = str(row.get("kmi", "0")).strip()
        kmf = str(row.get("kmf", kmi)).strip()
        ano = str(row.get("ano", "Sem Ano")).strip() if pd.notna(row.get("ano")) else "Sem Ano"
        sentido = str(row.get("sentido", "")).strip() if pd.notna(row.get("sentido")) else None

        lati = parse_coordinate(row.get("lati"))
        longi = parse_coordinate(row.get("longi"))
        latf = parse_coordinate(row.get("latf"))
        longf = parse_coordinate(row.get("longf"))

        if lati is None or longi is None:
            stats['skipped'] += 1
            continue

        if not validate_coordinates(lati, longi):
            stats['skipped'] += 1
            continue

        dados_para_processar.append({
            'tipo': tipo,
            'kmi': kmi,
            'kmf': kmf,
            'ano': ano,
            'sentido': sentido,
            'lati': lati,
            'longi': longi,
            'latf': latf,
            'longf': longf,
        })

    # Ordenar por latitude decrescente
    dados_para_processar.sort(key=lambda x: x['lati'], reverse=True)

    # Organizar por Ano > Tipo
    ano_folders = {}

    # Processar dados
    for contador, dados in enumerate(dados_para_processar, 1):
        tipo = dados['tipo']
        kmi = dados['kmi']
        kmf = dados['kmf']
        ano = dados['ano']
        lati = dados['lati']
        longi = dados['longi']
        latf = dados['latf']
        longf = dados['longf']

        # Criar hierarquia Ano > Tipo
        if ano not in ano_folders:
            ano_folders[ano] = kml.newfolder(name=ano)

        ano_folder = ano_folders[ano]

        tipo_key = f"{ano}_{tipo}"
        if tipo_key not in ano_folders:
            tipo_folder = ano_folder.newfolder(name=tipo)
            ano_folders[tipo_key] = tipo_folder
        else:
            tipo_folder = ano_folders[tipo_key]

        folder = tipo_folder

        # Nome do item
        nome_base = f"{tipo} {contador:03d}"
        nome_inicio = f"Inicio {nome_base} Kmi: {kmi}"

        # Criar ponto inicial
        ponto_inicial = folder.newpoint(name=nome_inicio, coords=[(longi, lati)])
        cor = generate_color_for_item(nome_base)
        ponto_inicial.style.iconstyle.color = cor
        ponto_inicial.style.iconstyle.scale = 1.2

        stats['processed'] += 1

        # Criar ponto final e rota se houver coordenadas válidas
        if (latf is not None and longf is not None and kmi != kmf):
            if validate_coordinates(latf, longf):
                # Ponto final
                nome_fim = f"Fim {nome_base} Km: {kmf}"
                ponto_final = folder.newpoint(name=nome_fim, coords=[(longf, latf)])
                ponto_final.style.iconstyle.color = cor
                ponto_final.style.iconstyle.scale = 1.0

                # Criar rota
                route_coords = get_google_route(lati, longi, latf, longf)
                if route_coords:
                    rota = folder.newlinestring(name=f"Rota {nome_base} {kmi} a {kmf}")
                    rota.coords = route_coords
                    rota.style.linestyle.color = cor
                    rota.style.linestyle.width = 3
                    stats['routes_created'] += 1
                    log_lines.append(f"  [ROTA] Criada rota de {kmi} a {kmf}\n")

    # Salvar arquivo
    kml.save(output_path)

    # Adicionar resumo ao log
    log_lines.append(f"\n=== RESUMO ===\n")
    log_lines.append(f"Total de itens: {stats['total']}\n")
    log_lines.append(f"Processados: {stats['processed']}\n")
    log_lines.append(f"Ignorados: {stats['skipped']}\n")
    log_lines.append(f"Rotas criadas: {stats['routes_created']}\n")
    log_lines.append(f"\nArquivo KML gerado: {output_path}\n")
    log_lines.append(f"Processamento concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Salvar log se caminho fornecido
    if log_path:
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.writelines(log_lines)
            stats['log_file'] = log_path
        except Exception as e:
            print(f"Erro ao salvar log: {e}")

    return stats


def process_excel_simples(file_path: str, output_path: str, log_path: str = None) -> dict:
    """
    Processa Excel e gera KML simples (apenas pontos)
    Retorna estatísticas do processamento
    """

    # Iniciar log
    log_lines = []
    log_lines.append(f"=== PROCESSAMENTO SIMPLES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    log_lines.append(f"Arquivo: {file_path}\n")

    # Carregar dados - usa primeira sheet disponível
    df = pd.read_excel(file_path, sheet_name=0, dtype=str)
    df.columns = df.columns.str.strip()

    log_lines.append(f"Total de registros no Excel: {len(df)}\n")
    log_lines.append(f"Colunas encontradas: {', '.join(df.columns)}\n\n")

    if 'Long' in df.columns:
        df = df.rename(columns={'Long': 'longf'})
        log_lines.append("Coluna 'Long' renomeada para 'longf'\n")

    kml = simplekml.Kml()

    # Contadores
    stats = {
        'processed': 0,
        'skipped': 0,
        'duplicated': 0,
        'total': len(df)
    }

    itens_processados = set()
    dados_para_processar = []

    for idx, row in df.iterrows():
        tipo = str(row.get("tipo", "Sem Tipo")).strip()
        kmi = str(row.get("kmi", "0")).strip()
        kmf = str(row.get("kmf", kmi)).strip()
        ano = str(row.get("ano", "Sem Ano")).strip() if pd.notna(row.get("ano")) else "Sem Ano"
        sentido = str(row.get("sentido", "")).strip() if pd.notna(row.get("sentido")) else None

        lati = parse_coordinate(row.get("lati"))
        longi = parse_coordinate(row.get("longi"))

        if lati is None or longi is None:
            stats['skipped'] += 1
            continue

        if not validate_coordinates(lati, longi):
            stats['skipped'] += 1
            continue

        dados_para_processar.append({
            'tipo': tipo,
            'kmi': kmi,
            'kmf': kmf,
            'ano': ano,
            'sentido': sentido,
            'lati': lati,
            'longi': longi,
        })

    # Ordenar por latitude decrescente
    dados_para_processar.sort(key=lambda x: x['lati'], reverse=True)

    # Organizar por Ano > Tipo
    ano_folders = {}

    # Processar dados
    for contador, dados in enumerate(dados_para_processar, 1):
        tipo = dados['tipo']
        kmi = dados['kmi']
        ano = dados['ano']
        sentido = dados['sentido']
        lati = dados['lati']
        longi = dados['longi']

        # Verificar duplicatas
        item_key = f"{tipo}_{lati:.6f}_{longi:.6f}"
        if item_key in itens_processados:
            stats['duplicated'] += 1
            continue

        itens_processados.add(item_key)

        # Criar hierarquia Ano > Tipo
        if ano not in ano_folders:
            ano_folders[ano] = kml.newfolder(name=ano)

        ano_folder = ano_folders[ano]

        tipo_key = f"{ano}_{tipo}"
        if tipo_key not in ano_folders:
            tipo_folder = ano_folder.newfolder(name=tipo)
            ano_folders[tipo_key] = tipo_folder
        else:
            tipo_folder = ano_folders[tipo_key]

        folder = tipo_folder

        # Nome do item
        nome_inicio = f"{tipo} {contador:03d}"

        # Criar ponto
        item_inicial = folder.newpoint(name=nome_inicio, coords=[(longi, lati)])
        cor = generate_color_for_item(nome_inicio)
        item_inicial.style.iconstyle.color = cor
        item_inicial.style.iconstyle.scale = 1.2

        # Descrição
        descricao = f"Tipo: {tipo}\nKm: {kmi}"
        if sentido:
            descricao += f"\nSentido: {sentido}"
        item_inicial.description = descricao

        stats['processed'] += 1
        log_lines.append(f"[PROCESSADO] {nome_inicio} - Coord: ({lati:.6f}, {longi:.6f})\n")

    # Salvar arquivo
    kml.save(output_path)

    # Adicionar resumo ao log
    log_lines.append(f"\n=== RESUMO ===\n")
    log_lines.append(f"Total de itens: {stats['total']}\n")
    log_lines.append(f"Processados: {stats['processed']}\n")
    log_lines.append(f"Ignorados: {stats['skipped']}\n")
    log_lines.append(f"Duplicados: {stats['duplicated']}\n")
    log_lines.append(f"\nArquivo KML gerado: {output_path}\n")
    log_lines.append(f"Processamento concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Salvar log se caminho fornecido
    if log_path:
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.writelines(log_lines)
            stats['log_file'] = log_path
        except Exception as e:
            print(f"Erro ao salvar log: {e}")

    return stats
