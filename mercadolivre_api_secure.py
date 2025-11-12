import requests
import json
from datetime import datetime
import time
from token_manager_secure import get_valid_ml_token

class MercadoLivreAPISecure:
    def __init__(self):
        self.base_url = "https://api.mercadolibre.com"
    
    def _get_headers(self):
        """Retorna headers com token"""
        token = get_valid_ml_token()
        if not token:
            raise Exception("Token do Mercado Livre não disponível. Faça a autenticação primeiro.")
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def testar_conexao(self):
        """Testa a conexão com a API"""
        try:
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Conexão OK - Usuário: {user_data.get('nickname')}")
                return True
            else:
                print(f"❌ Erro na conexão: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao testar conexão: {str(e)}")
            return False
    
    def buscar_anuncios_mlbs(self, mlbs):
        """Busca informações de múltiplos anúncios por MLB"""
        try:
            headers = self._get_headers()
            resultados = []
            encontrados = 0
            nao_encontrados = 0
            
            # A API do ML permite buscar até 20 itens por vez
            for i in range(0, len(mlbs), 20):
                lote = mlbs[i:i + 20]
                ids_str = ','.join(lote)
                
                print(f"🔍 Buscando lote {i//20 + 1}: {len(lote)} MLBs")
                
                response = requests.get(
                    f"{self.base_url}/items?ids={ids_str}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    dados_lote = response.json()
                    
                    for item_data in dados_lote:
                        mlb_id = item_data.get('id', 'MLB_DESCONHECIDO')
                        
                        if item_data.get('code') == 200 and 'body' in item_data:
                            item = item_data['body']
                            resultado = self._processar_anuncio(item)
                            resultados.append(resultado)
                            encontrados += 1
                            print(f"   ✅ {mlb_id}")
                        else:
                            resultados.append({
                                'id': mlb_id,
                                'error': 'Não encontrado ou erro na API',
                                'status': 'error'
                            })
                            nao_encontrados += 1
                            print(f"   ❌ {mlb_id}")
                
                # Delay para evitar rate limit
                time.sleep(0.5)
            
            return {
                'sucesso': True,
                'total_encontrado': encontrados,
                'total_nao_encontrado': nao_encontrados,
                'resultados': resultados,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro ao buscar MLBs: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _processar_anuncio(self, item):
        """Processa os dados de um anúncio"""
        try:
            # Extrai informações de shipping
            shipping = item.get('shipping', {})
            shipping_mode = shipping.get('mode', 'N/A')
            
            # Extrai manufacturing time dos sale_terms
            manufacturing_time = 'N/A'
            for term in item.get('sale_terms', []):
                if term.get('id') == 'MANUFACTURING_TIME':
                    manufacturing_time = term.get('value_name', 'N/A')
                    break
            
            # Se não encontrou nos sale_terms, tenta no campo direto
            if manufacturing_time == 'N/A':
                manufacturing_time = item.get('manufacturing_time', 'N/A')
            
            return {
                'id': item.get('id', 'N/A'),
                'title': item.get('title', 'N/A'),
                'price': item.get('price', 0),
                'currency_id': item.get('currency_id', 'BRL'),
                'status': item.get('status', 'N/A'),
                'condition': item.get('condition', 'N/A'),
                'available_quantity': item.get('available_quantity', 0),
                'sold_quantity': item.get('sold_quantity', 0),
                'listing_type_id': item.get('listing_type_id', 'N/A'),
                'shipping_mode': shipping_mode,
                'shipping_free_shipping': shipping.get('free_shipping', False),
                'shipping_local_pick_up': shipping.get('local_pick_up', False),
                'manufacturing_time': manufacturing_time,
                'permalink': item.get('permalink', 'N/A'),
                'thumbnail': item.get('thumbnail', 'N/A'),
                'seller_id': item.get('seller_id', 'N/A'),
                'category_id': item.get('category_id', 'N/A'),
                'warranty': item.get('warranty', 'N/A'),
                'date_created': item.get('date_created', 'N/A')
            }
            
        except Exception as e:
            return {
                'id': item.get('id', 'N/A'),
                'error': f'Erro no processamento: {str(e)}',
                'status': 'error'
            }
    
    def buscar_meus_anuncios(self, status='active', limit=50):
        """Busca anúncios do usuário autenticado"""
        try:
            headers = self._get_headers()
            
            # Primeiro obtém o user_id
            response_me = requests.get(
                f"{self.base_url}/users/me",
                headers=headers,
                timeout=10
            )
            
            if response_me.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': 'Erro ao obter dados do usuário'
                }
            
            user_data = response_me.json()
            user_id = user_data['id']
            print(f"👤 Usuário: {user_data.get('nickname')} (ID: {user_id})")
            
            # Busca os anúncios
            url = f"{self.base_url}/users/{user_id}/items/search"
            params = {
                'status': status,
                'limit': limit
            }
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                anuncios_ids = data.get('results', [])
                total = data.get('paging', {}).get('total', 0)
                
                print(f"📦 {total} anúncios encontrados (status: {status})")
                
                # Busca detalhes dos anúncios
                if anuncios_ids:
                    return self.buscar_anuncios_mlbs(anuncios_ids[:limit])  # Limita pelo parâmetro
                else:
                    return {
                        'sucesso': True,
                        'total_encontrado': 0,
                        'resultados': [],
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                return {
                    'sucesso': False,
                    'erro': f'Erro HTTP {response.status_code}'
                }
                
        except Exception as e:
            print(f"❌ Erro ao buscar meus anúncios: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

# Instância global
ml_api_secure = MercadoLivreAPISecure()