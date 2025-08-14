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
        # Verifica se os arquivos são válidos
        if arquivo_erp is None or arquivo_marketplace is None:
            raise ValueError("Arquivo(s) inválido(s) recebido(s)")

        # 1. Ler ambos os arquivos
        df_erp = ler_arquivo(arquivo_erp)
        df_market = ler_arquivo(arquivo_marketplace)
        
        # 2. Identificar o marketplace
        marketplace_nome = identificar_marketplace(df_market)
        if not marketplace_nome:
            raise ValueError("Não foi possível identificar o marketplace pelo formato do arquivo")
        
        # Obter configurações do marketplace
        marketplace_config = MAPA_MARKETPLACES[marketplace_nome]  # <-- Definição aqui
        
        # 3. Comparar os dados
        df_resultado = comparar_dados(df_erp, df_market, marketplace_nome)
        
        # 4. Filtrar só divergências
        divergencias = df_resultado[df_resultado['DIFERENCA_PRAZO'] != 0].copy()
        
        # 5. Gerar logs e resumo
        log = gerar_log(df_resultado, marketplace_nome)  # <-- Definição aqui
        resumo = gerar_resumo(df_resultado, marketplace_nome)  # <-- Definição aqui
        
        # 6. Salvar resultado
        nome_arquivo = f"divergencias_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"  # <-- Definição aqui
        caminho = os.path.join(pasta_upload, nome_arquivo)
        
        cols_saida = ['COD_COMPARACAO', 'DIAS_PRAZO_ERP', 'DIAS_PRAZO_MARKETPLACE', 'DIFERENCA_PRAZO']
        divergencias[cols_saida].to_excel(caminho, index=False)
        
        # 7. Retornar resultado (TODAS AS VARIÁVEIS JÁ DEFINIDAS)
        return {
            'sucesso': True,
            'arquivo': nome_arquivo,  # Nome do arquivo gerado
            'total_itens': len(df_resultado),
            'divergencias': len(divergencias),
            'log': gerar_log(df_resultado, marketplace_nome),
            'marketplace': {
                'nome': marketplace_nome,
                'imagem': f"/static/img/{marketplace_config['imagem']}"
            }
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }
    
def ler_arquivo(arquivo):
    """Função robusta para ler arquivos Excel/CSV"""
    if arquivo is None or arquivo.filename == '':
        raise ValueError("Nenhum arquivo foi enviado ou arquivo inválido")

    try:
        # Verifica se é um objeto de arquivo válido
        if not hasattr(arquivo, 'filename') or not hasattr(arquivo, 'save'):
            raise ValueError("Objeto de arquivo inválido")

        # Cria pasta de upload se não existir
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Cria caminho seguro
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(arquivo.filename))
        
        # Salva o arquivo temporariamente
        arquivo.save(temp_path)
        
        # Verifica se o arquivo foi salvo
        if not os.path.exists(temp_path):
            raise ValueError("Falha ao salvar arquivo temporário")

        # Processa conforme a extensão
        if arquivo.filename.lower().endswith('.xlsx'):
            df = pd.read_excel(temp_path, engine='openpyxl', dtype=str)
        elif arquivo.filename.lower().endswith('.xls'):
            try:
                df = pd.read_excel(temp_path, engine='xlrd', dtype=str)
            except:
                # Fallback para openpyxl se xlrd falhar
                df = pd.read_excel(temp_path, engine='openpyxl', dtype=str)
        elif arquivo.filename.lower().endswith('.csv'):
            df = pd.read_csv(temp_path, encoding='latin1', sep=None, engine='python', dtype=str)
        else:
            raise ValueError("Formato de arquivo não suportado")

        # Remove arquivo temporário
        os.remove(temp_path)
        
        return df

    except Exception as e:
        # Limpeza em caso de erro
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        raise ValueError(f"Erro ao processar arquivo {arquivo.filename if arquivo else 'None'}: {str(e)}")

def identificar_marketplace(df):
    """Identifica o marketplace baseado nas colunas presentes"""
    colunas = df.columns.tolist()
    for marketplace, config in MAPA_MARKETPLACES.items():
        if config['prazo'] in colunas:
            return marketplace
    return None

def comparar_dados(df_erp, df_marketplace, marketplace):
    """Realiza a comparação de prazos entre ERP e Marketplace"""
    config = MAPA_MARKETPLACES[marketplace]
    
    # Pré-processamento do Marketplace
    df_market = df_marketplace.rename(columns={
        config['cod_barra']: 'COD_COMPARACAO',
        config['prazo']: 'DIAS_PRAZO_MARKETPLACE'
    }).copy()
    
    # Pré-processamento do ERP
    coluna_chave_erp = 'COD AUXILIAR' if marketplace == 'Mobly' else 'COD BARRA'
    df_erp = df_erp.rename(columns={
        config['prazo_erp']: 'DIAS_PRAZO_ERP'
    }).copy()
    
    # Tratamento especial para Tray
    if marketplace == 'Tray':
        df_market['DIAS_PRAZO_MARKETPLACE'] = df_market['DIAS_PRAZO_MARKETPLACE'].apply(extrair_numeros)
    
    # Converter códigos para string
    df_erp[coluna_chave_erp] = df_erp[coluna_chave_erp].astype(str).str.strip()
    df_market['COD_COMPARACAO'] = df_market['COD_COMPARACAO'].astype(str).str.strip()
    
    # Merge dos dados
    df_resultado = pd.merge(
        df_erp,
        df_market,
        left_on=coluna_chave_erp,
        right_on='COD_COMPARACAO',
        how='inner',
        suffixes=('_ERP', '_MARKETPLACE')
    )
    
    # Converter prazos para numérico
    df_resultado['DIAS_PRAZO_ERP'] = pd.to_numeric(df_resultado['DIAS_PRAZO_ERP'], errors='coerce').fillna(0)
    df_resultado['DIAS_PRAZO_MARKETPLACE'] = pd.to_numeric(df_resultado['DIAS_PRAZO_MARKETPLACE'], errors='coerce').fillna(0)
    
    # Calcular diferença
    df_resultado['DIFERENCA_PRAZO'] = df_resultado['DIAS_PRAZO_MARKETPLACE'] - df_resultado['DIAS_PRAZO_ERP']
    
    # Ordenar por maior divergência
    df_resultado = df_resultado.sort_values('DIFERENCA_PRAZO', ascending=False, key=abs)
    
    return df_resultado

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
       # f"<span style='color: blue; font-weight: bold;'>Marketplace: {marketplace}</span>",
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