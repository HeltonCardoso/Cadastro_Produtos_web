import requests
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnyMarketAPI:
    """Classe para interagir com a API do AnyMarket"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://app.anymarket.com.br/rest/api"
        self.headers = {
            "gumgaToken": token,
            "Content-Type": "application/json;charset=UTF-8"
        }
    
    def buscar_fotos_produto(self, product_id: str) -> Dict[str, Any]:
        """
        Busca fotos de um produto específico
        
        Args:
            product_id (str): ID do produto no AnyMarket
            
        Returns:
            Dict com os dados da resposta
        """
        try:
            url = f"{self.base_url}/products/{product_id}/photos"
            
            logger.info(f"Consultando API AnyMarket - Produto: {product_id}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            resultado = {
                "sucesso": response.status_code == 200,
                "status_code": response.status_code,
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "url_consultada": url
            }
            
            if response.status_code == 200:
                dados = response.json()
                
                # Processar as fotos para extrair URLs de imagem
                fotos_processadas = self._processar_fotos(dados)
                
                resultado["dados"] = fotos_processadas
                resultado["quantidade_fotos"] = len(fotos_processadas)
                
                logger.info(f"Consulta bem-sucedida - {resultado['quantidade_fotos']} fotos encontradas")
            else:
                resultado["erro"] = f"Erro HTTP {response.status_code}"
                resultado["detalhes_erro"] = response.text
                logger.error(f"Erro na consulta: {response.status_code} - {response.text}")
            
            return resultado
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro de conexão: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            return {
                "sucesso": False,
                "erro": f"Erro inesperado: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _processar_fotos(self, dados: list) -> list:
        """Processa os dados das fotos para extrair URLs de imagem"""
        fotos_processadas = []
        
        # CORREÇÃO: Removido o enumerate desnecessário
        for foto in dados:
            foto_processada = {
                "id": foto.get("id"),
                "index": foto.get("index"),
                "main": foto.get("main", False),
                "type": foto.get("type"),
                "url": foto.get("url"),
                "original": self._extrair_url_imagem(foto)
            }
            
            fotos_processadas.append(foto_processada)
        
        return fotos_processadas
    
    def _extrair_url_imagem(self, foto: dict) -> str:
        """Extrai a URL da imagem dos diferentes campos possíveis"""
        # Campos prioritários para buscar imagens
        campos_prioritarios = ["original", "standard", "url", "thumbnail", "high", "medium", "small"]
        
        for campo in campos_prioritarios:
            if campo in foto and foto[campo]:
                url = foto[campo]
                if self._eh_url_valida(url):
                    return url
        
        # Buscar em todos os campos string que parecem URLs
        for campo, valor in foto.items():
            if isinstance(valor, str) and self._eh_url_valida(valor):
                return valor
        
        # Buscar em sub-objetos
        for campo, valor in foto.items():
            if isinstance(valor, dict):
                for sub_campo in campos_prioritarios:
                    if sub_campo in valor and valor[sub_campo]:
                        url = valor[sub_campo]
                        if self._eh_url_valida(url):
                            return url
        
        return ""
    
    def _eh_url_valida(self, url: str) -> bool:
        """Verifica se é uma URL válida de imagem"""
        if not isinstance(url, str):
            return False
        
        # Verificar se começa com http
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # Verificar extensões de imagem comuns
        extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        return any(ext in url.lower() for ext in extensoes_imagem)

def consultar_api_anymarket(product_id: str, token: str = None) -> Dict[str, Any]:
    """
    Função principal para consultar a API do AnyMarket
    
    Args:
        product_id (str): ID do produto
        token (str): Token de autenticação (se None, usa o padrão)
        
    Returns:
        Dict com resultados da consulta
    """
    # Token padrão (o mesmo do seu exemplo)
    default_token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
    
    api = AnyMarketAPI(token or default_token)
    return api.buscar_fotos_produto(product_id)