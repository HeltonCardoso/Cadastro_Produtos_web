import os
import requests
import json
from typing import Dict, Any
import logging
from datetime import datetime

# ======================================================
# NOVA IMPORT: Usando token manager do banco de dados
# ======================================================
from utils.token_manager_db import salvar_token, obter_token, remover_token

logger = logging.getLogger(__name__)


class AnyMarketAPI:
    """Classe para interagir com a API do AnyMarket - VERSÃO COMPLETA"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.anymarket.com.br/v2"
        self.headers = {
            "Content-Type": "application/json",
            "gumgaToken": token
        }
    
    # ======================================================
    # MÉTODOS DE FOTOS (já existentes)
    # ======================================================
    
    def buscar_fotos_produto(self, product_id: str) -> Dict[str, Any]:
        """Busca fotos de um produto específico"""
        try:
            url = f"{self.base_url}/products/{product_id}/images"
            logger.info(f"Consultando API AnyMarket - Produto: {product_id}")
            
            print(f"🔍 Fazendo requisição para: {url}")
            print(f"📋 Headers: {self.headers}")
            
            response = requests.get(url, headers=self.headers, timeout=60)
            
            resultado = {
                "sucesso": response.status_code == 200,
                "status_code": response.status_code,
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url
            }
            
            print(f"📡 Resposta da API: {response.status_code}")
            
            if response.status_code == 200:
                dados = response.json()
                print(f"📊 Dados recebidos: {len(dados)} fotos")
                fotos_processadas = self._processar_fotos_v2(dados)
                resultado["dados"] = fotos_processadas
                resultado["quantidade_fotos"] = len(fotos_processadas)
                logger.info(f"Consulta bem-sucedida - {resultado['quantidade_fotos']} fotos encontradas")
            elif response.status_code == 401:
                resultado["erro"] = "Token inválido ou não autorizado"
                logger.error("Erro 401 - Token inválido")
            elif response.status_code == 404:
                resultado["erro"] = "Produto não encontrado"
                logger.error("Erro 404 - Produto não encontrado")
            elif response.status_code == 502:
                resultado["erro"] = "Servidor AnyMarket indisponível (Erro 502)."
                logger.error("Erro 502 no AnyMarket - Servidor indisponível")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["detalhes_erro"] = response.text[:500]
                logger.error(f"Erro na consulta: {response.status_code} - {response.text}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro inesperado: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.now().isoformat()
            }

    def _processar_fotos_v2(self, dados: list) -> list:
        """Processa os dados das fotos da API"""
        fotos_processadas = []
        
        for i, foto in enumerate(dados):
            print(f"=== DEBUG FOTO {i} ===")
            print(f"Campos disponíveis: {list(foto.keys())}")
            
            url_imagem = (
                foto.get("url") or 
                foto.get("originalImage") or 
                foto.get("standardUrl") or 
                foto.get("thumbnailUrl") or 
                ""
            )
            
            foto_processada = {
                "id": str(foto.get("id", "")),
                "index": foto.get("index", 0),
                "main": foto.get("main", False),
                "type": foto.get("type", ""),
                "url": url_imagem,
                "original": url_imagem,
                "status": "disponivel" if url_imagem else "indisponivel",
                "debug_campos": list(foto.keys()),
                "thumbnailUrl": foto.get("thumbnailUrl"),
                "lowResolutionUrl": foto.get("lowResolutionUrl"),
                "standardUrl": foto.get("standardUrl"),
                "originalImage": foto.get("originalImage"),
                "status_api": foto.get("status"),
                "width": foto.get("standardWidth"),
                "height": foto.get("standardHeight")
            }
            
            if not url_imagem:
                print(f"❌ Nenhuma URL válida encontrada para foto {foto.get('id')}")
            else:
                print(f"✅ URL encontrada: {url_imagem}")
            
            fotos_processadas.append(foto_processada)
            print("=====================")
        
        return fotos_processadas

    # ======================================================
    # MÉTODO: Buscar canais de transmissão
    # ======================================================
    
    def buscar_canais_transmissao(self, partner_id: str = None) -> Dict[str, Any]:
        """
        Busca os canais/marketplaces com transmissões criadas
        Endpoint: /skus/marketplaces
        """
        try:
            url = f"{self.base_url}/skus/marketplaces"
            
            params = {}
            if partner_id:
                params['partnerID'] = partner_id
            
            logger.info(f"Consultando canais de transmissão - PartnerID: {partner_id}")
            
            print(f"🔍 Fazendo requisição para: {url}")
            print(f"📋 Headers: {self.headers}")
            print(f"📋 Params: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=60)
            
            resultado = {
                "sucesso": response.status_code == 200,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url,
                "params": params
            }
            
            print(f"📡 Resposta da API: {response.status_code}")
            
            if response.status_code == 200:
                dados = response.json()
                print(f"📊 Dados recebidos: {len(dados)} canais")
                resultado["dados"] = dados
                resultado["quantidade"] = len(dados)
                logger.info(f"Consulta bem-sucedida - {resultado['quantidade']} canais encontrados")
            elif response.status_code == 401:
                resultado["erro"] = "Token inválido ou não autorizado"
                resultado["dados"] = []
                logger.error("Erro 401 - Token inválido")
            elif response.status_code == 404:
                resultado["erro"] = "Endpoint não encontrado"
                resultado["dados"] = []
                logger.error("Erro 404 - Endpoint não encontrado")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["dados"] = []
                resultado["detalhes_erro"] = response.text[:500]
                logger.error(f"Erro na consulta: {response.status_code} - {response.text}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro inesperado: {str(e)}",
                "dados": [],
                "timestamp": datetime.now().isoformat()
            }

    # ======================================================
    # MÉTODOS DE EXCLUSÃO (já existentes)
    # ======================================================
    
    def excluir_foto(self, product_id: str, photo_id: str) -> Dict[str, Any]:
        """Exclui uma foto específica de um produto"""
        try:
            url = f"{self.base_url}/products/{product_id}/images/{photo_id}"
            logger.info(f"Excluindo foto - Produto: {product_id}, Foto: {photo_id}")
            
            print(f"🗑️ Fazendo DELETE para: {url}")
            
            response = requests.delete(url, headers=self.headers, timeout=30)
            
            resultado = {
                "sucesso": response.status_code in [200, 204],
                "status_code": response.status_code,
                "product_id": product_id,
                "photo_id": photo_id,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url
            }
            
            print(f"📡 Resposta DELETE: {response.status_code}")
            
            if response.status_code in [200, 204]:
                logger.info(f"Foto excluída com sucesso - Produto: {product_id}, Foto: {photo_id}")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["detalhes_erro"] = response.text[:500]
                logger.error(f"Erro ao excluir foto: {response.status_code} - {response.text}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao excluir foto: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro ao excluir foto: {str(e)}",
                "product_id": product_id,
                "photo_id": photo_id,
                "timestamp": datetime.now().isoformat()
            }

    def excluir_fotos_planilha(self, caminho_planilha: str) -> Dict[str, Any]:
        """Exclui fotos baseado em uma planilha Excel"""
        try:
            import pandas as pd
            
            df = pd.read_excel(caminho_planilha, dtype={"ID_PRODUTO": str, "ID_IMG": str})
            df["ID_PRODUTO"] = df["ID_PRODUTO"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            df["ID_IMG"] = df["ID_IMG"].astype(str).str.replace(r"\.0$", "", regex=True).str.replace(".", "", regex=False).str.strip()
            
            resultados = []
            total_sucesso = 0
            total_erro = 0
            
            for _, row in df.iterrows():
                product_id = row["ID_PRODUTO"]
                photo_id = row["ID_IMG"]
                
                if not product_id or not photo_id or product_id == 'nan' or photo_id == 'nan':
                    continue
                
                resultado_exclusao = self.excluir_foto(product_id, photo_id)
                resultados.append(resultado_exclusao)
                
                if resultado_exclusao["sucesso"]:
                    total_sucesso += 1
                else:
                    total_erro += 1
            
            return {
                "sucesso": total_erro == 0,
                "total_processado": len(resultados),
                "total_sucesso": total_sucesso,
                "total_erro": total_erro,
                "resultados": resultados,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar planilha: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro ao processar planilha: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


# ======================================================
# FUNÇÕES GLOBAIS (MODIFICADAS PARA USAR BANCO DE DADOS)
# ======================================================

def salvar_token_anymarket(token: str) -> bool:
    """Salva token do AnyMarket no BANCO DE DADOS"""
    return salvar_token('anymarket', {'token': token})


def obter_token_anymarket_seguro() -> str:
    """
    Obtém token do AnyMarket do BANCO DE DADOS.
    Levanta exceção se não encontrar.
    """
    # 1. Tenta do banco de dados primeiro (PERSISTENTE!)
    data = obter_token('anymarket')
    if data and data.get('token'):
        print(f"✅ Token AnyMarket obtido do BANCO DE DADOS")
        return data['token']
    
    # 2. Fallback para variável de ambiente (desenvolvimento local)
    token = os.environ.get('ANYMARKET_TOKEN')
    if token:
        print(f"⚠️ Token AnyMarket obtido da VARIÁVEL DE AMBIENTE")
        # Migra para o banco
        salvar_token_anymarket(token)
        return token
    
    # 3. Fallback para arquivo antigo (migração única)
    tokens_file = 'tokens_secure.json'
    if os.path.exists(tokens_file):
        try:
            with open(tokens_file, 'r', encoding='utf-8') as f:
                tokens = json.load(f)
            
            # Tenta estrutura nova
            token_data = tokens.get('anymarket')
            if token_data and token_data.get('token'):
                token = token_data['token']
                print(f"🔄 Migrando token do arquivo para o banco de dados")
                salvar_token_anymarket(token)
                return token
            
            # Tenta estrutura antiga
            for key, value in tokens.items():
                if isinstance(value, dict) and value.get('tipo') == 'anymarket' and value.get('token'):
                    token = value['token']
                    print(f"🔄 Migrando token do arquivo antigo para o banco")
                    salvar_token_anymarket(token)
                    return token
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo antigo: {e}")
    
    raise ValueError("Token do AnyMarket não configurado. Configure em /configuracoes/tokens")


def remover_token_anymarket() -> bool:
    """Remove token do AnyMarket do BANCO DE DADOS"""
    return remover_token('anymarket')


def token_anymarket_configurado() -> bool:
    """Verifica se o token AnyMarket está configurado no banco"""
    data = obter_token('anymarket')
    return data is not None and data.get('token') is not None


def consultar_api_anymarket(product_id: str, token: str = None) -> Dict[str, Any]:
    """Consulta fotos do produto na API AnyMarket"""
    if not token:
        token = obter_token_anymarket_seguro()
    
    api = AnyMarketAPI(token)
    return api.buscar_fotos_produto(product_id)


def consultar_canais_transmissao(partner_id: str = None, token: str = None) -> Dict[str, Any]:
    """
    Consulta canais de transmissão do AnyMarket
    Endpoint: /skus/marketplaces
    """
    if not token:
        token = obter_token_anymarket_seguro()
        print(f"✅ Token obtido com sucesso: {token[:20]}...")
    
    api = AnyMarketAPI(token)
    return api.buscar_canais_transmissao(partner_id)


def excluir_foto_anymarket(product_id: str, photo_id: str, token: str = None) -> Dict[str, Any]:
    """Exclui foto do produto"""
    if not token:
        token = obter_token_anymarket_seguro()
    
    api = AnyMarketAPI(token)
    return api.excluir_foto(product_id, photo_id)


def excluir_fotos_planilha_anymarket(caminho_planilha: str, token: str = None) -> Dict[str, Any]:
    """Exclui fotos em lote"""
    if not token:
        token = obter_token_anymarket_seguro()
    
    api = AnyMarketAPI(token)
    return api.excluir_fotos_planilha(caminho_planilha)


def buscar_produto_por_sku(sku: str, token: str = None) -> Dict[str, Any]:
    """Busca produto por SKU"""
    try:
        if not token:
            token = obter_token_anymarket_seguro()
        
        headers = {
            "Content-Type": "application/json",
            "gumgaToken": token
        }
        
        url = "https://api.anymarket.com.br/v2/products"
        params = {'sku': sku}
        
        print(f"🔍 Buscando produto com SKU: {sku}")
        print(f"🌐 URL: {url}?sku={sku}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"📡 Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            produtos = dados.get('content', [])
            
            print(f"📦 Produtos encontrados: {len(produtos)}")
            
            if produtos:
                produto = produtos[0]
                print(f"✅ PRODUTO ENCONTRADO: {produto.get('title', 'Sem título')}")
                
                for sku_info in produto.get('skus', []):
                    if sku_info.get('partnerId') == sku:
                        print(f"🎯 SKU ESPECÍFICO ENCONTRADO: {sku}")
                        return {
                            'sucesso': True,
                            'produto': produto,
                            'sku_encontrado': sku_info,
                            'tipo_busca': 'sku_direto'
                        }
                
                if produto.get('skus'):
                    print(f"⚠️ SKU não encontrado, mas produto sim. Usando primeiro SKU: {produto['skus'][0].get('partnerId')}")
                    return {
                        'sucesso': True,
                        'produto': produto,
                        'sku_encontrado': produto['skus'][0],
                        'tipo_busca': 'sku_direto_produto_encontrado'
                    }
            
            return {
                'sucesso': False,
                'erro': f'Nenhum produto encontrado com SKU "{sku}"',
                'status_code': 200,
                'produtos_encontrados': len(produtos)
            }
            
        else:
            erro_msg = f'Erro HTTP {response.status_code}'
            print(f"❌ {erro_msg}")
            return {
                'sucesso': False,
                'erro': erro_msg,
                'status_code': response.status_code,
                'detalhes': response.text[:500] if response.text else 'Sem detalhes'
            }
            
    except Exception as e:
        print(f"💥 Erro: {str(e)}")
        return {
            'sucesso': False,
            'erro': f'Erro ao buscar produto: {str(e)}'
        }


def testar_nova_api(product_id="347730803"):
    """Testa a conexão com a nova API"""
    try:
        token = obter_token_anymarket_seguro()
        print(f"🔑 Token obtido: {token[:20]}...")
        
        api = AnyMarketAPI(token)
        
        resultado = api.buscar_fotos_produto(product_id)
        print("=== TESTE NOVA API ===")
        print(f"Sucesso: {resultado['sucesso']}")
        print(f"Status: {resultado['status_code']}")
        print(f"Fotos encontradas: {resultado.get('quantidade_fotos', 0)}")
        
        if resultado['sucesso'] and resultado.get('dados'):
            for i, foto in enumerate(resultado['dados'][:3]):
                print(f"Foto {i+1}: ID={foto['id']}, Principal={foto['main']}, URL={foto['url'][:50]}...")
        elif resultado.get('erro'):
            print(f"❌ Erro: {resultado['erro']}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return None


# Teste rápido se executado diretamente
if __name__ == "__main__":
    print("🧪 Testando conexão com API AnyMarket...")
    testar_nova_api()