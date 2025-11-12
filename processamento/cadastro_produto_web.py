import os
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle
from datetime import datetime
from openpyxl.worksheet.datavalidation import DataValidation
import warnings
from datetime import datetime
import logging
import re
import unicodedata
from processamento.google_sheets import ler_planilha_google

PLANILHA_MODELO_FIXA = "Template_Produtos_Mpozenato_Cadastro_.xlsx"  # Nome do arquivo modelo fixo

warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

logger = logging.getLogger('cadastro')  # Usa o nome correspondente

def sanitize_filename(texto):
    """Remove acentos, caracteres especiais e sanitiza para nome de arquivo"""
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'[^\w\-_]', '', texto).strip().replace(' ', '_')

def copiar_validacoes(worksheet):
    return list(worksheet.data_validations.dataValidation)

def reaplicar_validacoes(worksheet, validacoes):
    for dv in validacoes:
        worksheet.add_data_validation(dv)

def executar_processamento(planilha_origem, planilha_destino=None):

    inicio = datetime.now()
    produtos_processados = []

    # 🔹 SE planilha_destino NÃO FOR FORNECIDA, USA O MODELO FIXO
    if planilha_destino is None:
        modelo_path = Path(__file__).parent.parent / "modelos" / PLANILHA_MODELO_FIXA
        if not modelo_path.exists():
            raise Exception(f"Modelo ATHUS fixo não encontrado em: {modelo_path}")
        planilha_destino = str(modelo_path)
        print(f"✅ Usando modelo fixo: {planilha_destino}")

    # 🔹 Lê planilha
    if isinstance(planilha_origem, dict):
        sheet_id = planilha_origem['sheet_id']
        aba_nome = planilha_origem['aba']
        df = ler_planilha_google(sheet_id, aba_nome)
    else:
        df = pd.read_excel(planilha_origem)

    # 🔹 Remove linhas completamente vazias
    df = df.dropna(how="all")

    # 🔹 Remove repetições de cabeçalhos no meio da planilha
    df = df[~df.apply(
        lambda row: all(str(row[c]).strip().upper() == c.upper() for c in df.columns if c in row),
        axis=1
    )]

    colunas_esperadas = [
        "EAN", "NOMEONCLICK", "NOMEE-COMMERCE", "TIPODEPRODUTO",
        "EMBALTURA", "EMBLARGURA", "EMBCOMPRIMENTO", "VOLUMES",
        "EANCOMPONENTES", "MARCA", "CUSTO", "DE", "POR", "FORNECEDOR",
        "OUTROS","IPI", "FRETE", "NCM", "CODFORN", "CATEGORIA", "GRUPO",
        "COMPLEMENTO", "DISPONIBILIDADEWEB", "DESCRICAOHTML", "PESOBRUTO",
        "PESOLIQUIDO", "VOLPESOBRUTO", "VOLPESOLIQ", "VOLLARGURA",
        "VOLALTURA", "VOLCOMPRIMENTO", "CATEGORIAPRINCIPALTRAY",
        "CATEGORIAPRINCIPALCORP", "NIVELADICIONAL1CORP", "CUSTOTOTAL"
    ]

    colunas_faltando = [col for col in colunas_esperadas if col not in df.columns]
    if colunas_faltando:
        raise Exception(f"Planilha Online faltando as seguintes colunas: {', '.join(colunas_faltando)}")

    logs = []
    dados_sheets = {
        "PRODUTO": [],
        "PRECO": [],
        "LOJA WEB": [],
        "KIT": [],
        "VOLUME": []
    }

    produto_dict = {
        str(row["EAN"]).strip(): row["NOMEONCLICK"] if pd.notna(row["NOMEONCLICK"]) else "Nome Desconhecido"
        for _, row in df.iterrows()
    }

    marcas_cadastradas = set()
    data_atual = datetime.now()
    data_formatada = data_atual.strftime("%d/%m/%Y")
    data_mais_20_anos = data_atual.replace(year=data_atual.year + 30)
    data_formatada_mais_20_anos = data_mais_20_anos.strftime("%d/%m/%Y")

    # 🔹 Remove linhas onde EAN, MARCA, ou outras colunas tenham o nome da coluna (ex: "EAN", "MARCA", "VOLUMES")
    df = df[~df.apply(lambda row: any(
        str(row[c]).strip().upper() == c.upper() for c in df.columns if pd.notna(row[c])
    ), axis=1)]
    
    for idx, row in df.iterrows():
        ean = str(row["EAN"]).strip()
        nome_onclick = row["NOMEONCLICK"]
        nome_ecommerce = row["NOMEE-COMMERCE"]
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Anuncio Criado: {ean} - {nome_ecommerce}")
        tipo_produto = str(row["TIPODEPRODUTO"]).strip().upper() if pd.notna(row["TIPODEPRODUTO"]) else ""
        altura = row["EMBALTURA"]
        largura = row["EMBLARGURA"]
        comprimento = row["EMBCOMPRIMENTO"]

        # 🔹 Corrige o erro de conversão de "VOLUMES"
        try:
            volumes = int(float(row["VOLUMES"])) if pd.notna(row["VOLUMES"]) else 1
        except Exception:
            volumes = 1

        componentes = row["EANCOMPONENTES"]
        marca = row["MARCA"]
        custo = row["CUSTO"]
        preco_venda = row["DE"]
        preco_promo = row["POR"]
        fornecedor = row["FORNECEDOR"]
        outros = row["OUTROS"]
        ipi = row["IPI"]
        frete = row["FRETE"]
        ncm = row["NCM"]
        cod_forn = row["CODFORN"]
        categoria = row["CATEGORIA"]
        grupo = row["GRUPO"]

        marca_web = nome_ecommerce.split("-")[-1].strip() if isinstance(nome_ecommerce, str) and "-" in nome_ecommerce else ""
        complemento = row["COMPLEMENTO"]
        disponibilidade_web = row["DISPONIBILIDADEWEB"]
        descricao_html = row["DESCRICAOHTML"]
        peso_bruto = row["PESOBRUTO"]
        peso_liquido = row["PESOLIQUIDO"]
        vol_peso_bruto = row["VOLPESOBRUTO"]
        vol_peso_liquido = row["VOLPESOLIQ"]
        vol_largura = row["VOLLARGURA"]
        vol_altura = row["VOLALTURA"]
        vol_comprimento = row["VOLCOMPRIMENTO"]
        tipo_produto_valor = 0 if tipo_produto == "ACABADO" else 2
        nome_reduzido = nome_onclick[:25] if isinstance(nome_onclick, str) else ""

        marcas_cadastradas.add(marca)

        dados_sheets["PRODUTO"].append([
            ean, cod_forn, tipo_produto_valor, nome_onclick, nome_reduzido, nome_onclick, nome_onclick, None,
            marca, categoria, grupo, None, None, complemento, None, None, "F", "F", "F", None, volumes,
            peso_bruto, peso_liquido, largura, altura, comprimento, None, 90, 1000,
            disponibilidade_web, "F", "F", ncm, None, "0", "T", "F", "F", "NAO", nome_ecommerce, marca_web,
            "90 dias após o recebimento do produto", disponibilidade_web, descricao_html, "F", "F"
        ])

        if tipo_produto == "KIT" and pd.notna(componentes):
            componentes_list = str(componentes).split("/")
            componentes_contados = {}
            for comp in componentes_list:
                comp_ean = comp.strip()
                componentes_contados[comp_ean] = componentes_contados.get(comp_ean, 0) + 1
            for comp_ean, quantidade in componentes_contados.items():
                nome_componente = produto_dict.get(comp_ean, "Desconhecido")
                dados_sheets["KIT"].append([ean, comp_ean, nome_componente, str(quantidade), "", "0"])

        for i in range(volumes):
            if volumes == 1:
                dados_sheets["VOLUME"].append([
                    ean, nome_onclick, peso_bruto, peso_liquido, largura, altura, "",
                    comprimento, "", "BOX", "T", i + 1
                ])
            else:
                dados_sheets["VOLUME"].append([
                    ean, nome_onclick, vol_peso_bruto, vol_peso_liquido, vol_largura, vol_altura, "",
                    vol_comprimento, "", "BOX", "T", i + 1
                ])

        dados_sheets["PRECO"].append([
            ean, fornecedor, custo, ipi, "", frete, row["CUSTOTOTAL"], preco_venda, preco_promo, preco_promo,
            data_formatada, data_formatada_mais_20_anos, "", "F"
        ])

        dados_sheets["LOJA WEB"].append([
            ean, "", "", "", row["CATEGORIAPRINCIPALTRAY"], "", "", "", "T", "F", "", "", "",
            row["CATEGORIAPRINCIPALCORP"], row["NIVELADICIONAL1CORP"], "", "", "T", "T"
        ])

        produtos_processados.append({
            'ean': ean,
            'nome': nome_ecommerce,
            'status': 'sucesso',
            'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    wb = load_workbook(planilha_destino)
    estilo_invisivel = NamedStyle(name="aspas_invisiveis")
    estilo_invisivel.number_format = '@'
    wb.add_named_style(estilo_invisivel)

    ws_tipo_importacao = wb["Tipo Importacao"]
    validacoes_tipo_importacao = copiar_validacoes(ws_tipo_importacao)

    for sheet_name, data in dados_sheets.items():
        ws = wb[sheet_name]
        start_row = 3 if sheet_name == "PRODUTO" else 2

        for row in ws.iter_rows(min_row=start_row, max_row=ws.max_row):
            for cell in row:
                cell.value = None

        for i, row_data in enumerate(data, start=start_row):
            for j, value in enumerate(row_data, start=1):
                ws.cell(row=i, column=j, value=value)

    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            if cell.value == "'":
                cell.style = "aspas_invisiveis"
                cell.value = "'"
                cell.fill = None

    marcas_validas = [m for m in marcas_cadastradas if isinstance(m, str) and m.strip() and m.strip().upper() != "MARCA"]

    marca_unica = next(iter(marcas_validas)) if marcas_validas else "saida"
    marca_sanitizada = sanitize_filename(marca_unica)
    novo_nome = f"Template_Produtos_Mpozenato_Cadastro_{marca_sanitizada}.xlsx"
    caminho_saida = os.path.join("uploads", novo_nome)

    wb.save(caminho_saida)

    # 🔁 Reabre para reaplicar validações da aba "Tipo Importacao"
    wb = load_workbook(caminho_saida)
    ws_tipo_importacao = wb["Tipo Importacao"]
    reaplicar_validacoes(ws_tipo_importacao, validacoes_tipo_importacao)
    wb.save(caminho_saida)

    fim = datetime.now()
    duracao = (fim - inicio).total_seconds()
    qtd_produtos = len(df)

    # Salva log
    with open('uploads/logs_processamento.txt', 'w', encoding='utf-8') as f:
        for linha in logs:
            f.write(linha + '\n')

    return caminho_saida, qtd_produtos, duracao, produtos_processados
