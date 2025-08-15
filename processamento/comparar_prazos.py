import pandas as pd
import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app as app

# Configuração dos marketplaces (mantida do seu código original)
MAPA_MARKETPLACES = {
    "Wake": {
        "cod_barra": "EAN",
        "prazo": "Prazo Manuseio (Dias)",
        "chave_comparacao": "EAN",
        "prazo_erp": "DIAS P/ ENTREGA",
        "imagem": "wake.png"
    },
    "Tray": {
        "cod_barra": "EAN",
        "prazo": "Disponibilidade",
        "chave_comparacao": "EAN",
        "prazo_erp": "SITE_DISPONIBILIDADE",
        "imagem": "tray.png"
    },
    "Shoppe": {
        "cod_barra": "EAN_shoppe",
        "prazo": "Disponibilidade_shoppe",
        "chave_comparacao": "EAN",
        "prazo_erp": "SITE_DISPONIBILIDADE",
        "imagem": "shoppe.png"
    },
    "Mobly": {
        "cod_barra": "SellerSku",
        "prazo": "SupplierDeliveryTime",
        "chave_comparacao": "SellerSku",
        "prazo_erp": "SITE_DISPONIBILIDADE",
        "imagem": "mobly.png"
    },
    "MadeiraMadeira": {
        "cod_barra": "EAN",
        "prazo": "Prazo expedição",
        "chave_comparacao": "EAN",
        "prazo_erp": "SITE_DISPONIBILIDADE",
        "imagem": "madeiramadeira.png"
    },
    "WebContinental": {
        "cod_barra": "EAN",
        "prazo": "Crossdoc",
        "chave_comparacao": "EAN",
        "prazo_erp": "SITE_DISPONIBILIDADE",
        "imagem": "webcontinental.png"
    }
}

