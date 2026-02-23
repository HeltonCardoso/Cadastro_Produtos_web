"""
Cliente para API Intelipost - VERSÃO CORRIGIDA
"""
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelipostAPI:
    """Cliente para API da Intelipost"""
    
    def __init__(self, api_key=None):
        """Inicializa o cliente da API"""
        print(f"\n🎯 INICIANDO INTELIPOST API")
        
        if not api_key:
            raise ValueError("API key é obrigatória")
        
        self.api_key = api_key
        self.base_url = "https://api.intelipost.com.br/api/v1"
        self.timeout = 30  # segundos
        
        # Headers para todas as requisições
        self.headers = {
            "Accept": "application/json",
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        print(f"✅ IntelipostAPI inicializado com chave de {len(api_key)} caracteres")
        print(f"🔗 URL base: {self.base_url}")
        print(f"⏱️ Timeout: {self.timeout}s")
    
    def buscar_rastreio(self, numero_pedido):
        """Busca rastreio por número do pedido"""
        try:
            print(f"\n📦 BUSCANDO PEDIDO: {numero_pedido}")
            
            url = f"{self.base_url}/shipment_order/order_number/{numero_pedido}"
            
            print(f"📡 URL: {url}")
            print(f"🔑 Headers: {self.headers}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Pedido encontrado - Status: {data.get('status', 'N/A')}")
                return data
            else:
                print(f"❌ Pedido não encontrado - Status: {response.status_code}")
                print(f"📝 Resposta: {response.text[:200]}")
                return {
                    'status': 'ERROR',
                    'messages': [f'Pedido não encontrado (status {response.status_code})'],
                    'content': []
                }
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout na consulta")
            return {
                'status': 'ERROR',
                'messages': ['Timeout na conexão'],
                'content': []
            }
        except requests.exceptions.ConnectionError:
            print(f"🔌 Erro de conexão")
            return {
                'status': 'ERROR',
                'messages': ['Erro de conexão'],
                'content': []
            }
        except Exception as e:
            print(f"💥 Erro inesperado: {str(e)}")
            return {
                'status': 'ERROR',
                'messages': [f'Erro: {str(e)}'],
                'content': []
            }
        
    def buscar_rastreio_por_nf(self, numero_nf):
        """Busca rastreio por número da Nota Fiscal"""
        try:
            print(f"\n📦 BUSCANDO POR NF: {numero_nf}")
            
            url = f"{self.base_url}/shipment_order/invoice/{numero_nf}"
            
            print(f"📡 URL: {url}")
            print(f"🔑 Headers: {self.headers}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resposta recebida - Status: {data.get('status', 'N/A')}")
                print(f"🔍 Tem 'content'?: {'content' in data}")
                if 'content' in data:
                    print(f"📦 Quantidade de pedidos: {len(data.get('content', []))}")
                return data
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                print(f"📝 Resposta: {response.text[:500]}")
                
                return {
                    'status': 'ERROR',
                    'messages': [f'Erro HTTP {response.status_code}'],
                    'content': []
                }
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout na consulta por NF")
            return {
                'status': 'ERROR',
                'messages': ['Timeout na conexão com a API'],
                'content': []
            }
        except requests.exceptions.ConnectionError:
            print(f"🔌 Erro de conexão por NF")
            return {
                'status': 'ERROR',
                'messages': ['Erro de conexão com a API'],
                'content': []
            }
        except Exception as e:
            print(f"💥 Erro inesperado por NF: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'ERROR',
                'messages': [f'Erro: {str(e)}'],
                'content': []
            }
    
    def testar_conexao(self):
        """Testa a conexão com a API"""
        try:
            print(f"\n🧪 TESTANDO CONEXÃO...")
            
            # Endpoint simples para testar conexão
            url = f"{self.base_url}/shipment_order/order_number/123456789"
            
            print(f"📡 URL teste: {url}")
            print(f"🔑 Headers: {self.headers}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 401:
                return {
                    'sucesso': False,
                    'conectado': False,
                    'mensagem': 'Token inválido ou expirado'
                }
            elif response.status_code == 200:
                return {
                    'sucesso': True,
                    'conectado': True,
                    'mensagem': 'Conexão estabelecida com sucesso'
                }
            else:
                return {
                    'sucesso': True,  # A conexão funcionou, mesmo que o pedido não exista
                    'conectado': True,
                    'mensagem': f'API respondendo (status {response.status_code})'
                }
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout na conexão")
            return {
                'sucesso': False,
                'conectado': False,
                'mensagem': 'Timeout na conexão com a API'
            }
        except requests.exceptions.ConnectionError:
            print(f"🔌 Erro de conexão")
            return {
                'sucesso': False,
                'conectado': False,
                'mensagem': 'Erro de conexão com a API'
            }
        except Exception as e:
            print(f"💥 Erro inesperado: {str(e)}")
            return {
                'sucesso': False,
                'conectado': False,
                'mensagem': f'Erro: {str(e)}'
            }
    
    def limpar_cache(self):
        """Limpa o cache da API"""
        self._cache.clear()
        logger.info("🗑️ Cache limpo")