import os
import pandas as pd
import simplekml
import requests
import polyline

# 🔑 Chave da API do Google Maps (substitua pela sua chave real)
GOOGLE_API_KEY = "AIzaSyA-hPt3mahG5soxVQnnc6yeDBN1LEC1kwM"

# 🎨 Cores para cada tipo de obra
cores_por_tipo = {
    "Duplicação": "ff000080",
    "Faixa Adicional": "ff00ffff",
    "Marginal": "ff0000ff",
    "Trombeta": "ff800080",
    "Retorno Em U": "ff0000ff",
    "Retorno Em X": "ff0080ff",
    "Parclo": "ff00ff00",
    "Passarela": "ffff8000",
    "Alça": "ff008080",
    "Diamante": "ff0000ff",
    "Acessos": "ffff0000",
    "Trevo": "ff800000",
}

# 🏷️ Ícones personalizados para alguns tipos de obras
icones_por_tipo = {
    "Trombeta": "http://maps.google.com/mapfiles/kml/paddle/T.png",
    "Retorno Em U": "http://maps.google.com/mapfiles/kml/paddle/U.png",
    "Retorno Em X": "http://maps.google.com/mapfiles/kml/paddle/X.png",
    "Parclo": "http://maps.google.com/mapfiles/kml/paddle/P.png",
    "Passarela": "http://maps.google.com/mapfiles/kml/shapes/man.png",
    "Diamante": "http://maps.google.com/mapfiles/kml/paddle/blu-blank.png",
}

# 🌎 Limites do Brasil para evitar coordenadas no oceano
LIMITE_LAT_MIN, LIMITE_LAT_MAX = -35.0, 5.0
LIMITE_LON_MIN, LIMITE_LON_MAX = -74.0, -32.0


# 🔄 Corrigir coordenadas inválidas
def corrigir_coordenada(coord):
    try:
        if isinstance(coord, str):
            coord = coord.replace(",", ".")
            coord = float(coord)

        if abs(coord) > 180:
            coord /= 10

        if (
            LIMITE_LAT_MIN <= coord <= LIMITE_LAT_MAX
            or LIMITE_LON_MIN <= coord <= LIMITE_LON_MAX
        ):
            return coord
        else:
            print(f"⚠️ Coordenada suspeita detectada: {coord} (IGNORADO)")
            return None
    except ValueError:
        print(f"⚠️ Erro ao converter coordenada: {coord}")
        return None


# 🚗 Obter rotas via Google Maps API
def obter_rota_google_maps(lat1, lon1, lat2, lon2):
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={lat1},{lon1}&destination={lat2},{lon2}&mode=driving&key={GOOGLE_API_KEY}"
    )

    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "OK":
            overview_polyline = data["routes"][0]["overview_polyline"]["points"]
            overview_coords = polyline.decode(overview_polyline)
            overview_coords = [(lng, lat) for lat, lng in overview_coords]
            return overview_coords
        else:
            print(f"⚠️ API do Google não retornou rota válida: {data.get('status')}")
    except Exception as e:
        print(f"❌ Erro ao buscar rota: {e}")

    return None


# 🔨 Gerar o KML
def gerar_kml(file_path, output_kml):
    print("🔄 Lendo o arquivo Excel...")
    try:
        df = pd.read_excel(file_path, dtype=str)
    except Exception as e:
        print("❌ Erro ao ler o arquivo: " + str(e))
        return

    df.columns = df.columns.str.strip()

    required_columns = {
        "Ano",
        "Tipo",
        "kmi",
        "kmf",
        "Sentido",
        "lati",
        "longi",
        "latf",
        "longf",
    }
    if not required_columns.issubset(df.columns):
        print(
            "❌ Erro: O arquivo Excel não contém todas as colunas necessárias:",
            required_columns,
        )
        return

    kml = simplekml.Kml()
    anos_folders = {}

    for _, row in df.iterrows():
        ano = row["Ano"].strip()
        tipo = row["Tipo"].strip()
        sentido = (
            str(row["Sentido"]).strip()
            if pd.notna(row["Sentido"]) and row["Sentido"] != "0"
            else None
        )
        kmi = row["kmi"].strip()
        kmf = row["kmf"].strip()

        lati = corrigir_coordenada(row["lati"])
        longi = corrigir_coordenada(row["longi"])
        latf = corrigir_coordenada(row["latf"])
        longf = corrigir_coordenada(row["longf"])

        if lati is None or longi is None:
            print(f"❌ Ponto ignorado (coordenadas suspeitas): {tipo} - {kmi}")
            continue

        if ano not in anos_folders:
            anos_folders[ano] = kml.newfolder(name=f"Ano {ano}")

        ano_folder = anos_folders[ano]

        tipo_folder = None
        for f in ano_folder.features:
            if f.name == tipo:
                tipo_folder = f
                break

        if not tipo_folder:
            tipo_folder = ano_folder.newfolder(name=tipo)

        # Criar subpasta de sentido apenas se houver sentido válido
        sentido_folder = tipo_folder
        if sentido:
            sentido_folder = None
            for f in tipo_folder.features:
                if f.name == f"Sentido {sentido}":
                    sentido_folder = f
                    break
            if not sentido_folder:
                sentido_folder = tipo_folder.newfolder(name=f"Sentido {sentido}")

        cor_pino = cores_por_tipo.get(tipo, "ff00ff00")
        icone_pino = icones_por_tipo.get(tipo, None)

        nome_ponto = (
            f"{tipo} - km {kmi} ({sentido})" if sentido else f"{tipo} - km {kmi}"
        )

        pnt_inicio = sentido_folder.newpoint(name=nome_ponto, coords=[(longi, lati)])
        pnt_inicio.style.iconstyle.color = cor_pino
        pnt_inicio.style.iconstyle.scale = 1.2
        if icone_pino:
            pnt_inicio.style.iconstyle.icon.href = icone_pino

        print(f"✅ Ponto adicionado: {nome_ponto} ({lati}, {longi})")

        # Criar ponto final e rota apenas se houver coordenadas de fim
        if latf is not None and longf is not None and kmi != kmf:
            nome_fim = f"{tipo} Fim - {kmf}"
            pnt_fim = sentido_folder.newpoint(name=nome_fim, coords=[(longf, latf)])
            pnt_fim.style.iconstyle.color = cor_pino
            pnt_fim.style.iconstyle.scale = 1.2

            print(f"✅ Ponto final adicionado: {nome_fim} ({latf}, {longf})")

            # 🔹 Adicionando rota entre início e fim
            rota_coords = obter_rota_google_maps(lati, longi, latf, longf)
            if rota_coords:
                route = sentido_folder.newlinestring(name=f"Rota {kmi} a {kmf}")
                route.coords = rota_coords
                route.style.linestyle.color = cor_pino
                route.style.linestyle.width = 3
                print(f"🚗 Rota adicionada entre {nome_ponto} e {nome_fim}")

    kml.save(output_kml)
    print(f"🎉 Arquivo KML gerado: '{output_kml}'! 🚀")


# --- EXECUTAR O SCRIPT ---
file_path = "Lista_EPR.xlsx"
output_kml = "Lista_OK.kml"

gerar_kml(file_path, output_kml)