def processar_comparacao(arquivo_erp, arquivo_marketplace, pasta_upload):
    try:
        # 1. Ler arquivos
        df_erp = ler_arquivo(arquivo_erp)
        df_market = ler_arquivo(arquivo_marketplace)
        
        # 2. Identificar marketplace
        marketplace_nome = identificar_marketplace(df_market)
        if not marketplace_nome:
            raise ValueError("Marketplace não identificado")
        
        # 3. Comparar dados
        df_resultado = comparar_dados(df_erp, df_market, marketplace_nome)
        
        # 4. Filtrar divergências
        divergencias = df_resultado[df_resultado['DIFERENCA_PRAZO'] != 0].copy()
        
        # 5. Gerar logs para exibição
        log = gerar_log(df_resultado, marketplace_nome)
        resumo = gerar_resumo(df_resultado, marketplace_nome)
        
        # 6. Salvar arquivo com todas colunas
        nome_arquivo = f"divergencias_{marketplace_nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        caminho = os.path.join(pasta_upload, nome_arquivo)
        os.makedirs(pasta_upload, exist_ok=True)
        
        # Salva apenas as divergências com todas colunas
        divergencias.to_excel(caminho, index=False)

        # 7. Preparar resultado com logs
        return {
            'sucesso': True,
            'arquivo': nome_arquivo,
            'total_itens': len(df_resultado),
            'divergencias': len(divergencias),
            'log': log,  # Mantém os logs para exibição
            'resumo': resumo,  # Mantém o resumo para exibição
            'marketplace': {
                'nome': marketplace_nome,
                'imagem': f"/static/img/{MAPA_MARKETPLACES[marketplace_nome]['imagem']}"
            },
            'itens_processados': [
                {
                    'ean': str(row['COD_COMPARACAO']),
                    'nome': row.get('DESCRICAO_ERP', 'Produto não identificado'),
                    'status': 'erro',
                    'detalhes': f"ERP: {row['DIAS_PRAZO_ERP']}d | Marketplace: {row['DIAS_PRAZO_MARKETPLACE']}d",
                    'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                for _, row in divergencias.iterrows()
            ]
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'itens_processados': [{
                'ean': '0000000000000',
                'nome': 'Processamento de prazos',
                'status': 'erro',
                'detalhes': str(e),
                'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
        }

def ler_arquivo(arquivo):
    """Função robusta para ler arquivos Excel/CSV com tratamento de encoding"""
    if arquivo is None or arquivo.filename == '':
        raise ValueError("Nenhum arquivo foi enviado ou arquivo inválido")

    try:
        # Cria pasta de upload se não existir
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(arquivo.filename))
        arquivo.save(temp_path)

        # Processa conforme a extensão
        if arquivo.filename.lower().endswith('.csv'):
            # Tenta detectar encoding automaticamente
            def detect_encoding(file_path):
                import chardet
                with open(file_path, 'rb') as f:
                    result = chardet.detect(f.read(10000))
                return result['encoding']

            encoding = detect_encoding(temp_path)
            
            # Tenta múltiplas combinações de encoding e separador
            for enc in [encoding, 'latin1', 'ISO-8859-1', 'utf-8', 'windows-1252']:
                for sep in [';', ',', '\t']:
                    try:
                        df = pd.read_csv(temp_path, 
                                        encoding=enc,
                                        sep=sep,
                                        dtype=str,
                                        on_bad_lines='warn')
                        print(f"Arquivo lido com encoding: {enc} e separador: {repr(sep)}")
                        break
                    except Exception as e:
                        continue
                else:
                    continue
                break
            else:
                raise ValueError("Não foi possível ler o arquivo CSV com nenhum encoding/separador conhecido")
        elif arquivo.filename.lower().endswith(('.xlsx', '.xls')):
            try:
                # Primeiro tenta com openpyxl (para .xlsx)
                df = pd.read_excel(temp_path, engine='openpyxl', dtype=str)
            except:
                try:
                    # Se falhar, tenta com xlrd (para .xls mais antigos)
                    df = pd.read_excel(temp_path, engine='xlrd', dtype=str)
                except Exception as e:
                    # Verifica se o arquivo está corrompido
                    if not os.path.getsize(temp_path):
                        raise ValueError("Arquivo Excel está vazio ou corrompido")
                    else:
                        raise ValueError(f"Erro ao ler arquivo Excel: {str(e)}")
        else:
            raise ValueError("Formato de arquivo não suportado")

        # Remove arquivo temporário
        os.remove(temp_path)
        return df

    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        raise ValueError(f"Erro ao processar arquivo {arquivo.filename}: {str(e)}")

def identificar_marketplace(df):
    """Identifica o marketplace baseado nas colunas presentes"""
    colunas = df.columns.tolist()
    for marketplace, config in MAPA_MARKETPLACES.items():
        if config['prazo'] in colunas:
            return marketplace
    return None

def comparar_dados(df_erp, df_marketplace, marketplace):
    """Realiza a comparação de prazos mantendo todas as colunas originais"""
    config = MAPA_MARKETPLACES[marketplace]
    
    # Cria cópias para não modificar os originais
    df_market = df_marketplace.copy()
    df_erp_copy = df_erp.copy()

    # Pré-processamento do Marketplace
    df_market['COD_COMPARACAO'] = df_market[config['cod_barra']].astype(str).str.strip()
    df_market['DIAS_PRAZO_MARKETPLACE'] = df_market[config['prazo']]
    
    # Pré-processamento do ERP
    coluna_chave_erp = 'COD AUXILIAR' if marketplace == 'Mobly' else 'COD BARRA'
    df_erp_copy['COD_COMPARACAO_ERP'] = df_erp_copy[coluna_chave_erp].astype(str).str.strip()
    df_erp_copy['DIAS_PRAZO_ERP'] = df_erp_copy[config['prazo_erp']]
    
    # Tratamento especial para Tray
    if marketplace == "Tray":
        df_market['DIAS_PRAZO_MARKETPLACE'] = df_market['DIAS_PRAZO_MARKETPLACE'].apply(extrair_numeros)
    
    # Merge mantendo TODAS as colunas originais
    df_comparacao = pd.merge(
        df_erp_copy,
        df_market,
        left_on='COD_COMPARACAO_ERP',
        right_on='COD_COMPARACAO',
        how='inner',
        suffixes=('_ERP', '_MARKET')
    )
    
    # Converter prazos para numérico
    df_comparacao['DIAS_PRAZO_ERP'] = pd.to_numeric(df_comparacao['DIAS_PRAZO_ERP'], errors='coerce').fillna(0)
    df_comparacao['DIAS_PRAZO_MARKETPLACE'] = pd.to_numeric(df_comparacao['DIAS_PRAZO_MARKETPLACE'], errors='coerce').fillna(0)
    
    # Calcular diferença
    df_comparacao['DIFERENCA_PRAZO'] = df_comparacao['DIAS_PRAZO_MARKETPLACE'] - df_comparacao['DIAS_PRAZO_ERP']
    
    return df_comparacao.sort_values('DIFERENCA_PRAZO', ascending=False, key=abs)

def extrair_numeros(texto):
    """Função auxiliar para extrair números de strings (usado para Tray)"""
    if pd.isna(texto):
        return 0
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 0

def gerar_log(df, marketplace):
    """Gera o conteúdo do log para exibição na interface"""
    divergencias = df[df['DIFERENCA_PRAZO'] != 0]
    log_lines = [
        f"<span style='color: black; font-weight: bold;font-size: 20px'>Anuncios Analisados: {len(df)}</span>",
        f"<span style='color: red;font-weight: bold; font-size: 25px'>Anuncios com Divergência: {len(divergencias)}</span>",
    ]
    
    return "<br>".join(log_lines)

def gerar_resumo(df, marketplace):
    """Gera um resumo estatístico da comparação"""
    total_itens = len(df)
    total_divergencias = len(df[df['DIFERENCA_PRAZO'] != 0])
    pct_divergencias = (total_divergencias / total_itens * 100) if total_itens > 0 else 0
    
    return (
        f"<strong>Marketplace:</strong> {marketplace}<br>"
        f"<strong>Itens analisados:</strong> {total_itens}<br>"
        f"<strong>Itens com divergência:</strong> {total_divergencias} ({pct_divergencias:.1f}%)<br>"
    )