"""
Cliente para API Intelipost
"""
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import time
import json

logger = logging.getLogger(__name__)

class IntelipostAPI:
    """Cliente para a API Intelipost"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicializa o cliente Intelipost
        
        Args:
            api_key: Chave de API Intelipost
            base_url: URL base da API
        """
        from config import Config
        
        self.api_key = (api_key or Config.INTELIPOST_API_KEY).strip()
        self.base_url = base_url or Config.INTELIPOST_BASE_URL
        
        logger.info(f"IntelipostAPI inicializado")
        
        # Cache para resultados
        self._cache = {}
        self.cache_timeout = getattr(Config, 'INTELIPOST_CACHE_TIMEOUT', 300)
    
    def _get_headers(self):
        """Retorna headers corretos para a API Intelipost"""
        return {
            'Accept': 'application/json',
            'api-key': self.api_key
        }
    
    def buscar_rastreio(self, numero_pedido: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Busca informações de rastreamento pelo número do pedido
        
        Args:
            numero_pedido: Número do pedido na Intelipost
            use_cache: Se deve usar cache
            
        Returns:
            Dict com os dados de rastreamento
            
        Raises:
            Exception: Em caso de erro na requisição
        """
        cache_key = f"rastreio_{numero_pedido}"
        
        # Verifica cache
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_timeout:
                logger.info(f"Usando cache para pedido {numero_pedido}")
                return cached_data
        
        url = f"{self.base_url}/shipment_order/{numero_pedido}"
        headers = self._get_headers()
        
        logger.info(f"Buscando rastreio para: {numero_pedido}")
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=30)
            elapsed_time = time.time() - start_time
            
            logger.info(f"Resposta em {elapsed_time:.2f}s: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK':
                    logger.info(f"✅ Pedido {numero_pedido} encontrado!")
                    
                    # Armazena no cache
                    if use_cache:
                        self._cache[cache_key] = (data, datetime.now())
                    
                    return data
                else:
                    error_msg = data.get('messages', [{}])[0].get('text', 'Erro desconhecido')
                    raise Exception(f"Intelipost: {error_msg}")
                    
            elif response.status_code == 400:
                # Analisa erro 400
                try:
                    error_data = response.json()
                    error_msg = error_data.get('messages', [{}])[0].get('text', 'Erro desconhecido')
                except:
                    error_msg = response.text[:200]
                
                if "Número do pedido desconhecido" in error_msg or "unknown.order.number" in error_msg:
                    raise Exception(f"Pedido não encontrado: {numero_pedido}")
                else:
                    raise Exception(f"Erro na requisição: {error_msg}")
                    
            elif response.status_code == 401:
                raise Exception("API Key inválida ou expirada")
                
            elif response.status_code == 403:
                raise Exception("Acesso negado à API Intelipost")
                
            elif response.status_code == 404:
                raise Exception(f"Pedido não encontrado: {numero_pedido}")
                
            else:
                raise Exception(f"Erro HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            raise Exception("Timeout na conexão com Intelipost (30s)")
        except requests.exceptions.ConnectionError:
            raise Exception("Erro de conexão com Intelipost")
        except Exception as e:
            logger.error(f"Erro ao buscar rastreio: {str(e)}")
            raise
    
    def testar_conexao(self) -> Dict[str, Any]:
        """Testa a conexão com a API Intelipost"""
        try:
            # Testa com um pedido que não existe
            test_pedido = f"TEST_CONEXAO_{int(time.time())}"
            url = f"{self.base_url}/shipment_order/{test_pedido}"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Análise da resposta
            if response.status_code == 400:
                resposta_texto = response.text.lower()
                if "número do pedido desconhecido" in resposta_texto or "unknown.order.number" in resposta_texto:
                    return {
                        'sucesso': True,
                        'conectado': True,
                        'api_key_valida': True,
                        'status_code': response.status_code,
                        'mensagem': 'API Intelipost conectada com sucesso',
                        'detalhe': 'Erro 400 esperado para pedido de teste inexistente'
                    }
                else:
                    return {
                        'sucesso': False,
                        'conectado': False,
                        'status_code': response.status_code,
                        'mensagem': f'Erro 400: {response.text[:100]}'
                    }
                    
            elif response.status_code == 401:
                return {
                    'sucesso': False,
                    'conectado': False,
                    'api_key_valida': False,
                    'status_code': response.status_code,
                    'mensagem': 'API Key inválida ou expirada'
                }
                
            elif response.status_code == 200:
                return {
                    'sucesso': True,
                    'conectado': True,
                    'api_key_valida': True,
                    'status_code': response.status_code,
                    'mensagem': 'API Intelipost conectada com sucesso'
                }
                
            elif response.status_code == 404:
                return {
                    'sucesso': True,
                    'conectado': True,
                    'api_key_valida': True,
                    'status_code': response.status_code,
                    'mensagem': 'API Intelipost conectada'
                }
                
            else:
                return {
                    'sucesso': False,
                    'conectado': False,
                    'status_code': response.status_code,
                    'mensagem': f'Status inesperado: {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'sucesso': False,
                'conectado': False,
                'mensagem': 'Timeout (10s) na conexão'
            }
        except Exception as e:
            return {
                'sucesso': False,
                'conectado': False,
                'mensagem': f'Erro: {str(e)}'
            }
    
    def limpar_cache(self):
        """Limpa o cache da API"""
        self._cache.clear()
        logger.info("Cache da API Intelipost limpo")