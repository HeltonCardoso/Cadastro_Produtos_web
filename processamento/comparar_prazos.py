import pandas as pd
import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app as app  # Acesso ao Flask app

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
            'arquivo': nome_arquivo,
            'total_itens': len(df_resultado),
            'divergencias': len(divergencias),
            'log': log,
            'resumo': resumo,
            'marketplace': {
                'nome': marketplace_nome,
                'imagem': f"/static/img/{marketplace_config['imagem']}"  # Caminho completo
            }
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }
    

def ler_arquivo(arquivo):
    """Função robusta para ler tanto Excel quanto CSV"""
    try:
        # Garantir que a pasta de upload existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Criar caminho seguro para o arquivo temporário
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(arquivo.filename))
        arquivo.save(temp_path)
        
        if arquivo.filename.lower().endswith('.csv'):
            # Primeiro detectar o delimitador
            with open(temp_path, 'r', encoding='latin1') as f:
                first_lines = [f.readline() for _ in range(5)]
            
            # Verificar delimitadores comuns
            for delim in [';', ',', '\t', '|']:
                if delim in first_lines[0]:
                    df = pd.read_csv(temp_path, delimiter=delim, encoding='latin1', 
                                   on_bad_lines='skip', dtype=str)
                    break
            else:
                # Se nenhum delimitador for óbvio, tentar automático
                df = pd.read_csv(temp_path, encoding='latin1', 
                               sep=None, engine='python', dtype=str)
            
        elif arquivo.filename.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(temp_path, dtype=str)
        else:
            raise ValueError("Formato de arquivo não suportado")
        
        # Remover arquivo temporário
        os.remove(temp_path)
        
        # Converter colunas numéricas
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['prazo', 'dias', 'dia', 'entrega']):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise ValueError(f"Erro ao ler arquivo {arquivo.filename}: {str(e)}")

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
       # "<hr>",
       # "<strong>PRINCIPAIS DIVERGÊNCIAS:</strong>"
    ]
    
    # Adiciona as top 10 divergências
   # for _, row in divergencias.head(10).iterrows():
    #    cor = "red" if row['DIFERENCA_PRAZO'] > 0 else "blue"
     #   log_lines.append(
    
      #      f"<span style='color: {cor}'>"
       #     f"EAN/SKU: {row['COD_COMPARACAO']} | "
        #    f"ERP: {row['DIAS_PRAZO_ERP']}d | "
         #   f"Marketplace: {row['DIAS_PRAZO_MARKETPLACE']}d | "
          #  f"Diferença: <strong>{row['DIFERENCA_PRAZO']}d</strong>"
          #  "</span>"
       # )
    
    return "<br>".join(log_lines)

def gerar_resumo(df, marketplace):
    """Gera um resumo estatístico da comparação"""
    total_itens = len(df)
    total_divergencias = len(df[df['DIFERENCA_PRAZO'] != 0])
    pct_divergencias = (total_divergencias / total_itens * 100) if total_itens > 0 else 0
    
   # maior_diferenca_positiva = df['DIFERENCA_PRAZO'].max()
   # maior_diferenca_negativa = df['DIFERENCA_PRAZO'].min()
    
    return (
        f"<strong>Marketplace:</strong> {marketplace}<br>"
        f"<strong>Itens analisados:</strong> {total_itens}<br>"
        f"<strong>Itens com divergência:</strong> {total_divergencias} ({pct_divergencias:.1f}%)<br>"
       # f"<strong>Maior atraso no ERP:</strong> {abs(maior_diferenca_negativa)} dias<br>"
       # f"<strong>Maior atraso no Marketplace:</strong> {maior_diferenca_positiva} dias"
    )