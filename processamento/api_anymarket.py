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
        ENDPOINT ORIGINAL QUE FUNCIONAVA: GET /products/{id}/photos
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

    # MANTER AS FUNÇÕES QUE JÁ FUNCIONAVAM
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

    # NOVAS FUNCIONALIDADES - TESTAR COM ENDPOINTS ORIGINAIS
    def atualizar_foto(self, product_id: str, photo_id: str, index: int, main: bool) -> Dict[str, Any]:
        """
        Tenta atualizar índice e status principal de uma foto
        USANDO ENDPOINTS ORIGINAIS QUE FUNCIONAM
        """
        try:
            # Tentar usar PUT no endpoint original
            url = f"{self.base_url}/products/{product_id}/photos/{photo_id}"
            
            logger.info(f"Tentando atualizar foto - Produto: {product_id}, Foto: {photo_id}, Index: {index}, Principal: {main}")
            
            # Dados para atualização
            dados_atualizacao = {
                "index": index,
                "main": main
            }
            
            response = requests.put(url, headers=self.headers, json=dados_atualizacao, timeout=30)
            
            resultado = {
                "sucesso": response.status_code in [200, 204],
                "status_code": response.status_code,
                "product_id": product_id,
                "photo_id": photo_id,
                "index": index,
                "main": main,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url
            }
            
            if response.status_code in [200, 204]:
                logger.info(f"Foto atualizada com sucesso - Produto: {product_id}, Foto: {photo_id}")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["detalhes_erro"] = response.text[:500]
                logger.error(f"Erro ao atualizar foto: {response.status_code}")
                
                # Se PUT não funcionar, tentar PATCH
                if response.status_code in [405, 404]:
                    return self._atualizar_com_patch(product_id, photo_id, index, main)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao atualizar foto: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro ao atualizar foto: {str(e)}",
                "product_id": product_id,
                "photo_id": photo_id,
                "timestamp": datetime.now().isoformat()
            }

    def _atualizar_com_patch(self, product_id: str, photo_id: str, index: int, main: bool) -> Dict[str, Any]:
        """
        Tentar atualizar com PATCH se PUT não funcionar
        """
        try:
            url = f"{self.base_url}/products/{product_id}/photos/{photo_id}"
            
            dados_atualizacao = {
                "index": index,
                "main": main
            }
            
            response = requests.patch(url, headers=self.headers, json=dados_atualizacao, timeout=30)
            
            resultado = {
                "sucesso": response.status_code in [200, 204],
                "status_code": response.status_code,
                "product_id": product_id,
                "photo_id": photo_id,
                "index": index,
                "main": main,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url,
                "metodo": "PATCH"
            }
            
            if response.status_code in [200, 204]:
                logger.info(f"Foto atualizada com PATCH - Produto: {product_id}, Foto: {photo_id}")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code} com PATCH"
                resultado["detalhes_erro"] = response.text[:500]
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no PATCH: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro no PATCH: {str(e)}",
                "product_id": product_id,
                "photo_id": photo_id,
                "timestamp": datetime.now().isoformat()
            }

    def definir_foto_principal(self, product_id: str, photo_id: str) -> Dict[str, Any]:
        """
        Define uma foto como principal
        """
        try:
            # Buscar índice atual da foto
            fotos = self.buscar_fotos_produto(product_id)
            if not fotos["sucesso"]:
                return fotos
            
            foto_alvo = next((f for f in fotos["dados"] if f["id"] == photo_id), None)
            if not foto_alvo:
                return {
                    "sucesso": False,
                    "erro": f"Foto {photo_id} não encontrada",
                    "product_id": product_id,
                    "photo_id": photo_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            index_atual = foto_alvo["index"]
            
            return self.atualizar_foto(
                product_id=product_id,
                photo_id=photo_id,
                index=index_atual,
                main=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao definir foto principal: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro ao definir foto principal: {str(e)}",
                "product_id": product_id,
                "photo_id": photo_id,
                "timestamp": datetime.now().isoformat()
            }

    def reordenar_fotos(self, product_id: str, nova_ordem: List[Dict]) -> Dict[str, Any]:
        """
        Reordena as fotos
        """
        try:
            resultados = []
            total_sucesso = 0
            total_erro = 0
            
            for novo_index, foto_info in enumerate(nova_ordem, start=1):
                # Buscar status principal atual
                fotos = self.buscar_fotos_produto(product_id)
                if not fotos["sucesso"]:
                    continue
                
                foto_atual = next((f for f in fotos["dados"] if f["id"] == foto_info["id"]), None)
                main_atual = foto_atual["main"] if foto_atual else False
                
                resultado = self.atualizar_foto(
                    product_id=product_id,
                    photo_id=foto_info["id"],
                    index=novo_index,
                    main=main_atual
                )
                
                resultados.append(resultado)
                
                if resultado["sucesso"]:
                    total_sucesso += 1
                else:
                    total_erro += 1
            
            return {
                "sucesso": total_erro == 0,
                "status_code": 200 if total_erro == 0 else 207,
                "product_id": product_id,
                "total_processado": len(nova_ordem),
                "total_sucesso": total_sucesso,
                "total_erro": total_erro,
                "resultados": resultados,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao reordenar fotos: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro ao reordenar fotos: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.now().isoformat()
            }

    # MANTER AS FUNÇÕES AUXILIARES ORIGINAIS
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
    
    def _extrair_url_imagem_com_debug(self, foto: dict) -> str:
        """Extrai URL da imagem com debug detalhado"""
        campos_prioritarios = ["original", "standard", "high", "medium", "small", "thumbnail", "url"]
        
        print(f"  Buscando URL em campos: {campos_prioritarios}")
        
        for campo in campos_prioritarios:
            if campo in foto and foto[campo]:
                url = foto[campo]
                print(f"  Tentando campo '{campo}': {url}")
                if self._eh_url_valida(url):
                    print(f"  ✅ URL válida no campo '{campo}'")
                    return url
                else:
                    print(f"  ❌ URL inválida no campo '{campo}'")
        
        # Buscar em todos os campos string
        for campo, valor in foto.items():
            if isinstance(valor, str) and 'http' in valor.lower():
                print(f"  Tentando campo genérico '{campo}': {valor}")
                if self._eh_url_valida(valor):
                    print(f"  ✅ URL válida no campo genérico '{campo}'")
                    return valor
        
        return ""
    
    def _eh_url_valida(self, url: str) -> bool:
        """Verifica se é uma URL válida de imagem"""
        if not isinstance(url, str):
            return False
        
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        return any(ext in url.lower() for ext in extensoes_imagem)
    
    
def testar_endpoints_anymarket(product_id: str, photo_id: str, token: str = None) -> Dict[str, Any]:
    """
    Testa quais endpoints e métodos são suportados pela API
    """
    default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
    api = AnyMarketAPI(token or default_token)
    
    resultados = {}
    
    # Testar diferentes endpoints e métodos
    endpoints = [
        f"/products/{product_id}/photos/{photo_id}",  # Endpoint original
        f"/products/{product_id}/images/{photo_id}",  # Endpoint alternativo
        f"/produtos/{product_id}/imagens/{photo_id}", # Endpoint em português
    ]
    
    for endpoint in endpoints:
        resultados[endpoint] = {}
        url = f"{api.base_url}{endpoint}"
        
        # Testar diferentes métodos
        for method in ['GET', 'PUT', 'PATCH', 'POST']:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=api.headers,
                    timeout=10,
                    json={"index": 1, "main": True} if method in ['PUT', 'PATCH', 'POST'] else None
                )
                resultados[endpoint][method] = {
                    "status_code": response.status_code,
                    "suportado": response.status_code not in [404, 405, 401]
                }
            except Exception as e:
                resultados[endpoint][method] = {
                    "status_code": "ERROR",
                    "suportado": False,
                    "erro": str(e)
                }
    
    return {
        "sucesso": True,
        "product_id": product_id,
        "photo_id": photo_id,
        "resultados": resultados,
        "timestamp": datetime.now().isoformat()
    }
# FUNÇÕES DE INTERFACE ORIGINAIS
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

# NOVAS FUNÇÕES
def definir_foto_principal_anymarket(product_id: str, photo_id: str, token: str = None) -> Dict[str, Any]:
    default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
    api = AnyMarketAPI(token or default_token)
    return api.definir_foto_principal(product_id, photo_id)

def reordenar_fotos_anymarket(product_id: str, nova_ordem: List[Dict], token: str = None) -> Dict[str, Any]:
    default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
    api = AnyMarketAPI(token or default_token)
    return api.reordenar_fotos(product_id, nova_ordem)

def atualizar_foto_anymarket(product_id: str, photo_id: str, index: int, main: bool, token: str = None) -> Dict[str, Any]:
    default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
    api = AnyMarketAPI(token or default_token)
    return api.atualizar_foto(product_id, photo_id, index, main)