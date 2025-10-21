import os
import requests
import json
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnyMarketAPI:
    """Classe para interagir com a API do AnyMarket - VERSÃO CORRIGIDA"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.anymarket.com.br/v2"  # URL CORRETA
        self.headers = {
            "Content-Type": "application/json",
            "gumgaToken": token  # ✅ APENAS gumgaToken NO HEADER
        }
    
    def buscar_fotos_produto(self, product_id: str) -> Dict[str, Any]:
        """Busca fotos de um produto específico - VERSÃO CORRIGIDA"""
        try:
            # URL CORRETA com endpoint correto
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
        """Processa os dados das fotos da NOVA API - VERSÃO CORRIGIDA"""
        fotos_processadas = []
        
        for i, foto in enumerate(dados):
            print(f"=== DEBUG FOTO {i} ===")
            print(f"Campos disponíveis: {list(foto.keys())}")
            
            # ✅ CORREÇÃO: Usa a URL correta da nova API
            # Prioridade: url > originalImage > standardUrl > thumbnailUrl
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
                "original": url_imagem,  # Campo compatível com template
                "status": "disponivel" if url_imagem else "indisponivel",
                "debug_campos": list(foto.keys()),
                # Novos campos disponíveis
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

    def _processar_fotos(self, dados: list) -> list:
        """Mantém método antigo para compatibilidade"""
        return self._processar_fotos_v2(dados)

    def excluir_foto(self, product_id: str, photo_id: str) -> Dict[str, Any]:
        """Exclui uma foto específica de um produto - VERSÃO CORRIGIDA"""
        try:
            # URL CORRETA
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
        """Exclui fotos baseado em uma planilha Excel - VERSÃO CORRIGIDA"""
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
# 🔹 Funções globais acessíveis para import no app.py
# ======================================================

def consultar_api_anymarket(product_id: str, token: str = None) -> Dict[str, Any]:
    """Consulta fotos do produto na API AnyMarket - VERSÃO CORRIGIDA"""
    if not token:
        try:
            token = obter_token_anymarket_seguro()
        except:
            raise ValueError("Token do AnyMarket não configurado. Configure em /configuracoes/tokens")
    
    api = AnyMarketAPI(token)
    return api.buscar_fotos_produto(product_id)

def excluir_foto_anymarket(product_id: str, photo_id: str, token: str = None) -> Dict[str, Any]:
    """Exclui foto do produto - VERSÃO CORRIGIDA"""
    if not token:
        token = obter_token_anymarket_seguro()
    
    api = AnyMarketAPI(token)
    return api.excluir_foto(product_id, photo_id)

def excluir_fotos_planilha_anymarket(caminho_planilha: str, token: str = None) -> Dict[str, Any]:
    """Exclui fotos em lote - VERSÃO CORRIGIDA"""
    if not token:
        token = obter_token_anymarket_seguro()
    
    api = AnyMarketAPI(token)
    return api.excluir_fotos_planilha(caminho_planilha)

def obter_token_anymarket_seguro() -> str:
    """
    Obtém token do AnyMarket de forma segura do arquivo tokens_secure.json
    Levanta exceção se não encontrar
    """
    try:
        tokens_file = 'tokens_secure.json'
        if not os.path.exists(tokens_file):
            raise ValueError("Arquivo de tokens não encontrado. Configure o token primeiro.")
        
        with open(tokens_file, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
        
        # Primeiro tenta a estrutura nova: {"anymarket": {"token": ...}}
        token_data = tokens.get('anymarket')
        if token_data and token_data.get('token'):
            return token_data['token']
        
        # Se não encontrar, procura em estrutura antiga com IDs aleatórios
        for key, value in tokens.items():
            if isinstance(value, dict) and value.get('tipo') == 'anymarket' and value.get('token'):
                print(f"✅ Token encontrado na estrutura antiga (ID: {key})")
                return value['token']
        
        raise ValueError("Token do AnyMarket não configurado no arquivo seguro.")
        
    except json.JSONDecodeError:
        raise ValueError("Arquivo de tokens corrompido.")
    except Exception as e:
        raise ValueError(f"Erro ao obter token: {str(e)}")

# Função de teste para verificar a nova API
def testar_nova_api(product_id="347730803"):
    """Testa a conexão com a nova API"""
    try:
        token = obter_token_anymarket_seguro()
        print(f"🔑 Token obtido: {token[:20]}...")
        
        api = AnyMarketAPI(token)
        
        # Testa com um produto conhecido
        resultado = api.buscar_fotos_produto(product_id)
        print("=== TESTE NOVA API ===")
        print(f"Sucesso: {resultado['sucesso']}")
        print(f"Status: {resultado['status_code']}")
        print(f"Fotos encontradas: {resultado.get('quantidade_fotos', 0)}")
        
        if resultado['sucesso'] and resultado.get('dados'):
            for i, foto in enumerate(resultado['dados'][:3]):  # Mostra apenas 3 primeiras
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