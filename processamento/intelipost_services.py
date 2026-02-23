import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelipostService:
    """Serviço de processamento de dados Intelipost"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa o serviço"""
        from .intelipost_api import IntelipostAPI
        
        if api_key:
            self.api = IntelipostAPI(api_key=api_key)
            logger.info(f"✅ IntelipostService criado com API key")
        else:
            self.api = None
            logger.warning("⚠️ IntelipostService criado sem API key")
    
    def formatar_dados_rastreio(self, dados_api: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata os dados brutos da API para exibição
        """
        try:
            logger.info(f"📊 Formatando dados da API...")
            
            if not dados_api:
                return {'erro': 'Dados da API vazios'}
            
            content = dados_api.get('content', {})
            
            if not content:
                return {'erro': 'Conteúdo vazio na resposta'}
            
            logger.info(f"✅ Dados válidos recebidos")
            
            # ========== DADOS DO PEDIDO ==========
            pedido_data = {
                'numero': content.get('order_number', 'N/D'),
                'numero_vendas': content.get('sales_order_number', 'N/D'),
                'transportadora': content.get('logistic_provider_name', 'N/D'),
                'data_criacao': self._formatar_data(content.get('created')),
                'data_criacao_iso': content.get('created_iso', 'N/D'),
                'data_modificacao': self._formatar_data(content.get('modified')),
                'data_modificacao_iso': content.get('modified_iso', 'N/D'),
                'metodo_entrega': content.get('delivery_method_name', 'N/D'),
                'metodo_entrega_id': content.get('delivery_method_id', 'N/D'),
                'metodo_entrega_externo_id': content.get('delivery_method_external_id', 'N/D'),
                'url_rastreio': content.get('tracking_url', ''),
                'previsao_entrega': self._formatar_data(content.get('estimated_delivery_date')),
                'previsao_entrega_iso': content.get('estimated_delivery_date_iso', 'N/D'),
                'data_envio': self._formatar_data(content.get('shipped_date')),
                'data_envio_iso': content.get('shipped_date_iso', 'N/D'),
                'custo_frete': self._formatar_valor(content.get('customer_shipping_costs')),
                'canal_venda': content.get('sales_channel', 'N/D'),
                'tipo_pedido': content.get('shipment_order_type', 'N/D'),
                'agendado': content.get('scheduled', False),
                'plataforma': content.get('platform', 'N/D'),
                'warehouse_id': content.get('warehouse_address_id', 'N/D'),
                'observacoes': content.get('observation', ''),
                'id': content.get('id', 'N/D')
            }
            
            # ========== DADOS DO CLIENTE ==========
            cliente_data = content.get('end_customer', {})
            cliente_formatado = {
                'nome': f"{cliente_data.get('first_name', '')} {cliente_data.get('last_name', '')}".strip(),
                'email': cliente_data.get('email', 'N/D'),
                'telefone': cliente_data.get('phone', 'N/D'),
                'celular': cliente_data.get('cellphone', 'N/D'),
                'documento': cliente_data.get('federal_tax_payer_id', 'N/D'),
                'empresa': cliente_data.get('is_company', False),
                'documento_estado': cliente_data.get('state_tax_payer_id', 'N/D'),
                'cidade': cliente_data.get('shipping_city', 'N/D'),
                'estado': cliente_data.get('shipping_state', 'N/D'),
                'estado_codigo': cliente_data.get('shipping_state_code', 'N/D'),
                'cep': cliente_data.get('shipping_zip_code', 'N/D'),
                'pais': cliente_data.get('shipping_country', 'Brasil'),
                'endereco': f"{cliente_data.get('shipping_address', '')} {cliente_data.get('shipping_number', '')}".strip(),
                'complemento': cliente_data.get('shipping_additional', ''),
                'bairro': cliente_data.get('shipping_quarter', 'N/D'),
                'referencia': cliente_data.get('shipping_reference', '')
            }
            
            # ========== DADOS DE ORIGEM ==========
            origem_data = {
                'nome': content.get('origin_name', 'N/D'),
                'cidade': content.get('origin_city', 'N/D'),
                'estado': content.get('origin_state_code', 'N/D'),
                'endereco': f"{content.get('origin_street', '')} {content.get('origin_number', '')}".strip(),
                'bairro': content.get('origin_quarter', 'N/D'),
                'cep': content.get('origin_zip_code', 'N/D'),
                'documento': content.get('origin_federal_tax_payer_id', 'N/D'),
                'email': content.get('origin_customer_email', 'N/D'),
                'telefone': content.get('origin_customer_phone', 'N/D')
            }
            
            # ========== DADOS DO MOTORISTA ==========
            motorista_data = {}
            veiculo_data = {}
            
            carrier = content.get('carrier', {})
            if carrier:
                driver = carrier.get('driver', {})
                if driver:
                    motorista_data = {
                        'nome': f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip(),
                        'documento': driver.get('federal_tax_id', 'N/D'),
                        'cnh': driver.get('license', 'N/D'),
                        'email': driver.get('email', 'N/D'),
                        'celular': driver.get('cell_phone', 'N/D')
                    }
                
                vehicle = carrier.get('vehicle', {})
                if vehicle:
                    veiculo_data = {
                        'placa': vehicle.get('licence_plate', 'N/D'),
                        'fabricante': vehicle.get('manufacturer', 'N/D'),
                        'modelo': vehicle.get('model', 'N/D'),
                        'cor': vehicle.get('color', 'N/D'),
                        'categoria': vehicle.get('category', 'N/D')
                    }
            
            # ========== VOLUMES ==========
            volumes = content.get('shipment_order_volume_array', [])
            volumes_formatados = []
            
            logger.info(f"📦 Processando {len(volumes)} volume(s)")
            
            for i, volume in enumerate(volumes):
                volume_formatado = self._processar_volume(volume, i)
                volumes_formatados.append(volume_formatado)
            
            # ========== DADOS FINAIS FORMATADOS ==========
            dados_formatados = {
                'status_geral': 'success',
                'pedido': pedido_data,
                'cliente': cliente_formatado,
                'origem': origem_data,
                'motorista': motorista_data,
                'veiculo': veiculo_data,
                'volumes': volumes_formatados,
                'informacoes_adicionais': content.get('additional_information', {}),
                'numeros_externos': content.get('external_order_numbers', {}),
                'verificacao': dados_api.get('verification', {}),
                'metadata': {
                    'tempo_resposta': dados_api.get('time'),
                    'timezone': dados_api.get('timezone'),
                    'locale': dados_api.get('locale'),
                    'status_api': dados_api.get('status', 'N/D'),
                    'mensagens': dados_api.get('messages', [])
                }
            }
            
            return dados_formatados
            
        except Exception as e:
            logger.error(f"❌ Erro ao formatar dados: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'erro': f'Erro ao processar dados: {str(e)}',
                'dados_brutos': dados_api
            }
    
    def _processar_volume(self, volume: Dict[str, Any], indice: int) -> Dict[str, Any]:
        """Processa os dados de um volume específico"""
        # Histórico de eventos
        historico = volume.get('shipment_order_volume_state_history_array', [])
        historico_formatado = []
        
        for evento in historico:
            micro_state = evento.get('shipment_volume_micro_state', {})
            location = evento.get('location', {})
            
            evento_formatado = {
                'status': evento.get('shipment_order_volume_state_localized', 'N/D'),
                'status_codigo': evento.get('shipment_order_volume_state', 'N/D'),
                'data': self._formatar_data(evento.get('event_date')),
                'data_iso': evento.get('event_date_iso', 'N/D'),
                'descricao': micro_state.get('description', ''),
                'micro_status': micro_state.get('default_name', ''),
                'micro_status_i18n': micro_state.get('i18n_name', ''),
                'local': self._formatar_local(location),
                'id_historico': evento.get('shipment_order_volume_state_history', 'N/D'),
                'data_criacao': self._formatar_data(evento.get('created'))
            }
            historico_formatado.append(evento_formatado)
        
        # Ordenar histórico por data (mais recente primeiro)
        historico_formatado.sort(key=lambda x: x.get('data_iso', ''), reverse=True)
        
        # Produtos no volume
        produtos = volume.get('products', [])
        produtos_formatados = []
        
        for produto in produtos:
            produto_formatado = {
                'id': produto.get('id', 'N/D'),
                'descricao': produto.get('description', 'N/D'),
                'sku': produto.get('sku', 'N/D'),
                'quantidade': produto.get('quantity', 1),
                'preco': self._formatar_valor(produto.get('price')),
                'dimensoes': {
                    'comprimento': produto.get('length'),
                    'largura': produto.get('width'),
                    'altura': produto.get('height')
                },
                'dimensoes_str': f"{produto.get('length', '')}×{produto.get('width', '')}×{produto.get('height', '')} cm",
                'peso': produto.get('weight'),
                'peso_str': f"{produto.get('weight', '')} kg" if produto.get('weight') else 'N/D',
                'categoria': produto.get('category', ''),
                'imagem': produto.get('image_url', ''),
                'volume_total': produto.get('quantity', 1) * (produto.get('price') or 0)
            }
            produtos_formatados.append(produto_formatado)
        
        # Nota fiscal do volume
        nota_fiscal = volume.get('shipment_order_volume_invoice', {})
        nota_fiscal_formatada = {
            'serie': nota_fiscal.get('invoice_series', ''),
            'numero': nota_fiscal.get('invoice_number', ''),
            'chave': nota_fiscal.get('invoice_key', ''),
            'valor_total': self._formatar_valor(nota_fiscal.get('invoice_total_value')),
            'valor_produtos': self._formatar_valor(nota_fiscal.get('invoice_products_value')),
            'cfop': nota_fiscal.get('invoice_cfop', ''),
            'data': self._formatar_data(nota_fiscal.get('invoice_date_iso')),
            'data_iso': nota_fiscal.get('invoice_date_iso_iso', '')
        }
        
        # Dados do volume
        volume_formatado = {
            'numero': volume.get('shipment_order_volume_number', f'Volume {indice + 1}'),
            'id': volume.get('shipment_order_volume_id', 'N/D'),
            'codigo_rastreio': volume.get('logistic_provider_tracking_code', 'N/D'),
            'tracking_code': volume.get('tracking_code', 'N/D'),
            'status': volume.get('shipment_order_volume_state_localized', 'N/D'),
            'status_codigo': volume.get('shipment_order_volume_state', 'N/D'),
            'peso': volume.get('weight'),
            'peso_str': f"{volume.get('weight', '')} kg" if volume.get('weight') else 'N/D',
            'dimensoes': {
                'altura': volume.get('height'),
                'largura': volume.get('width'),
                'comprimento': volume.get('length')
            },
            'dimensoes_str': f"{volume.get('length', '')}×{volume.get('width', '')}×{volume.get('height', '')} cm",
            'tipo_volume': volume.get('volume_type_code', 'N/D'),
            'natureza_produtos': volume.get('products_nature', 'N/D'),
            'quantidade_produtos': volume.get('products_quantity', 0),
            'entregue': volume.get('delivered', False),
            'atrasado': volume.get('delivered_late', False),
            'nome': volume.get('name', f'Volume {indice + 1}'),
            'data_criacao': self._formatar_data(volume.get('created')),
            'data_criacao_iso': volume.get('created_iso', ''),
            'data_envio': self._formatar_data(volume.get('shipped_date')),
            'data_envio_iso': volume.get('shipped_date_iso', ''),
            'previsao_entrega': self._formatar_data(volume.get('estimated_delivery_date')),
            'previsao_entrega_iso': volume.get('estimated_delivery_date_iso', ''),
            'lista_envio_cliente': volume.get('client_pre_shipment_list', ''),
            'lista_envio_status': volume.get('pre_shipment_list_state', ''),
            'historico': historico_formatado,
            'produtos': produtos_formatados,
            'nota_fiscal': nota_fiscal_formatada,
            'hash_etiqueta': volume.get('logistic_provider_label_hash'),
            'codigo_embalagem': volume.get('packaging_code'),
            'is_icms_exempt': volume.get('is_icms_exempt', False)
        }
        
        return volume_formatado
    

    def formatar_dados_rastreio_por_nf(self, dados_api):
        """Formata dados de rastreio obtidos por número da Nota Fiscal"""
        try:
            print(f"\n🔧 Formatando dados por NF...")
            print(f"📊 Dados API recebidos: {dados_api.get('status', 'N/A')}")
            print(f"🔍 Tem 'content'?: {'content' in dados_api}")
            
            if 'status' not in dados_api:
                return {
                    'sucesso': False,
                    'mensagem': 'Resposta da API inválida',
                    'pedidos': []
                }
            
            if dados_api.get('status') != 'OK':
                print(f"⚠️ Status não é OK: {dados_api.get('status')}")
                return {
                    'sucesso': False,
                    'mensagem': dados_api.get('messages', ['Erro na API'])[0] if dados_api.get('messages') else 'Erro na API',
                    'pedidos': []
                }
            
            if not dados_api.get('content'):
                print(f"⚠️ Content vazio ou None")
                return {
                    'sucesso': False,
                    'mensagem': 'Nenhum pedido encontrado para esta Nota Fiscal',
                    'pedidos': []
                }
            
            pedidos = dados_api.get('content', [])
            print(f"📦 Encontrados {len(pedidos)} pedido(s) para esta NF")
            
            pedidos_formatados = []
            
            for pedido in pedidos:
                print(f"\n🔍 Processando pedido: {pedido.get('order_number', 'N/A')}")
                
                # Extrair informações básicas do pedido
                end_customer = pedido.get('end_customer', {})
                
                # Pegar informações da NF do primeiro volume
                nota_fiscal_info = {}
                volumes = pedido.get('shipment_order_volume_array', [])
                if volumes:
                    for volume in volumes:
                        invoice = volume.get('shipment_order_volume_invoice')
                        if invoice:
                            nota_fiscal_info = {
                                'numero': invoice.get('invoice_number'),
                                'serie': invoice.get('invoice_series'),
                                'chave': invoice.get('invoice_key'),
                                'data': invoice.get('invoice_date_iso_iso')
                            }
                            break
                
                # Formatar data da NF
                nf_data_formatada = None
                if nota_fiscal_info.get('data'):
                    try:
                        from datetime import datetime
                        # Remove o timezone para simplificar
                        dt_str = nota_fiscal_info['data'].split('.')[0].replace('T', ' ')
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        nf_data_formatada = dt.strftime('%d/%m/%Y %H:%M')
                    except Exception as e:
                        print(f"⚠️ Erro ao formatar data: {e}")
                        nf_data_formatada = nota_fiscal_info['data']
                
                # Processar volumes
                volumes_formatados = []
                for volume in volumes:
                    invoice = volume.get('shipment_order_volume_invoice', {})
                    volumes_formatados.append({
                        'numero_volume': volume.get('shipment_order_volume_number', 'N/A'),
                        'status_volume': volume.get('shipment_order_volume_state_localized', 'N/A'),
                        'peso': f"{volume.get('weight', 0)} kg",
                        'dimensoes': f"{volume.get('length', 0)}x{volume.get('width', 0)}x{volume.get('height', 0)} cm",
                        'rastreio': volume.get('logistic_provider_tracking_code') or volume.get('tracking_code') or 'Não disponível',
                        'nota_fiscal': invoice.get('invoice_number'),
                        'serie_nf': invoice.get('invoice_series')
                    })
                
                # Processar histórico do primeiro volume
                historico_formatado = []
                if volumes:
                    primeiro_volume = volumes[0]
                    historico = primeiro_volume.get('shipment_order_volume_state_history_array', [])
                    for evento in historico:
                        event_date = evento.get('event_date_iso')
                        data_formatada = 'Data não disponível'
                        if event_date:
                            try:
                                dt_str = event_date.split('.')[0].replace('T', ' ')
                                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                                data_formatada = dt.strftime('%d/%m/%Y %H:%M')
                            except:
                                data_formatada = event_date
                        
                        historico_formatado.append({
                            'data': data_formatada,
                            'status': evento.get('shipment_order_volume_state_localized', 'N/A'),
                            'descricao': evento.get('shipment_volume_micro_state', {}).get('description', 'Sem descrição')
                        })
                
                pedido_formatado = {
                    'pedido': pedido.get('order_number', 'N/A'),
                    'pedido_venda': pedido.get('sales_order_number', 'N/A'),
                    'nota_fiscal': nota_fiscal_info.get('numero'),
                    'nf_serie': nota_fiscal_info.get('serie'),
                    'nf_chave': nota_fiscal_info.get('chave'),
                    'nf_data': nf_data_formatada,
                    'cliente': f"{end_customer.get('first_name', '')} {end_customer.get('last_name', '')}".strip() or end_customer.get('email', 'N/A'),
                    'cidade_destino': end_customer.get('shipping_city', 'N/A'),
                    'estado_destino': end_customer.get('shipping_state_code', 'N/A'),
                    'transportadora': pedido.get('logistic_provider_name', 'N/A'),
                    'status': pedido.get('shipment_order_volume_state_localized', 'N/A'),
                    'volumes': volumes_formatados,
                    'historico': historico_formatado,
                    'informacoes_adicionais': {
                        'plataforma': pedido.get('platform', 'N/A'),
                        'canal_venda': pedido.get('sales_channel', 'N/A'),
                        'valor_frete': f"R$ {pedido.get('customer_shipping_costs', 0):.2f}" if pedido.get('customer_shipping_costs') else 'N/A',
                        'data_envio': pedido.get('shipped_date_iso', 'N/A'),
                        'data_estimada': pedido.get('estimated_delivery_date_lp_iso', 'N/A')
                    }
                }
                
                pedidos_formatados.append(pedido_formatado)
                print(f"✅ Pedido {pedido_formatado['pedido']} formatado com sucesso")
            
            print(f"✅ Total de {len(pedidos_formatados)} pedido(s) formatado(s)")
            
            return {
                'sucesso': True,
                'pedidos': pedidos_formatados,
                'quantidade_pedidos': len(pedidos_formatados),
                'consulta_por': 'NF'
            }
            
        except Exception as e:
            print(f"❌ Erro ao formatar dados por NF: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'sucesso': False,
                'erro': f'Erro ao processar dados: {str(e)}',
                'pedidos': []
            }
    

    def _formatar_local(self, local: Dict[str, Any]) -> str:
        """Formata informações de localização"""
        if not local:
            return 'Local não informado'
        
        partes = []
        
        # Endereço completo
        endereco_parts = []
        if local.get('address'):
            endereco_parts.append(local.get('address'))
            if local.get('number'):
                endereco_parts.append(local.get('number'))
        
        if endereco_parts:
            partes.append(', '.join(endereco_parts))
        
        # Cidade/Estado
        cidade_estado = []
        if local.get('city'):
            cidade_estado.append(local.get('city'))
        if local.get('state_code'):
            cidade_estado.append(local.get('state_code'))
        
        if cidade_estado:
            partes.append(' - '.join(cidade_estado))
        
        # Bairro
        if local.get('quarter'):
            partes.append(f"Bairro: {local.get('quarter')}")
        
        # CEP
        if local.get('zip_code'):
            partes.append(f"CEP: {local.get('zip_code')}")
        
        # Descrição adicional
        if local.get('description'):
            partes.append(local.get('description'))
        
        local_str = ' | '.join(filter(None, partes))
        return local_str if local_str else 'Local não informado'
    
    def _formatar_data(self, timestamp: Optional[int]) -> Optional[str]:
        """Formata timestamp para data legível"""
        if not timestamp:
            return None
        
        try:
            # Converte de milissegundos para segundos se necessário
            if timestamp > 1e12:
                timestamp = timestamp / 1000
            
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return None
    
    def _formatar_valor(self, valor: Optional[float]) -> Optional[str]:
        """Formata valor monetário"""
        if valor is None:
            return None
        
        try:
            return f"R$ {float(valor):.2f}".replace('.', ',')
        except:
            return str(valor)