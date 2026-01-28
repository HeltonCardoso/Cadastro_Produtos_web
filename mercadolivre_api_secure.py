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
        """Atualiza o manufacturing time de um anúncio - VERSÃO CORRIGIDA"""
        try:
            headers = self._get_headers()
            
            # 🔹 CORREÇÃO: Tratar dias=0 de forma especial
            if manufacturing_time_days == 0:
                value_name = ""  # String vazia para REMOVER o prazo
                mensagem = "Prazo removido (sem prazo)"
            else:
                value_name = f"{manufacturing_time_days} dias"  # String normal para definir prazo
                mensagem = f"Manufacturing Time atualizado para {manufacturing_time_days} dias"
            
            # Prepara os dados de atualização
            update_data = {
                "sale_terms": [
                    {
                        "id": "MANUFACTURING_TIME",
                        "value_name": value_name
                    }
                ]
            }
            
            print(f"🔄 Atualizando MLB {mlb_id} - Manufacturing Time: {value_name if value_name else 'REMOVER PRAZO'}")
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ {mensagem}")
                return {
                    'sucesso': True,
                    'mensagem': mensagem,
                    'dias': manufacturing_time_days,
                    'detalhes': f'Valor enviado: "{value_name}"'
                }
            else:
                error_msg = f"Erro HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ {error_msg}")
                
                # 🔹 TENTATIVA ALTERNATIVA se a primeira falhar para dias=0
                if manufacturing_time_days == 0 and response.status_code == 400:
                    return self._tentar_abordagem_alternativa_remocao(mlb_id, headers)
                
                return {
                    'sucesso': False,
                    'erro': error_msg,
                    'dias': manufacturing_time_days
                }
                
        except Exception as e:
            print(f"❌ Erro ao atualizar manufacturing time: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _tentar_abordagem_alternativa_remocao(self, mlb_id, headers):
        """Tentativa alternativa para remover manufacturing time"""
        try:
            print(f"🔄 Tentando abordagem alternativa para MLB {mlb_id}...")
            
            # Primeiro busca os dados atuais para ver a estrutura
            response_get = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            
            if response_get.status_code != 200:
                return {'sucesso': False, 'erro': 'Não foi possível buscar dados do item'}
            
            dados_atuais = response_get.json()
            print(f"📋 Dados atuais do MLB {mlb_id}:")
            print(f"   - Sale terms: {dados_atuais.get('sale_terms', [])}")
            
            # Verifica se tem outros sale_terms além do manufacturing
            sale_terms_atuais = dados_atuais.get('sale_terms', [])
            outros_terms = []
            
            for term in sale_terms_atuais:
                if term.get('id') != 'MANUFACTURING_TIME':
                    outros_terms.append(term)  # Mantém os outros termos
            
            # Prepara update_data sem o MANUFACTURING_TIME
            update_data = {}
            if outros_terms:
                # Mantém os outros termos e OMITE o MANUFACTURING_TIME
                update_data["sale_terms"] = outros_terms
                print(f"✅ Mantendo {len(outros_terms)} outros sale_terms")
            else:
                # Se não tem outros termos, envia array vazio
                update_data["sale_terms"] = []
                print(f"✅ Enviando sale_terms vazio")
            
            print(f"📤 Enviando (abordagem alternativa): {update_data}")
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Prazo removido com abordagem alternativa")
                return {
                    'sucesso': True,
                    'mensagem': 'Prazo removido (sem prazo)',
                    'dias': 0,
                    'abordagem': 'alternativa'
                }
            else:
                error_msg = f"Erro alternativo {response.status_code}: {response.text[:200]}"
                print(f"❌ {error_msg}")
                return {'sucesso': False, 'erro': error_msg}
                
        except Exception as e:
            print(f"❌ Erro na abordagem alternativa: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
        
    def atualizar_multiplos_manufacturing(self, atualizacoes):
        """Atualiza manufacturing time para múltiplos anúncios - VERSÃO MELHORADA"""
        try:
            resultados = []
            log_detalhado = []
            
            for idx, atualizacao in enumerate(atualizacoes):
                mlb_id = atualizacao.get('mlb')
                dias = atualizacao.get('dias')
                
                if not mlb_id or dias is None:
                    resultado = {
                        'mlb': mlb_id,
                        'sucesso': False,
                        'erro': 'MLB ou dias não fornecidos'
                    }
                    resultados.append(resultado)
                    log_detalhado.append(f"❌ {mlb_id}: MLB ou dias não fornecidos")
                    continue
                
                # Atualiza individualmente
                log_detalhado.append(f"🔄 [{idx+1}/{len(atualizacoes)}] {mlb_id} → {dias} dias")
                resultado = self.atualizar_manufacturing_time(mlb_id, dias)
                resultado['mlb'] = mlb_id
                resultados.append(resultado)
                
                if resultado.get('sucesso'):
                    log_detalhado.append(f"   ✅ Sucesso: {resultado.get('mensagem', '')}")
                else:
                    log_detalhado.append(f"   ❌ Erro: {resultado.get('erro', '')}")
                
                # Delay para evitar rate limit (maior delay para remoções)
                delay = 1.0 if dias == 0 else 0.5  # Mais tempo para remoções
                time.sleep(delay)
            
            # Estatísticas finais
            sucessos = len([r for r in resultados if r.get('sucesso')])
            erros = len([r for r in resultados if not r.get('sucesso')])
            removidos = len([r for r in resultados if r.get('sucesso') and r.get('dias') == 0])
            
            print(f"\n📊 RESUMO DA ATUALIZAÇÃO EM MASSA:")
            print(f"   Total processados: {len(atualizacoes)}")
            print(f"   Sucessos: {sucessos}")
            print(f"   Erros: {erros}")
            print(f"   Prazos removidos: {removidos}")
            
            return {
                'sucesso': sucessos > 0,
                'resultados': resultados,
                'total_atualizado': sucessos,
                'total_erros': erros,
                'prazos_removidos': removidos,
                'mensagem': f'{sucessos} de {len(atualizacoes)} atualizados com sucesso',
                'log_detalhado': log_detalhado
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
        Exclui permanentemente um anúncio com tratamento inteligente para diferentes status.
        
        Fluxo correto:
        1. Verificar status atual
        2. Se under_review: tentar excluir diretamente (sem fechar)
        3. Se active: pausar → fechar → marcar como deletado
        4. Se paused: fechar → marcar como deletado
        5. Se já closed: apenas marcar como deletado
        
        Documentação oficial: https://developers.mercadolivre.com.br/pt_br/atualiza-tuas-publicacoes
        """
        try:
            headers = self._get_headers()
            print(f"🔍 INICIANDO EXCLUSÃO DEFINITIVA DO MLB: {mlb_id}")
            
            # ETAPA 0: VERIFICAR STATUS ATUAL
            print("📋 ETAPA 0: Verificando status atual...")
            response_status = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            
            # Se o item já não existe
            if response_status.status_code == 404:
                print(f"✅ MLB {mlb_id} já não existe ou já foi excluído")
                return {
                    'sucesso': True,
                    'mensagem': f'MLB {mlb_id} já não existe no sistema',
                    'status_code': 404
                }
            
            current_status = 'unknown'
            if response_status.status_code == 200:
                item_data = response_status.json()
                current_status = item_data.get('status', 'unknown')
                print(f"📊 Status atual: {current_status}")
            
            # CASO ESPECIAL 1: ANÚNCIO EM REVISÃO
            if current_status == 'under_review':
                print("⚠️  Anúncio em revisão - Tentando exclusão direta...")
                
                # Tenta excluir diretamente sem fechar
                payload_excluir = {"deleted": True}
                
                response_excluir = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=payload_excluir,
                    timeout=30
                )
                
                print(f"📥 Resposta exclusão direta: Status {response_excluir.status_code}")
                
                if response_excluir.status_code == 200:
                    print(f"✅ Anúncio em revisão excluído com sucesso!")
                    return {
                        'sucesso': True,
                        'mensagem': f'MLB {mlb_id} (em revisão) excluído permanentemente.',
                        'status': current_status,
                        'detalhes': response_excluir.json() if response_excluir.content else {}
                    }
                else:
                    error_msg = self._extrair_mensagem_erro(response_excluir)
                    print(f"❌ Não foi possível excluir anúncio em revisão: {error_msg}")
                    return {
                        'sucesso': False,
                        'erro': f'Anúncio em revisão. Aguarde a análise do Mercado Livre para excluir: {error_msg}',
                        'status': current_status
                    }
            
            # CASO ESPECIAL 2: ANÚNCIO ATIVO - PRIMEIRO PAUSAR
            if current_status == 'active':
                print("📋 ETAPA 1 (ativo): Pausando anúncio primeiro...")
                payload_pausar = {"status": "paused"}
                
                response_pausar = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=payload_pausar,
                    timeout=30
                )
                
                print(f"📥 Resposta pausar: Status {response_pausar.status_code}")
                
                if response_pausar.status_code != 200:
                    error_msg = self._extrair_mensagem_erro(response_pausar)
                    print(f"❌ FALHA ao pausar anúncio ativo: {error_msg}")
                    return {
                        'sucesso': False,
                        'erro': f'Erro ao pausar anúncio: {error_msg}',
                        'etapa': 'pausar',
                        'status': current_status
                    }
                
                print("✅ Anúncio pausado com sucesso")
                import time
                time.sleep(2)
            
            # ETAPA 1 (GERAL): FECHAR O ANÚNCIO (closed)
            # Nota: Para under_review pulamos esta etapa, para active já pausamos, 
            # para paused vamos fechar direto
            print("📋 ETAPA 1 (geral): Alterando status para 'closed'...")
            payload_fechar = {"status": "closed"}
            
            response_fechar = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=payload_fechar,
                timeout=30
            )
            
            print(f"📥 Resposta ETAPA 1 (fechar): Status {response_fechar.status_code}")
            
            # Se já estiver fechado, continua normalmente
            if response_fechar.status_code != 200:
                error_msg = self._extrair_mensagem_erro(response_fechar)
                
                # Verifica se já está fechado
                if "already closed" in error_msg.lower() or current_status == 'closed':
                    print("ℹ️  Anúncio já estava fechado, continuando...")
                else:
                    print(f"❌ FALHA na ETAPA 1: {error_msg}")
                    
                    # Tenta abordagem alternativa para anúncios pausados
                    if current_status == 'paused':
                        print("🔄 Tentando abordagem alternativa para anúncio pausado...")
                        payload_alt = {
                            "status": "closed",
                            "deleted": False
                        }
                        response_fechar = requests.put(
                            f"{self.base_url}/items/{mlb_id}",
                            headers=headers,
                            json=payload_alt,
                            timeout=30
                        )
                        
                        if response_fechar.status_code != 200:
                            return {
                                'sucesso': False,
                                'erro': f'Erro ao fechar anúncio: {self._extrair_mensagem_erro(response_fechar)}',
                                'etapa': 1
                            }
                    else:
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
            
            # Tratamento especial para erro 400 (bad request)
            if response_excluir.status_code == 400:
                error_msg = self._extrair_mensagem_erro(response_excluir)
                print(f"⚠️  Erro 400 - Tentando abordagem alternativa: {error_msg}")
                
                # Tenta com payload diferente
                payload_alt = {
                    "deleted": True,
                    "status": "closed"
                }
                response_excluir = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=payload_alt,
                    timeout=30
                )
                print(f"📥 Tentativa alternativa: Status {response_excluir.status_code}")
            
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