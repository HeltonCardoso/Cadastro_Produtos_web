"""
Cliente para API Intelipost - VERSÃO CORRIGIDA
"""
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelipostAPI:
    """Cliente para a API Intelipost"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente Intelipost
        
        Args:
            api_key: Chave de API Intelipost (OBRIGATÓRIA)
        """
        if not api_key:
            raise ValueError("❌ API Key Intelipost não fornecida")
        
        self.api_key = api_key.strip()
        self.base_url = "https://api.intelipost.com.br/api/v1"
        
        logger.info(f"✅ IntelipostAPI inicializado com chave de {len(self.api_key)} caracteres")
        logger.info(f"🔗 URL base: {self.base_url}")
        
        # Cache simples
        self._cache = {}
    
    def _get_headers(self):
        """Retorna headers para a API Intelipost"""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
    
    def buscar_rastreio(self, numero_pedido: str) -> Dict[str, Any]:
        """
        Busca informações de rastreamento
        
        Args:
            numero_pedido: Número do pedido na Intelipost
            
        Returns:
            Dict com os dados de rastreamento
        """
        # URL da API Intelipost para shipment_order
        url = f"{self.base_url}/shipment_order/{numero_pedido}"
        headers = self._get_headers()
        
        logger.info(f"📤 GET {url}")
        logger.info(f"🔑 API Key: {self.api_key[:10]}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"📥 Resposta: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Status da API: {data.get('status', 'N/A')}")
                
                if data.get('status') == 'OK':
                    logger.info(f"✅ Pedido {numero_pedido} encontrado!")
                    return data
                else:
                    error_msg = data.get('messages', [{}])[0].get('text', 'Erro desconhecido')
                    raise Exception(f"Intelipost: {error_msg}")
                    
            elif response.status_code == 400:
                # Pedido não encontrado ou erro
                error_text = response.text[:500]
                logger.error(f"❌ Erro 400: {error_text}")
                
                if "Número do pedido desconhecido" in error_text or "unknown.order.number" in error_text:
                    raise Exception(f"Pedido não encontrado: {numero_pedido}")
                elif "Invalid API key" in error_text or "api-key" in error_text.lower():
                    raise Exception(f"API Key inválida")
                else:
                    raise Exception(f"Erro 400: {error_text}")
                    
            elif response.status_code == 401:
                raise Exception("API Key inválida ou expirada")
                
            elif response.status_code == 403:
                raise Exception("Acesso negado à API Intelipost")
                
            elif response.status_code == 404:
                raise Exception(f"Endpoint não encontrado")
                
            else:
                error_text = response.text[:500]
                logger.error(f"❌ Erro HTTP {response.status_code}: {error_text}")
                raise Exception(f"Erro HTTP {response.status_code}: {error_text}")
                
        except requests.exceptions.Timeout:
            logger.error("⏰ Timeout na conexão com Intelipost")
            raise Exception("Timeout na conexão com Intelipost (30s)")
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Erro de conexão com Intelipost")
            raise Exception("Erro de conexão com Intelipost")
        except Exception as e:
            logger.error(f"❌ Erro ao buscar rastreio: {str(e)}")
            raise
    
    def testar_conexao(self) -> Dict[str, Any]:
        """Testa a conexão com a API Intelipost"""
        try:
            logger.info("🧪 Testando conexão com Intelipost...")
            
            # Testa endpoint de shipment_order com pedido que não existe
            test_pedido = "TESTE_CONEXAO_123456"
            url = f"{self.base_url}/shipment_order/{test_pedido}"
            headers = self._get_headers()
            
            logger.info(f"📤 Teste GET {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"📥 Teste resposta: {response.status_code}")
            
            # Análise da resposta
            if response.status_code == 400:
                # 400 é esperado para pedido de teste
                error_text = response.text.lower()
                if "número do pedido desconhecido" in error_text or "unknown.order.number" in error_text:
                    return {
                        'sucesso': True,
                        'conectado': True,
                        'api_key_valida': True,
                        'mensagem': 'API Intelipost conectada com sucesso',
                        'status_code': response.status_code,
                        'detalhe': 'Erro 400 esperado para pedido de teste inexistente'
                    }
                else:
                    return {
                        'sucesso': False,
                        'conectado': False,
                        'api_key_valida': False,
                        'mensagem': f'API Key pode ser inválida',
                        'status_code': response.status_code,
                        'resposta': response.text[:200]
                    }
                    
            elif response.status_code == 401:
                return {
                    'sucesso': False,
                    'conectado': False,
                    'api_key_valida': False,
                    'mensagem': 'API Key inválida ou expirada',
                    'status_code': response.status_code
                }
                
            elif response.status_code == 200:
                return {
                    'sucesso': True,
                    'conectado': True,
                    'api_key_valida': True,
                    'mensagem': 'API Intelipost conectada com sucesso',
                    'status_code': response.status_code
                }
                
            else:
                return {
                    'sucesso': response.status_code < 500,
                    'conectado': response.status_code < 500,
                    'api_key_valida': response.status_code != 401,
                    'mensagem': f'Status inesperado: {response.status_code}',
                    'status_code': response.status_code,
                    'resposta': response.text[:200]
                }
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão: {str(e)}")
            return {
                'sucesso': False,
                'conectado': False,
                'mensagem': f'Erro: {str(e)}'
            }
    
    def limpar_cache(self):
        """Limpa o cache da API"""
        self._cache.clear()
        logger.info("🗑️ Cache limpo")