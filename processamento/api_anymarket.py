import requests
import json
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnyMarketAPI:
    """Classe para interagir com a API do AnyMarket"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://app.anymarket.com.br/rest/api"  # VOLTAR PARA URL ORIGINAL
        self.headers = {
            "gumgaToken": token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8"
        }
    
    def buscar_fotos_produto(self, product_id: str) -> Dict[str, Any]:
        """
        Busca fotos de um produto específico
        """
        try:
            url = f"{self.base_url}/products/{product_id}/photos"  # VOLTAR ENDPOINT ORIGINAL
            
            logger.info(f"Consultando API AnyMarket - Produto: {product_id}")
            
            response = requests.get(url, headers=self.headers, timeout=60)
            
            resultado = {
                "sucesso": response.status_code == 200,
                "status_code": response.status_code,
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url
            }
            
            if response.status_code == 200:
                dados = response.json()
                fotos_processadas = self._processar_fotos(dados)
                
                resultado["dados"] = fotos_processadas
                resultado["quantidade_fotos"] = len(fotos_processadas)
                
                logger.info(f"Consulta bem-sucedida - {resultado['quantidade_fotos']} fotos encontradas")
            
            elif response.status_code == 502:
                resultado["erro"] = "Servidor AnyMarket indisponível (Erro 502). Tente novamente em alguns minutos."
                logger.error(f"Erro 502 no AnyMarket - Servidor indisponível")
            
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["detalhes_erro"] = response.text[:500]
                logger.error(f"Erro na consulta: {response.status_code}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro inesperado: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def excluir_foto(self, product_id: str, photo_id: str) -> Dict[str, Any]:
        """
        Exclui uma foto específica de um produto
        ENDPOINT ORIGINAL: DELETE /products/{id}/photos/{photoId}
        """
        try:
            url = f"{self.base_url}/products/{product_id}/photos/{photo_id}"  # VOLTAR ENDPOINT ORIGINAL
            
            logger.info(f"Excluindo foto - Produto: {product_id}, Foto: {photo_id}")
            
            response = requests.delete(url, headers=self.headers, timeout=30)
            
            resultado = {
                "sucesso": response.status_code in [200, 204],
                "status_code": response.status_code,
                "product_id": product_id,
                "photo_id": photo_id,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url
            }
            
            if response.status_code in [200, 204]:
                logger.info(f"Foto excluída com sucesso - Produto: {product_id}, Foto: {photo_id}")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["detalhes_erro"] = response.text[:500]
                logger.error(f"Erro ao excluir foto: {response.status_code}")
            
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

    def _processar_fotos(self, dados: list) -> list:
        """Processa os dados das fotos com debug detalhado"""
        fotos_processadas = []
        
        for i, foto in enumerate(dados):
            print(f"=== DEBUG FOTO {i} ===")
            print(f"Campos disponíveis: {list(foto.keys())}")
            
            # Extrair URL com debug
            url_original = self._extrair_url_imagem_com_debug(foto)
            
            foto_processada = {
                "id": str(foto.get("id", "")),
                "index": foto.get("index", 0),
                "main": foto.get("main", False),
                "type": foto.get("type", ""),
                "url": foto.get("url", ""),
                "original": url_original,
                "status": "disponivel" if url_original else "indisponivel",
                "debug_campos": list(foto.keys())  # Para debug no template
            }
            
            # Log de debug
            if not url_original:
                print(f"❌ Nenhuma URL válida encontrada para foto {foto.get('id')}")
                print(f"   Campos com 'http': {[k for k, v in foto.items() if isinstance(v, str) and 'http' in v]}")
            else:
                print(f"✅ URL encontrada: {url_original}")
            
            fotos_processadas.append(foto_processada)
            print("=====================")
        
        return fotos_processadas
      
    def consultar_api_anymarket(product_id: str, token: str = None) -> Dict[str, Any]:
        default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
        api = AnyMarketAPI(token or default_token)
        return api.buscar_fotos_produto(product_id)

    def excluir_foto_anymarket(product_id: str, photo_id: str, token: str = None) -> Dict[str, Any]:
        default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
        api = AnyMarketAPI(token or default_token)
        return api.excluir_foto(product_id, photo_id)

    def excluir_fotos_planilha_anymarket(caminho_planilha: str, token: str = None) -> Dict[str, Any]:
        default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
        api = AnyMarketAPI(token or default_token)
        return api.excluir_fotos_planilha(caminho_planilha)
