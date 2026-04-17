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
    
    def debug_manufacturing_time_detalhado(self, mlb_id):
        """Debug completo do manufacturing time"""
        try:
            headers = self._get_headers()
            
            print(f"\n🔍 DEBUG COMPLETO - MLB: {mlb_id}")
            print("=" * 60)
            
            # Busca dados atuais
            response = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                dados = response.json()
                
                print("📋 DADOS DO ITEM:")
                print(f"- ID: {dados.get('id')}")
                print(f"- Status: {dados.get('status')}")
                print(f"- Listing Type: {dados.get('listing_type_id')}")
                
                # Manufacturing time direto
                print(f"\n🔧 MANUFACTURING_TIME DIRETO:")
                mt_direto = dados.get('manufacturing_time')
                print(f"- manufacturing_time: {mt_direto}")
                print(f"- Tipo: {type(mt_direto)}")
                
                # Sale terms
                print(f"\n📋 SALE_TERMS:")
                sale_terms = dados.get('sale_terms', [])
                print(f"- Total de termos: {len(sale_terms)}")
                
                for i, term in enumerate(sale_terms):
                    if term.get('id') == 'MANUFACTURING_TIME':
                        print(f"\n  ✅ ENCONTRADO MANUFACTURING_TIME:")
                        print(f"    - ID: {term.get('id')}")
                        print(f"    - Name: {term.get('name')}")
                        print(f"    - Value Name: {term.get('value_name')}")
                        print(f"    - Estrutura completa: {term}")
                
                print("=" * 60)
                return dados
                
            else:
                print(f"❌ Erro: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return None
    
    def remover_manufacturing_time(self, mlb_id):
        """Remove completamente o manufacturing time (prazo = 0/sem prazo)"""
        try:
            headers = self._get_headers()
            
            print(f"🔄 Tentando REMOVER prazo do MLB: {mlb_id}")
            
            # Primeiro debug para entender a estrutura
            dados_item = self.debug_manufacturing_time_detalhado(mlb_id)
            if not dados_item:
                return {'sucesso': False, 'erro': 'Não foi possível buscar dados do item'}
            
            sale_terms_atuais = dados_item.get('sale_terms', [])
            
            # 🔍 Vamos testar abordagens possíveis
            abordagens = [
                # 1. Sale_terms vazio
                ("sale_terms_vazio", {"sale_terms": []}),
                
                # 2. Mantém outros termos, remove apenas manufacturing
                ("remove_apenas_manufacturing", self._preparar_sale_terms_sem_manufacturing(sale_terms_atuais)),
                
                # 3. Manufacturing_time como string vazia
                ("campo_direto_vazio", {"manufacturing_time": ""}),
                
                # 4. Manufacturing_time como None
                ("campo_direto_none", {"manufacturing_time": None}),
                
                # 5. Manufacturing_time como "0 dias"
                ("zero_dias", {"sale_terms": [{"id": "MANUFACTURING_TIME", "value_name": "0 dias"}]}),
            ]
            
            # Testa cada abordagem
            for nome, update_data in abordagens:
                print(f"\n🔄 Testando: {nome}")
                
                if not update_data:
                    continue
                
                response = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=update_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"   ✅ SUCESSO! Prazo removido")
                    return {
                        'sucesso': True,
                        'mensagem': f'Prazo removido',
                        'abordagem': nome,
                        'dias': 0
                    }
                else:
                    error_data = response.json()
                    print(f"   ❌ Falhou: {error_data.get('message', '')}")
            
            return {'sucesso': False, 'erro': 'Todas as abordagens falharam'}
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def _preparar_sale_terms_sem_manufacturing(self, sale_terms):
        """Prepara sale_terms removendo apenas MANUFACTURING_TIME"""
        if not sale_terms:
            return {"sale_terms": []}
        
        novos_terms = []
        for term in sale_terms:
            if term.get('id') != 'MANUFACTURING_TIME':
                # Mantém a estrutura mínima
                term_minimo = {
                    "id": term.get('id'),
                    "value_name": term.get('value_name', '')
                }
                novos_terms.append(term_minimo)
        
        return {"sale_terms": novos_terms}

    def atualizar_manufacturing_time(self, mlb_id, manufacturing_time_days):
        """
        Atualiza o manufacturing time
        - Se dias > 0: Define prazo normalmente
        - Se dias = 0: Tenta REMOVER o prazo
        """
        try:
            # Se for para REMOVER prazo (dias=0)
            if manufacturing_time_days == 0:
                return self.remover_manufacturing_time(mlb_id)
            
            # Se for para DEFINIR prazo (dias>0) - use sua lógica atual
            headers = self._get_headers()
            
            print(f"🔄 Definindo prazo {manufacturing_time_days} dias para MLB: {mlb_id}")
            
            # Sua lógica atual para definir prazo (que já funciona)
            value_name = f"{manufacturing_time_days} dias"
            
            update_data = {
                "sale_terms": [
                    {
                        "id": "MANUFACTURING_TIME",
                        "value_name": value_name
                    }
                ]
            }
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Prazo definido para {manufacturing_time_days} dias")
                return {
                    'sucesso': True,
                    'mensagem': f'Prazo definido para {manufacturing_time_days} dias',
                    'dias': manufacturing_time_days
                }
            else:
                # Tentar com campo direto
                update_data_alt = {
                    "manufacturing_time": f"{manufacturing_time_days} dias"
                }
                
                response_alt = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=update_data_alt,
                    timeout=30
                )
                
                if response_alt.status_code == 200:
                    print(f"✅ Prazo definido (campo direto)")
                    return {'sucesso': True, 'mensagem': f'Prazo {manufacturing_time_days} dias definido'}
                else:
                    error_data = response_alt.json()
                    return {
                        'sucesso': False,
                        'erro': f"Erro: {error_data.get('message', '')}",
                        'dias': manufacturing_time_days
                    }
                    
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}

    def _atualizar_apenas_manufacturing(self, mlb_id, manufacturing_time_days, headers):
        """Atualiza apenas o manufacturing_time sem mexer em outros campos"""
        try:
            # Primeiro verifica se o item existe e está ativo
            response_get = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            
            if response_get.status_code != 200:
                return {'sucesso': False, 'erro': 'Item não encontrado'}
            
            # 🔹 ABORDAGEM DIRETA: Envia apenas manufacturing_time no nível raiz
            if manufacturing_time_days > 0:
                update_data = {
                    "manufacturing_time": f"{manufacturing_time_days} dias"
                }
            else:
                update_data = {
                    "manufacturing_time": ""  # String vazia para remover
                }
            
            print(f"📤 Enviando update direto: {update_data}")
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                mensagem = f"Prazo {'removido' if manufacturing_time_days == 0 else f'definido para {manufacturing_time_days} dias'}"
                print(f"✅ {mensagem} (update direto)")
                return {'sucesso': True, 'mensagem': mensagem}
            else:
                # 🔹 ÚLTIMA TENTATIVA: Com sale_terms mínimo
                print("🔄 Última tentativa (estrutura mínima)...")
                if manufacturing_time_days > 0:
                    sale_terms = [{
                        "id": "MANUFACTURING_TIME",
                        "value_name": f"{manufacturing_time_days} dias"
                    }]
                else:
                    sale_terms = []
                
                update_data_final = {"sale_terms": sale_terms}
                
                response_final = requests.put(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    json=update_data_final,
                    timeout=30
                )
                
                if response_final.status_code == 200:
                    mensagem = f"Prazo {'removido' if manufacturing_time_days == 0 else 'atualizado'}"
                    print(f"✅ {mensagem} (estrutura mínima)")
                    return {'sucesso': True, 'mensagem': mensagem}
                else:
                    error_data = response_final.json()
                    return {'sucesso': False, 'erro': f"Erro final: {error_data.get('message', '')}"}
                    
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    def _remover_duplicatas_sale_terms(self, sale_terms):
        """Remove termos duplicados mantendo a primeira ocorrência"""
        if not sale_terms:
            return []
        
        termos_vistos = set()
        termos_unicos = []
        
        for term in sale_terms:
            term_id = term.get('id')
            if not term_id:
                termos_unicos.append(term)
                continue
                
            # Cria uma chave única baseada no ID e no valor
            value_id = term.get('value_id')
            value_name = term.get('value_name', '')
            chave = f"{term_id}_{value_id}_{value_name}"
            
            if chave not in termos_vistos:
                termos_vistos.add(chave)
                termos_unicos.append(term)
        
        print(f"🔍 Removidas {len(sale_terms) - len(termos_unicos)} duplicatas de sale_terms")
        return termos_unicos

    def _tentar_abordagem_alternativa_remocao(self, mlb_id, headers, dados_atuais):
        """Tentativa alternativa para remover manufacturing time quando a primeira falhar"""
        try:
            print(f"🔄 Tentando abordagem alternativa para MLB {mlb_id}...")
            
            # 🔹 ABORDAGEM 1: Tentar com campo manufacturing_time vazio
            update_data_alt1 = {
                "manufacturing_time": ""
            }
            
            print(f"📤 Tentativa 1 (campo vazio): {update_data_alt1}")
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data_alt1,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Prazo removido com campo vazio")
                return {
                    'sucesso': True,
                    'mensagem': 'Prazo removido (sem prazo)',
                    'dias': 0,
                    'abordagem': 'campo_vazio'
                }
            
            # 🔹 ABORDAGEM 2: Tentar com manufacturing_time None/null
            print("📤 Tentativa 2 (campo None)...")
            update_data_alt2 = {
                "manufacturing_time": None
            }
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_data_alt2,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Prazo removido com campo None")
                return {
                    'sucesso': True,
                    'mensagem': 'Prazo removido (sem prazo)',
                    'dias': 0,
                    'abordagem': 'campo_none'
                }
            
            # 🔹 ABORDAGEM 3: Tentar atualizar todo o item
            print("📤 Tentativa 3 (update completo)...")
            
            # Cria uma cópia dos dados atuais
            dados_update = dados_atuais.copy()
            
            # Remove manufacturing_time se existir
            if 'manufacturing_time' in dados_update:
                del dados_update['manufacturing_time']
            
            # Remove MANUFACTURING_TIME dos sale_terms
            if 'sale_terms' in dados_update:
                dados_update['sale_terms'] = [
                    term for term in dados_update['sale_terms'] 
                    if term.get('id') != 'MANUFACTURING_TIME'
                ]
            
            # Mantém apenas campos essenciais para update
            campos_permitidos = ['title', 'available_quantity', 'price', 'condition', 
                            'shipping', 'sale_terms', 'pictures', 'attributes']
            
            dados_filtrados = {k: v for k, v in dados_update.items() 
                            if k in campos_permitidos}
            
            # Adiciona sale_terms vazio se necessário
            if 'sale_terms' not in dados_filtrados:
                dados_filtrados['sale_terms'] = []
            
            print(f"📤 Enviando update completo (campos filtrados)")
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=dados_filtrados,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Prazo removido com update completo")
                return {
                    'sucesso': True,
                    'mensagem': 'Prazo removido (sem prazo)',
                    'dias': 0,
                    'abordagem': 'update_completo'
                }
            else:
                error_msg = f"Todas as abordagens falharam. Último erro: {response.status_code}"
                print(f"❌ {error_msg}")
                return {
                    'sucesso': False,
                    'erro': error_msg
                }
                
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
                time.sleep(0.5)
            
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
            time.sleep(1)
            
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
    
    ########################################  ALTERAÇÂO DO CAMPO MODELO #############################################

    def _buscar_opcoes_atributo(self, atributo_id, category_id):
        """
        Busca todas as opções válidas para um atributo, incluindo "Não se aplica"
        """
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/categories/{category_id}/attributes"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                atributos_cat = response.json()
                for attr in atributos_cat:
                    if attr.get('id') == atributo_id:
                        valores = []
                        for valor in attr.get('values', []):
                            valores.append({
                                'id': valor.get('id'),
                                'nome': valor.get('name')
                            })
                        
                        # Verifica se tem a opção "Não se aplica"
                        tem_na = any(v['nome'].lower() in ['não se aplica', 'nao se aplica', 'not applicable', 'n/a'] 
                                    for v in valores)
                        
                        return {
                            'valores': valores,
                            'tem_nao_se_aplica': tem_na
                        }
                return {'valores': [], 'tem_nao_se_aplica': False}
            return {'valores': [], 'tem_nao_se_aplica': False}
        except:
            return {'valores': [], 'tem_nao_se_aplica': False}
    
    def buscar_atributo_modelo(self, mlb):
        """
        Busca o valor atual do atributo MODELO de um produto
        """
        try:
            headers = self._get_headers()
            url = f"https://api.mercadolibre.com/items/{mlb}"
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': f'Erro ao buscar produto: {response.status_code}',
                    'mlb': mlb
                }
            
            dados = response.json()
            
            # Procura o atributo MODEL
            modelo_atual = None
            for atributo in dados.get('attributes', []):
                if atributo.get('id') == 'MODEL':
                    modelo_atual = {
                        'id': atributo.get('id'),
                        'name': atributo.get('name'),
                        'value_id': atributo.get('value_id'),
                        'value_name': atributo.get('value_name'),
                        'values': atributo.get('values', [])
                    }
                    break
            
            return {
                'sucesso': True,
                'mlb': mlb,
                'titulo': dados.get('title'),
                'modelo_atual': modelo_atual,
                'modelo_valor': modelo_atual.get('value_name') if modelo_atual else 'Não definido'
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'mlb': mlb
            }

    def buscar_modelos_disponiveis(self, mlb=None):
        """
        Busca os modelos disponíveis para um produto (valores possíveis)
        """
        try:
            # Lista de modelos comuns (fallback)
            modelos_comuns = [
                {'id': '2833029', 'name': 'Daisy'},
                {'id': '2833030', 'name': 'Lily'},
                {'id': '2833031', 'name': 'Rose'},
                {'id': '2833032', 'name': 'Tulip'},
                {'id': '2833033', 'name': 'Sunflower'},
                {'id': '2833034', 'name': 'Orchid'},
                {'id': '2833035', 'name': 'Lavender'},
                {'id': '2833036', 'name': 'Jasmine'},
                {'id': '2833037', 'name': 'Violet'},
                {'id': '2833038', 'name': 'Magnolia'},
            ]
            
            # Se tiver um MLB, tenta buscar modelos específicos da categoria
            if mlb:
                try:
                    headers = self._get_headers()
                    url = f"https://api.mercadolibre.com/items/{mlb}"
                    response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        dados = response.json()
                        category_id = dados.get('category_id')
                        
                        if category_id:
                            url_cat = f"https://api.mercadolibre.com/categories/{category_id}/attributes"
                            response_cat = requests.get(url_cat, headers=headers, timeout=15)
                            
                            if response_cat.status_code == 200:
                                atributos = response_cat.json()
                                for attr in atributos:
                                    if attr.get('id') == 'MODEL':
                                        valores = []
                                        for valor in attr.get('values', []):
                                            valores.append({
                                                'id': valor.get('id'),
                                                'name': valor.get('name')
                                            })
                                        if valores:
                                            return {
                                                'sucesso': True,
                                                'modelos_disponiveis': valores,
                                                'category_id': category_id
                                            }
                except Exception as e:
                    print(f"Erro ao buscar modelos da categoria: {e}")
            
            return {
                'sucesso': True,
                'modelos_disponiveis': modelos_comuns,
                'observacao': 'Lista de modelos comuns. Verifique se o modelo desejado existe na categoria do produto.'
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def alterar_modelo_produto(self, mlb, novo_modelo_nome):
        """
        Altera o atributo MODELO de um produto
        
        Args:
            mlb: ID do produto (ex: MLB1234567890)
            novo_modelo_nome: Nome do novo modelo (ex: Esportivo, Luxo, Daisy)
        """
        try:
            headers = self._get_headers()
            url = f"https://api.mercadolibre.com/items/{mlb}"
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': f'Erro ao buscar produto: {response.status_code}',
                    'mlb': mlb
                }
            
            dados = response.json()
            
            # Atualiza ou adiciona o atributo MODELO
            atributos = dados.get('attributes', [])
            modelo_encontrado = False
            
            for i, attr in enumerate(atributos):
                if attr.get('id') == 'MODEL':
                    atributos[i] = {
                        'id': 'MODEL',
                        'name': 'Modelo',
                        'value_name': novo_modelo_nome,
                        'value_struct': None
                    }
                    modelo_encontrado = True
                    break
            
            if not modelo_encontrado:
                atributos.append({
                    'id': 'MODEL',
                    'name': 'Modelo',
                    'value_name': novo_modelo_nome,
                    'value_struct': None
                })
            
            # Prepara o payload para atualização
            payload = {
                'attributes': atributos
            }
            
            # Envia a atualização
            url_update = f"https://api.mercadolibre.com/items/{mlb}"
            response_update = requests.put(url_update, headers=headers, json=payload, timeout=30)
            
            if response_update.status_code == 200:
                return {
                    'sucesso': True,
                    'mlb': mlb,
                    'modelo_novo': novo_modelo_nome,
                    'mensagem': f'Modelo alterado para "{novo_modelo_nome}" com sucesso!'
                }
            else:
                return {
                    'sucesso': False,
                    'erro': f'Erro ao atualizar: {response_update.status_code} - {response_update.text[:200]}',
                    'mlb': mlb
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'mlb': mlb
            }

    def alterar_modelo_multiplos(self, mlbs, novo_modelo_nome):
        """
        Altera o modelo de múltiplos produtos em lote
        """
        import time
        resultados = []
        sucessos = 0
        erros = 0
        
        for mlb in mlbs:
            resultado = self.alterar_modelo_produto(mlb, novo_modelo_nome)
            resultados.append(resultado)
            
            if resultado.get('sucesso'):
                sucessos += 1
            else:
                erros += 1
            
            time.sleep(1)
        
        return {
            'sucesso': sucessos > 0,
            'total': len(mlbs),
            'sucessos': sucessos,
            'erros': erros,
            'resultados': resultados
        }

    def _extrair_mensagem_erro(self, response):
        """Extrai mensagem de erro da resposta da API"""
        try:
            error_data = response.json()
            return error_data.get('message', error_data.get('error', str(error_data)))
        except:
            return response.text[:200] if response.text else f'Erro HTTP {response.status_code}'

    def verificar_requisitos_me2(self, mlb_id):
        """
        Verifica se um anúncio específico atende a todos os requisitos para ser migrado para ME2.
        """
        try:
            headers = self._get_headers()
            print(f"\n🔍 VERIFICANDO REQUISITOS ME2 PARA MLB: {mlb_id}")
            print("=" * 60)

            # 1. Busca dados do item
            response_item = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            if response_item.status_code != 200:
                return {'sucesso': False, 'erro': 'Item não encontrado'}
            
            item = response_item.json()
            category_id = item.get('category_id')
            print(f"📂 Categoria: {category_id}")
            print(f"🏷️ Domínio: {item.get('domain_id')}")

            # 2. Verifica atributos de dimensão (essenciais para ME2)
            atributos_necessarios = [
                'SELLER_PACKAGE_HEIGHT',
                'SELLER_PACKAGE_LENGTH', 
                'SELLER_PACKAGE_WIDTH',
                'SELLER_PACKAGE_WEIGHT'
            ]
            
            atributos_item = {attr['id']: attr for attr in item.get('attributes', [])}
            atributos_presentes = []
            atributos_ausentes = []
            
            print("\n📋 Verificando atributos de dimensão:")
            for attr_id in atributos_necessarios:
                if attr_id in atributos_item:
                    value = atributos_item[attr_id].get('value_name', 'N/A')
                    print(f"  ✅ {attr_id}: {value}")
                    atributos_presentes.append(attr_id)
                else:
                    print(f"  ❌ {attr_id}: AUSENTE")
                    atributos_ausentes.append(attr_id)
            
            # 3. Verifica shipping.dimensions
            shipping_dimensions = item.get('shipping', {}).get('dimensions')
            print(f"\n📦 shipping.dimensions: {shipping_dimensions}")
            
            # 4. Verifica se modo atual é me1
            modo_atual = item.get('shipping', {}).get('mode')
            print(f"📦 Modo de envio atual: {modo_atual}")
            
            # 5. Verifica preferências do usuário
            response_user = requests.get(
                f"{self.base_url}/users/me",
                headers=headers,
                timeout=10
            )
            user_id = response_user.json()['id']
            
            response_prefs = requests.get(
                f"{self.base_url}/users/{user_id}/shipping_preferences",
                headers=headers,
                timeout=10
            )
            
            me2_habilitado = False
            if response_prefs.status_code == 200:
                prefs = response_prefs.json()
                me2_habilitado = 'me2' in prefs.get('modes', [])
                print(f"\n👤 ME2 habilitado na conta: {'✅ SIM' if me2_habilitado else '❌ NÃO'}")
            
            # 6. Verifica se categoria suporta ME2
            response_cat = requests.get(
                f"{self.base_url}/categories/{category_id}/shipping_preferences",
                headers=headers,
                timeout=10
            )
            
            categoria_suporta = False
            if response_cat.status_code == 200:
                cat_data = response_cat.json()
                for logistics in cat_data.get('logistics', []):
                    if logistics.get('mode') == 'me2':
                        categoria_suporta = True
                        break
                print(f"📦 Categoria suporta ME2: {'✅ SIM' if categoria_suporta else '❌ NÃO'}")
            
            # 7. Resultado
            print("\n" + "=" * 60)
            if not atributos_ausentes and shipping_dimensions and modo_atual == 'me1' and me2_habilitado and categoria_suporta:
                print("🎉 RESULTADO: ANÚNCIO PRONTO PARA MIGRAR PARA ME2!")
                return {
                    'sucesso': True, 
                    'pronto': True,
                    'dimensoes': shipping_dimensions,
                    'atributos': atributos_presentes,
                    'modo_atual': modo_atual,
                    'me2_habilitado': me2_habilitado,
                    'categoria_suporta': categoria_suporta
                }
            else:
                problemas = []
                if atributos_ausentes:
                    problemas.append(f"Atributos ausentes: {atributos_ausentes}")
                if not shipping_dimensions:
                    problemas.append("shipping.dimensions não preenchido")
                if modo_atual != 'me1':
                    problemas.append(f"Modo atual é {modo_atual}, não me1")
                if not me2_habilitado:
                    problemas.append("ME2 não habilitado na sua conta")
                if not categoria_suporta:
                    problemas.append("Categoria não suporta ME2")
                
                print("⚠️ RESULTADO: ANÚNCIO NÃO PRONTO")
                for problema in problemas:
                    print(f"   - {problema}")
                
                return {
                    'sucesso': True,
                    'pronto': False,
                    'problemas': problemas,
                    'atributos_ausentes': atributos_ausentes,
                    'modo_atual': modo_atual,
                    'me2_habilitado': me2_habilitado,
                    'categoria_suporta': categoria_suporta
                }
                
        except Exception as e:
            print(f"❌ Erro na verificação: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}

    def alterar_para_me2(self, mlb_id):
        """
        Altera um anúncio existente para o modo de envio ME2.
        Versão otimizada baseada no debug que funcionou!
        """
        try:
            headers = self._get_headers()
            
            print(f"\n🚀 INICIANDO MIGRAÇÃO PARA ME2 - MLB: {mlb_id}")
            print("=" * 60)
            
            # 1. Busca dados do anúncio (apenas para informação)
            response = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return {'sucesso': False, 'erro': 'Não foi possível buscar o anúncio'}
            
            item = response.json()
            modo_anterior = item.get('shipping', {}).get('mode')
            
            print(f"📦 Modo atual: {modo_anterior}")
            
            # 2. Prepara payload MÍNIMO (o único que funcionou no debug)
            update_payload = {
                "shipping": {
                    "mode": "me2"
                }
            }
            
            print(f"\n📤 Enviando atualização:")
            print(f"   Modo: {modo_anterior} → me2")
            print(f"   Payload: {json.dumps(update_payload, indent=2)}")
            
            # 3. Faz a requisição PUT com payload mínimo
            response_put = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_payload,
                timeout=30
            )
            
            if response_put.status_code == 200:
                print(f"\n✅ SUCESSO! Anúncio migrado para ME2")
                
                # 4. Verifica a mudança
                import time
                time.sleep(2)
                response_check = requests.get(
                    f"{self.base_url}/items/{mlb_id}",
                    headers=headers,
                    timeout=10
                )
                
                if response_check.status_code == 200:
                    novo_mode = response_check.json().get('shipping', {}).get('mode')
                    print(f"✅ Confirmação: Modo agora é {novo_mode}")
                    
                    return {
                        'sucesso': True,
                        'mensagem': f'Anúncio {mlb_id} migrado para ME2',
                        'modo_anterior': modo_anterior,
                        'modo_atual': novo_mode,
                        'mlb': mlb_id
                    }
                else:
                    return {
                        'sucesso': True,
                        'mensagem': f'Anúncio {mlb_id} migrado para ME2',
                        'mlb': mlb_id
                    }
            else:
                error_data = response_put.json()
                error_msg = error_data.get('message', str(error_data))
                print(f"❌ Erro: {error_msg}")
                
                return {
                    'sucesso': False,
                    'erro': error_msg,
                    'mlb': mlb_id
                }
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e), 'mlb': mlb_id}

    def _tentar_abordagem_alternativa_me2(self, mlb_id, item, headers):
        """Segunda tentativa com payload um pouco mais completo"""
        try:
            print("\n🔄 Tentando abordagem alternativa...")
            
            # Extrai apenas os campos essenciais que a API aceita
            campos_permitidos = ['title', 'price', 'available_quantity', 'shipping']
            
            update_payload = {}
            
            # Adiciona título se existir
            if 'title' in item:
                update_payload['title'] = item['title']
            
            # Adiciona preço se existir
            if 'price' in item:
                update_payload['price'] = item['price']
            
            # Adiciona quantidade se existir
            if 'available_quantity' in item:
                update_payload['available_quantity'] = item['available_quantity']
            
            # Configura shipping
            dimensions = item.get('shipping', {}).get('dimensions')
            update_payload['shipping'] = {
                'mode': 'me2'
            }
            
            if dimensions:
                update_payload['shipping']['dimensions'] = dimensions
            
            print(f"📤 Enviando payload alternativo:")
            print(json.dumps(update_payload, indent=2))
            
            response = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=update_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ SUCESSO (abordagem alternativa)!")
                return {
                    'sucesso': True,
                    'mensagem': f'Anúncio {mlb_id} migrado para ME2',
                    'mlb': mlb_id
                }
            else:
                error_data = response.json()
                error_msg = error_data.get('message', str(error_data))
                return {
                    'sucesso': False,
                    'erro': f'Falha: {error_msg}',
                    'mlb': mlb_id
                }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'mlb': mlb_id}

    def debug_mudanca_envio(self, mlb_id):
        """
        Função de debug para entender o que a API espera
        """
        try:
            headers = self._get_headers()
            
            print(f"\n🔍 DEBUG - Tentando entender o erro BODY_INVALID_FIELDS")
            print("=" * 60)
            
            # 1. Busca o item atual
            response = requests.get(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Erro ao buscar item: {response.status_code}")
                return
            
            item = response.json()
            
            print(f"\n📦 Item encontrado: {item.get('id')}")
            print(f"   Título: {item.get('title')}")
            print(f"   Status: {item.get('status')}")
            print(f"   Modo atual: {item.get('shipping', {}).get('mode')}")
            
            # 2. Tenta com payload MÍNIMO POSSÍVEL
            print(f"\n🔄 Tentativa 1: Payload mínimo")
            payload1 = {
                "shipping": {
                    "mode": "me2"
                }
            }
            
            print(f"   Payload: {json.dumps(payload1, indent=2)}")
            
            response1 = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=payload1,
                timeout=30
            )
            
            print(f"   Status: {response1.status_code}")
            if response1.status_code != 200:
                try:
                    error = response1.json()
                    print(f"   Erro: {error.get('message', 'Desconhecido')}")
                    print(f"   Detalhes: {json.dumps(error, indent=2)}")
                except:
                    print(f"   Resposta: {response1.text[:200]}")
            
            # 3. Tenta com shipping completo incluindo dimensions
            print(f"\n🔄 Tentativa 2: Payload com dimensions")
            dimensions = item.get('shipping', {}).get('dimensions')
            payload2 = {
                "shipping": {
                    "mode": "me2"
                }
            }
            
            if dimensions:
                payload2["shipping"]["dimensions"] = dimensions
            
            print(f"   Payload: {json.dumps(payload2, indent=2)}")
            
            response2 = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=payload2,
                timeout=30
            )
            
            print(f"   Status: {response2.status_code}")
            if response2.status_code != 200:
                try:
                    error = response2.json()
                    print(f"   Erro: {error.get('message', 'Desconhecido')}")
                    print(f"   Detalhes: {json.dumps(error, indent=2)}")
                except:
                    print(f"   Resposta: {response2.text[:200]}")
            
            # 4. Tenta com shipping completo incluindo free_shipping e local_pick_up
            print(f"\n🔄 Tentativa 3: Payload completo do shipping")
            payload3 = {
                "shipping": {
                    "mode": "me2",
                    "local_pick_up": item.get('shipping', {}).get('local_pick_up', False),
                    "free_shipping": item.get('shipping', {}).get('free_shipping', False)
                }
            }
            
            if dimensions:
                payload3["shipping"]["dimensions"] = dimensions
            
            print(f"   Payload: {json.dumps(payload3, indent=2)}")
            
            response3 = requests.put(
                f"{self.base_url}/items/{mlb_id}",
                headers=headers,
                json=payload3,
                timeout=30
            )
            
            print(f"   Status: {response3.status_code}")
            if response3.status_code != 200:
                try:
                    error = response3.json()
                    print(f"   Erro: {error.get('message', 'Desconhecido')}")
                except:
                    print(f"   Resposta: {response3.text[:200]}")
            
            print("\n" + "=" * 60)
            return {
                'tentativa1': response1.status_code,
                'tentativa2': response2.status_code,
                'tentativa3': response3.status_code
            }
            
        except Exception as e:
            print(f"❌ Erro no debug: {str(e)}")
            return None
    
    def alterar_multiplos_para_me2(self, lista_mlbs):
        """
        Altera múltiplos anúncios para ME2
        Versão otimizada baseada no debug
        """
        try:
            resultados = []
            sucessos = 0
            falhas = 0
            ignorados = 0
            
            print(f"\n🚀 INICIANDO MIGRAÇÃO EM MASSA PARA ME2")
            print(f"Total de MLBs: {len(lista_mlbs)}")
            print("=" * 60)
            
            for i, mlb_id in enumerate(lista_mlbs, 1):
                print(f"\n📌 [{i}/{len(lista_mlbs)}] Processando MLB: {mlb_id}")
                
                # Verifica se já está em ME2
                try:
                    headers = self._get_headers()
                    response = requests.get(
                        f"{self.base_url}/items/{mlb_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        modo_atual = response.json().get('shipping', {}).get('mode')
                        if modo_atual == 'me2':
                            print(f"   ⏭️ Já está em ME2, ignorando")
                            resultados.append({
                                'mlb': mlb_id,
                                'sucesso': True,
                                'mensagem': 'Já estava em ME2',
                                'ignorado': True
                            })
                            ignorados += 1
                            continue
                except:
                    pass
                
                # Tenta migrar com payload mínimo
                resultado = self.alterar_para_me2(mlb_id)
                
                if resultado.get('sucesso'):
                    sucessos += 1
                    print(f"   ✅ Migrado com sucesso!")
                else:
                    falhas += 1
                    print(f"   ❌ Falha: {resultado.get('erro', 'Erro desconhecido')}")
                
                resultados.append(resultado)
                
                # Delay para não sobrecarregar a API
                import time
                time.sleep(1)
            
            # Resumo final
            print("\n" + "=" * 60)
            print("📊 RESUMO DA MIGRAÇÃO:")
            print(f"   Total processados: {len(lista_mlbs)}")
            print(f"   ✅ Migrados com sucesso: {sucessos}")
            print(f"   ⏭️  Já estavam em ME2: {ignorados}")
            print(f"   ❌ Falhas: {falhas}")
            
            return {
                'sucesso': sucessos > 0 or ignorados > 0,
                'resultados': resultados,
                'total': len(lista_mlbs),
                'sucessos': sucessos,
                'ignorados': ignorados,
                'falhas': falhas
            }
            
        except Exception as e:
            print(f"❌ Erro na migração em massa: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
        
    def _get_headers(self):
        """Retorna headers com token atualizado"""
        token = ml_token_manager.get_valid_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def buscar_todos_atributos_produto(self, mlb):
        try:
            headers = self._get_headers()

            url_item = f"{self.base_url}/items/{mlb}"
            response_item = requests.get(url_item, headers=headers, timeout=15)

            if response_item.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': f'Erro ao buscar produto: {response_item.status_code}',
                    'mlb': mlb
                }

            item = response_item.json()
            category_id = item.get('category_id')

            url_cat = f"{self.base_url}/categories/{category_id}/attributes"
            resp_cat = requests.get(url_cat, headers=headers, timeout=15)

            if resp_cat.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': f'Erro categoria atributos: {resp_cat.status_code}',
                    'mlb': mlb
                }

            cat_attrs = resp_cat.json()
            item_attrs = {a['id']: a for a in item.get('attributes', [])}

            atributos = []

            for cat_attr in cat_attrs:
                attr_id = cat_attr.get('id')
                item_attr = item_attrs.get(attr_id, {})

                value_name = item_attr.get('value_name')
                value_id = item_attr.get('value_id')

                e_nao_se_aplica = self._eh_nao_se_aplica(value_id, value_name)

                esta_vazio = (
                    not value_name and
                    not value_id and
                    not e_nao_se_aplica
                )

                tags = cat_attr.get('tags', [])
                obrigatorio = 'required' in tags
                recomendado = 'recommended' in tags

                relevance = cat_attr.get('relevance', 0)

                if obrigatorio or relevance >= 2:
                    categoria = 'principal'
                elif recomendado or relevance == 1:
                    categoria = 'recomendado'
                else:
                    categoria = 'secundario'

                valores = cat_attr.get('values', [])

                atributos.append({
                    'id': attr_id,
                    'nome': cat_attr.get('name'),
                    'valor': None if e_nao_se_aplica else value_name,
                    'value_id': value_id,
                    'valores_possiveis': valores,
                    'tem_nao_se_aplica': any(v.get('id') == "-1" for v in valores),
                    'e_nao_se_aplica': e_nao_se_aplica,
                    'esta_vazio': esta_vazio,
                    'obrigatorio': obrigatorio,
                    'recomendado': recomendado,
                    'categoria': categoria,
                    'relevance': relevance
                })

            qualidade = self._buscar_qualidade_oficial(mlb)

            if not qualidade:
                score_calculado = self.calcular_score_inteligente(atributos)
                qualidade = {
                    'pontuacao': score_calculado,
                    'nivel': self._nivel_por_score(score_calculado),
                    'dicas': ['Score calculado localmente — ML não retornou dados oficiais'],
                    'origem': 'calculado'
                }

            return {
                'sucesso': True,
                'mlb': mlb,
                'titulo': item.get('title'),
                'categoria_id': category_id,
                'atributos': atributos,
                'qualidade': qualidade
            }

        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'mlb': mlb
            }


    def _eh_nao_se_aplica(self, value_id, value_name):
        if value_id == "-1":
            return True

        if value_name:
            return value_name.strip().lower() in [
                "não se aplica",
                "nao se aplica",
                "n/a",
                "not applicable"
            ]

        return False


    def _buscar_qualidade_oficial(self, mlb):
        try:
            headers = self._get_headers()

            endpoints = [
                f"{self.base_url}/items/{mlb}/quality",
                f"{self.base_url}/items/{mlb}/listing_quality"
            ]

            for url in endpoints:
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code != 200:
                    continue

                dados = response.json()

                score = dados.get('quality_score') or dados.get('score')

                if score is None:
                    continue

                score = float(score)

                return {
                    'pontuacao': score,
                    'nivel': self._nivel_por_score(score),
                    'dicas': dados.get('tips', []),
                    'origem': 'oficial'
                }

            return None

        except Exception as e:
            print("Erro qualidade:", e)
            return None


    def _nivel_por_score(self, score):
        if score >= 80:
            return "Excelente"
        elif score >= 60:
            return "Bom"
        else:
            return "Precisa melhorar"


    def calcular_score_inteligente(self, atributos):
        obrigatorios = [a for a in atributos if a.get('obrigatorio')]

        if not obrigatorios:
            return 0

        preenchidos = [
            a for a in obrigatorios
            if a.get('valor') and not a.get('e_nao_se_aplica')
        ]

        base = (len(preenchidos) / len(obrigatorios)) * 60

        extras = 0
        extras += min(sum(1 for a in atributos if a.get('valor')), 10) * 3
        extras += min(sum(1 for a in atributos if a.get('e_nao_se_aplica')), 5) * 1

        score = base + extras

        return round(min(score, 100), 1)


    def alterar_multiplos_atributos(self, mlb, atributos_dict):
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/items/{mlb}"

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': f'Erro ao buscar produto: {response.status_code}',
                    'mlb': mlb
                }

            dados = response.json()
            atributos_existentes = dados.get('attributes', [])
            category_id = dados.get('category_id')

            url_cat = f"{self.base_url}/categories/{category_id}/attributes"
            resp_cat = requests.get(url_cat, headers=headers, timeout=15)

            if resp_cat.status_code != 200:
                return {
                    'sucesso': False,
                    'erro': f'Erro categoria: {resp_cat.status_code}',
                    'mlb': mlb
                }

            cat_attrs = resp_cat.json()
            cat_map = {a['id']: a for a in cat_attrs}

            for attr_id, attr_data in atributos_dict.items():

                if isinstance(attr_data, dict):
                    valor = attr_data.get('valor')
                    is_nao_se_aplica = attr_data.get('is_nao_se_aplica', False)
                else:
                    valor = attr_data
                    is_nao_se_aplica = False

                cat_attr = cat_map.get(attr_id, {})
                valores = cat_attr.get('values', [])

                novo = {
                    'id': attr_id,
                    'name': cat_attr.get('name', attr_id)
                }

                if is_nao_se_aplica:
                    if any(v.get('id') == "-1" for v in valores):
                        novo['value_id'] = "-1"
                    else:
                        continue
                elif valor:
                    novo['value_name'] = valor
                else:
                    continue

                encontrado = False
                for i, a in enumerate(atributos_existentes):
                    if a.get('id') == attr_id:
                        atributos_existentes[i] = novo
                        encontrado = True
                        break

                if not encontrado:
                    atributos_existentes.append(novo)

            payload = {'attributes': atributos_existentes}

            response_update = requests.put(url, headers=headers, json=payload, timeout=30)

            if response_update.status_code == 200:
                return {
                    'sucesso': True,
                    'mlb': mlb,
                    'mensagem': 'Atributos atualizados com sucesso'
                }

            return {
                'sucesso': False,
                'erro': response_update.text,
                'mlb': mlb
            }

        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'mlb': mlb
            }


    def _buscar_nome_atributo(self, atributo_id, category_id):
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/categories/{category_id}/attributes"
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                atributos = response.json()
                for attr in atributos:
                    if attr.get('id') == atributo_id:
                        return attr.get('name')
            return atributo_id
        except:
            return atributo_id


    def otimizar_qualidade_produto(self, mlb, auto_corrigir=True):
        resultado = self.buscar_todos_atributos_produto(mlb)

        if not resultado['sucesso']:
            return resultado

        qualidade = resultado['qualidade']
        atributos = resultado['atributos']

        if qualidade['pontuacao'] >= 80:
            return {
                'sucesso': True,
                'mlb': mlb,
                'qualidade': qualidade,
                'acao_tomada': 'nenhuma',
                'mensagem': 'Produto já possui qualidade profissional'
            }

        correcoes = []

        if auto_corrigir:
            for attr in atributos:
                if attr.get('valor') or not attr.get('valores_possiveis'):
                    continue

                primeiro_valor = (
                    attr['valores_possiveis'][0].get('name') or
                    attr['valores_possiveis'][0].get('id', '')
                )

                if not primeiro_valor:
                    continue

                self.alterar_multiplos_atributos(mlb, {
                    attr['id']: {'valor': primeiro_valor, 'is_nao_se_aplica': False}
                })

                correcoes.append({
                    'atributo': attr['nome'],
                    'valor_antigo': None,
                    'valor_novo': primeiro_valor
                })

        if correcoes:
            resultado_atualizado = self.buscar_todos_atributos_produto(mlb)
            qualidade_atualizada = resultado_atualizado['qualidade']

            return {
                'sucesso': True,
                'mlb': mlb,
                'qualidade_anterior': qualidade,
                'qualidade_atual': qualidade_atualizada,
                'correcoes_aplicadas': correcoes,
                'melhoria_pontos': qualidade_atualizada['pontuacao'] - qualidade['pontuacao'],
                'mensagem': f'Qualidade melhorou de {qualidade["pontuacao"]} para {qualidade_atualizada["pontuacao"]} pontos'
            }

        return {
            'sucesso': True,
            'mlb': mlb,
            'qualidade': qualidade,
            'acao_tomada': 'nenhuma',
            'mensagem': 'Produto precisa de melhorias manuais',
            'dicas': qualidade['dicas']
        }
        
   
# Instância global
ml_api_secure = MercadoLivreAPISecure()