import requests
import json
from datetime import datetime
import time
from token_manager_secure import ml_token_manager

class MercadoLivreAPISecure:
    def __init__(self):
        self.base_url = "https://api.mercadolibre.com"
    
    def _get_headers(self):
        """Retorna headers com token"""
        token = ml_token_manager.get_valid_token()
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
    
    def atualizar_manufacturing_time(self, mlb_id, manufacturing_time_days):
        """Atualiza o manufacturing time de um anúncio"""
        try:
            headers = self._get_headers()
            
            # Prepara os dados de atualização
            update_data = {
                "sale_terms": [
                    {
                        "id": "MANUFACTURING_TIME",
                        "value_name": f"{manufacturing_time_days} dias"
                    }
                ]
            }
            
            print(f"🔄 Atualizando MLB {mlb_id} - Manufacturing Time: {manufacturing_time_days} dias")
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Manufacturing Time atualizado com sucesso para {manufacturing_time_days} dias")
                return {
                    'sucesso': True,
                    'mensagem': f'Manufacturing Time atualizado para {manufacturing_time_days} dias'
                }
            else:
                error_msg = f"Erro HTTP {response.status_code}"
                print(f"❌ {error_msg}")
                return {
                    'sucesso': False,
                    'erro': error_msg
                }
                
        except Exception as e:
            print(f"❌ Erro ao atualizar manufacturing time: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def atualizar_multiplos_manufacturing(self, atualizacoes):
        """Atualiza manufacturing time para múltiplos anúncios"""
        try:
            resultados = []
            
            for atualizacao in atualizacoes:
                mlb_id = atualizacao.get('mlb')
                dias = atualizacao.get('dias')
                
                if not mlb_id or not dias:
                    resultados.append({
                        'mlb': mlb_id,
                        'sucesso': False,
                        'erro': 'MLB ou dias não fornecidos'
                    })
                    continue
                
                # Atualiza individualmente
                resultado = self.atualizar_manufacturing_time(mlb_id, dias)
                resultado['mlb'] = mlb_id
                resultados.append(resultado)
                
                # Delay para evitar rate limit
                time.sleep(0.5)
            
            return {
                'sucesso': True,
                'resultados': resultados,
                'total_atualizado': len([r for r in resultados if r.get('sucesso')]),
                'total_erros': len([r for r in resultados if not r.get('sucesso')])
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def buscar_anuncios_mlbs(self, mlbs):
        """Busca informações de múltiplos anúncios por MLB"""
        try:
            headers = self._get_headers()
            resultados = []
            encontrados = 0
            nao_encontrados = 0
            
            # DEBUG: Mostrar JSON completo do primeiro MLB
            if mlbs:
                self.debug_json_completo(mlbs[0])
            
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
        """Processa os dados de um anúncio incluindo tipo, catálogo e variações"""
        try:
            # Extrai informações de shipping
            shipping = item.get('shipping', {})
            shipping_mode = shipping.get('mode', 'N/A')
            
            # Frete grátis - campo confirmado no JSON
            frete_gratis = shipping.get('free_shipping', False)
            frete_gratis_texto = 'Sim' if frete_gratis else 'Não'
            
            # Manufacturing time - procura nos sale_terms
            manufacturing_time = 'N/A'
            for term in item.get('sale_terms', []):
                if term.get('id') == 'MANUFACTURING_TIME':
                    manufacturing_time = term.get('value_name', 'N/A')
                    break
            
            # Se não encontrou, tenta campo direto
            if manufacturing_time == 'N/A':
                manufacturing_time = item.get('manufacturing_time', 'N/A')
            
            # SKU do vendedor - campo confirmado no JSON
            meu_sku = item.get('seller_custom_field', 'N/A')
            
            # =========================================
            # NOVOS CAMPOS: CATÁLOGO, VARIAÇÕES E TIPO
            # =========================================
            
            # 1. Verifica se é produto do catálogo
            catalog_product_id = item.get('catalog_product_id')
            eh_catalogo = 'Sim' if catalog_product_id else 'Não'
            
            # 2. Verifica se tem variações
            variations = item.get('variations', [])
            tem_variacoes = 'Sim' if variations and len(variations) > 0 else 'Não'
            quantidade_variacoes = len(variations)
            
            # 3. Identifica o tipo de anúncio (listing_type_id)
            listing_type_id = item.get('listing_type_id', 'N/A')
            tipo_anuncio = self._mapear_tipo_anuncio(listing_type_id)
            
            # 4. Verifica se é Premium/Gold/Classic
            tipo_premium = self._identificar_tipo_premium(listing_type_id, item.get('tags', []))
            
            # 5. Processa dados das variações
            variacoes_detalhes = []
            if variations:
                for variacao in variations:
                    # Extrai os atributos da variação
                    atributos = []
                    for attr in variacao.get('attribute_combinations', []):
                        atributos.append({
                            'name': attr.get('name', ''),
                            'value_name': attr.get('value_name', '')
                        })
                    
                    # Manufacturing time da variação
                    manufacturing_time_variacao = 'N/A'
                    for term in variacao.get('sale_terms', []):
                        if term.get('id') == 'MANUFACTURING_TIME':
                            manufacturing_time_variacao = term.get('value_name', 'N/A')
                            break
                    
                    variacao_info = {
                        'id': variacao.get('id', 'N/A'),
                        'attribute_combinations': atributos,
                        'price': variacao.get('price', 0),
                        'available_quantity': variacao.get('available_quantity', 0),
                        'sold_quantity': variacao.get('sold_quantity', 0),
                        'picture_ids': variacao.get('picture_ids', []),
                        'manufacturing_time': manufacturing_time_variacao,  # NOVO CAMPO
                        'seller_custom_field': variacao.get('seller_custom_field', 'N/A')  # SKU da variação
                    }
                    variacoes_detalhes.append(variacao_info)

            return {
                # ORDEM SOLICITADA ORIGINAL
                'meu_sku': meu_sku,
                'id': item.get('id', 'N/A'),
                'title': item.get('title', 'N/A'),
                'price': item.get('price', 0),
                'available_quantity': item.get('available_quantity', 0),
                'shipping_mode': shipping_mode,
                'manufacturing_time': manufacturing_time,
                'status': item.get('status', 'N/A'),
                'frete_gratis': frete_gratis_texto,
                
                # NOVOS CAMPOS ADICIONAIS
                'eh_catalogo': eh_catalogo,
                'tem_variacoes': tem_variacoes,
                'quantidade_variacoes': quantidade_variacoes,
                'variacoes_detalhes': variacoes_detalhes,  # AGORA COM PRAZOS
                'tipo_anuncio': tipo_anuncio,
                'tipo_premium': tipo_premium,
                'listing_type_id': listing_type_id,
                'catalog_product_id': catalog_product_id,
                
                # Campos adicionais para compatibilidade
                'currency_id': item.get('currency_id', 'BRL'),
                'condition': item.get('condition', 'N/A'),
                'sold_quantity': item.get('sold_quantity', 0),
                'shipping_free_shipping': shipping.get('free_shipping', False),
                'shipping_local_pick_up': shipping.get('local_pick_up', False),
                'permalink': item.get('permalink', 'N/A'),
                'thumbnail': item.get('thumbnail', 'N/A'),
                'seller_id': item.get('seller_id', 'N/A'),
                'category_id': item.get('category_id', 'N/A'),
                'warranty': item.get('warranty', 'N/A'),
                'date_created': item.get('date_created', 'N/A')
            }
            
        except Exception as e:
            print(f"❌ Erro no processamento do item {item.get('id', 'N/A')}: {str(e)}")
            return {
                'id': item.get('id', 'N/A'),
                'error': f'Erro no processamento: {str(e)}',
                'status': 'error'
            }

    def _mapear_tipo_anuncio(self, listing_type_id):
        """Mapeia o listing_type_id para um nome mais amigável"""
        mapeamento = {
            'gold_special': 'Gold Special',
            'gold_pro': 'Gold Pro', 
            'gold_premium': 'Gold Premium',
            'gold': 'Gold',
            'silver': 'Silver',
            'bronze': 'Bronze',
            'free': 'Gratuito',
            'classic': 'Clássico',
            'premium': 'Premium',
            'blue': 'Blue',
            'orange': 'Orange'
        }
        return mapeamento.get(listing_type_id, listing_type_id)

    def _identificar_tipo_premium(self, listing_type_id, tags):
        """Identifica se é Premium, Gold ou Classic baseado no listing_type_id e tags"""
        listing_lower = listing_type_id.lower()
        
        # Verifica pelo listing_type_id primeiro
        if 'premium' in listing_lower:
            return 'Premium'
        elif 'gold' in listing_lower:
            return 'Gold'
        elif 'classic' in listing_lower or 'clássico' in listing_lower:
            return 'Classic'
        elif 'silver' in listing_lower:
            return 'Silver'
        elif 'bronze' in listing_lower:
            return 'Bronze'
        
        # Verifica pelas tags
        tags_str = ' '.join(tags).lower()
        if 'premium' in tags_str:
            return 'Premium'
        elif 'gold' in tags_str:
            return 'Gold'
        elif 'classic' in tags_str or 'clássico' in tags_str:
            return 'Classic'
        
        return 'Standard'

    def debug_json_completo(self, mlb):
        """Debug: Mostra o JSON completo retornado pela API para um MLB"""
        try:
            headers = self._get_headers()
            
            print(f"\n🔍 DEBUG - Buscando MLB: {mlb}")
            print("=" * 60)
            
            # Faz a requisição para um item específico
            response = requests.get(
                f"{self.base_url}/items/{mlb}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                json_completo = response.json()
                
                print("✅ JSON COMPLETO DA API:")
                print(json.dumps(json_completo, indent=2, ensure_ascii=False))
                
                # Análise da estrutura shipping
                print("\n📦 ANALISE DA ESTRUTURA SHIPPING:")
                if 'shipping' in json_completo:
                    shipping = json_completo['shipping']
                    print(f"Chaves disponíveis no shipping: {list(shipping.keys())}")
                    for key, value in shipping.items():
                        print(f"  {key}: {value}")
                else:
                    print("  ❌ 'shipping' não encontrado no JSON")
                
                # Análise dos sale_terms
                print("\n📋 ANALISE DOS SALE_TERMS:")
                if 'sale_terms' in json_completo:
                    sale_terms = json_completo['sale_terms']
                    print(f"Total de sale_terms: {len(sale_terms)}")
                    for term in sale_terms:
                        print(f"  ID: {term.get('id')}, Name: {term.get('name')}, Value: {term.get('value_name')}")
                else:
                    print("  ❌ 'sale_terms' não encontrado no JSON")
                    
                # Mostra todas as chaves principais do JSON
                print("\n🔑 CHAVES PRINCIPAIS DO JSON:")
                for key in json_completo.keys():
                    print(f"  - {key}")
                    
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                print(f"Resposta: {response.text}")
                
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Erro no debug: {str(e)}")

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

    def excluir_anuncio_definitivo(self, mlb_id):
        """
        Exclui permanentemente um anúncio seguindo o fluxo oficial de 2 etapas:
        1. Fechar o anúncio (status: closed)
        2. Marcar como deletado (deleted: true)
        
        Documentação oficial: https://developers.mercadolivre.com.br/pt_br/atualiza-tuas-publicacoes
        """
        try:
            headers = self._get_headers()
            print(f"🔍 INICIANDO EXCLUSÃO DEFINITIVA DO MLB: {mlb_id}")
            
            # ETAPA 1: FECHAR O ANÚNCIO
            print("📋 ETAPA 1: Alterando status para 'closed'...")
            payload_fechar = {"status": "closed"}
            
            response_fechar = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=payload_fechar,
                timeout=30
            )
            
            print(f"📥 Resposta ETAPA 1 (fechar): Status {response_fechar.status_code}")
            
            if response_fechar.status_code != 200:
                error_msg = self._extrair_mensagem_erro(response_fechar)
                print(f"❌ FALHA na ETAPA 1: {error_msg}")
                return {
                    'sucesso': False,
                    'erro': f'Erro ao fechar anúncio: {error_msg}',
                    'etapa': 1,
                    'status_code': response_fechar.status_code
                }
            
            print("✅ ETAPA 1 concluída: Anúncio fechado com sucesso")
            
            # Aguarda 2 segundos para evitar erro de conflito
            import time
            time.sleep(2)
            
            # ETAPA 2: EXCLUIR PERMANENTEMENTE
            print("📋 ETAPA 2: Marcando como deletado permanente (deleted: true)...")
            payload_excluir = {"deleted": True}
            
            response_excluir = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=payload_excluir,
                timeout=30
            )
            
            print(f"📥 Resposta ETAPA 2 (deletar): Status {response_excluir.status_code}")
            
            # Tratamento especial para erro 409 (conflito)
            if response_excluir.status_code == 409:
                print("⚠️  Erro 409 - Conflito detectado. Aguardando e tentando novamente...")
                time.sleep(5)
                
                # Segunda tentativa
                response_excluir = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=payload_excluir,
                    timeout=30
                )
                print(f"📥 Segunda tentativa: Status {response_excluir.status_code}")
            
            if response_excluir.status_code == 200:
                print(f"🎉 EXCLUSÃO DEFINITIVA CONCLUÍDA! MLB {mlb_id} removido permanentemente.")
                
                # Verifica se realmente foi deletado
                try:
                    response_verificacao = requests.get(
                        f"{self.base_url}/items/{mlb_id}",
                        headers=headers,
                        timeout=10
                    )
                    if response_verificacao.status_code == 404:
                        print("✅ Confirmação: MLB não encontrado (excluído com sucesso)")
                    elif response_verificacao.status_code == 200:
                        data = response_verificacao.json()
                        if data.get('status') == 'closed' and 'deleted' in data.get('sub_status', []):
                            print("✅ Confirmação: MLB marcado como deletado no sistema")
                except:
                    pass  # Ignora erro na verificação
                
                return {
                    'sucesso': True,
                    'mensagem': f'MLB {mlb_id} excluído permanentemente do Mercado Livre.',
                    'etapa': 2,
                    'status_code': response_excluir.status_code,
                    'detalhes': response_excluir.json() if response_excluir.content else {}
                }
            else:
                error_msg = self._extrair_mensagem_erro(response_excluir)
                print(f"❌ FALHA na ETAPA 2: {error_msg}")
                return {
                    'sucesso': False,
                    'erro': f'Erro na exclusão permanente: {error_msg}',
                    'etapa': 2,
                    'status_code': response_excluir.status_code
                }
                
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT na exclusão do MLB {mlb_id}")
            return {
                'sucesso': False,
                'erro': 'Timeout na conexão com o Mercado Livre',
                'etapa': 'timeout'
            }
        except requests.exceptions.ConnectionError:
            print(f"❌ ERRO DE CONEXÃO na exclusão do MLB {mlb_id}")
            return {
                'sucesso': False,
                'erro': 'Erro de conexão com o Mercado Livre',
                'etapa': 'connection'
            }
        except Exception as e:
            print(f"❌ ERRO INESPERADO: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'sucesso': False,
                'erro': f'Erro inesperado: {str(e)}',
                'etapa': 'exception'
            }

    def _extrair_mensagem_erro(self, response):
        """Extrai mensagem de erro da resposta da API"""
        try:
            error_data = response.json()
            return error_data.get('message', error_data.get('error', str(error_data)))
        except:
            return response.text[:200] if response.text else f'Erro HTTP {response.status_code}'
    
# Instância global
ml_api_secure = MercadoLivreAPISecure()