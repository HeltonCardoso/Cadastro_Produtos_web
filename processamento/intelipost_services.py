"""
Serviços de processamento para Intelipost
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .intelipost_api import IntelipostAPI

logger = logging.getLogger(__name__)

class IntelipostService:
    """Serviço de processamento de dados Intelipost"""
    
    def __init__(self):
        self.api = IntelipostAPI()
    
    def formatar_dados_rastreio(self, dados_api: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata os dados brutos da API para exibição no template
        
        Args:
            dados_api: Dados brutos da API Intelipost
            
        Returns:
            Dados formatados para o template
        """
        try:
            content = dados_api.get('content', {})
            
            if not content:
                raise Exception("Dados da API vazios")
            
            # Processar volumes
            volumes = content.get('shipment_order_volume_array', [])
            volumes_formatados = []
            
            for volume in volumes:
                volume_formatado = self._processar_volume(volume)
                volumes_formatados.append(volume_formatado)
            
            # Dados principais formatados
            dados_formatados = {
                'status_geral': 'success' if dados_api.get('status') == 'OK' else 'error',
                'pedido': {
                    'numero': content.get('order_number'),
                    'numero_vendas': content.get('sales_order_number'),
                    'data_criacao': self._formatar_data(content.get('created')),
                    'data_modificacao': self._formatar_data(content.get('modified')),
                    'metodo_entrega': content.get('delivery_method_name'),
                    'transportadora': content.get('logistic_provider_name'),
                    'url_rastreio': content.get('tracking_url'),
                    'previsao_entrega': self._formatar_data(content.get('estimated_delivery_date')),
                    'data_envio': self._formatar_data(content.get('shipped_date')),
                    'custo_frete': content.get('customer_shipping_costs'),
                    'canal_venda': content.get('sales_channel'),
                    'tipo_pedido': content.get('shipment_order_type'),
                    'agendado': content.get('scheduled', False)
                },
                'cliente': {
                    'nome': f"{content.get('end_customer', {}).get('first_name', '')} {content.get('end_customer', {}).get('last_name', '')}".strip(),
                    'email': content.get('end_customer', {}).get('email'),
                    'telefone': content.get('end_customer', {}).get('phone'),
                    'celular': content.get('end_customer', {}).get('cellphone'),
                    'documento': content.get('end_customer', {}).get('federal_tax_payer_id'),
                    'endereco': self._formatar_endereco(content.get('end_customer', {})),
                    'cidade': content.get('end_customer', {}).get('shipping_city'),
                    'estado': content.get('end_customer', {}).get('shipping_state'),
                    'cep': content.get('end_customer', {}).get('shipping_zip_code')
                },
                'origem': {
                    'nome': content.get('origin_name'),
                    'cidade': content.get('origin_city'),
                    'estado': content.get('origin_state_code'),
                    'endereco': f"{content.get('origin_street')} {content.get('origin_number')}",
                    'bairro': content.get('origin_quarter'),
                    'cep': content.get('origin_zip_code'),
                    'documento': content.get('origin_federal_tax_payer_id'),
                    'email': content.get('origin_customer_email'),
                    'telefone': content.get('origin_customer_phone')
                },
                'volumes': volumes_formatados,
                'motorista': content.get('carrier', {}).get('driver') if content.get('carrier') else None,
                'veiculo': content.get('carrier', {}).get('vehicle') if content.get('carrier') else None,
                'informacoes_adicionais': content.get('additional_information', {}),
                'numeros_externos': content.get('external_order_numbers', {}),
                'verificacao': dados_api.get('verification', {}),
                'metadata': {
                    'tempo_resposta': dados_api.get('time'),
                    'timezone': dados_api.get('timezone'),
                    'locale': dados_api.get('locale')
                }
            }
            
            return dados_formatados
            
        except Exception as e:
            logger.error(f"Erro ao formatar dados de rastreio: {str(e)}")
            raise
    
    def _processar_volume(self, volume: Dict[str, Any]) -> Dict[str, Any]:
        """Processa os dados de um volume específico"""
        historico = volume.get('shipment_order_volume_state_history_array', [])
        
        return {
            'numero': volume.get('shipment_order_volume_number'),
            'codigo_rastreio': volume.get('logistic_provider_tracking_code'),
            'status': volume.get('shipment_order_volume_state_localized'),
            'status_codigo': volume.get('shipment_order_volume_state'),
            'peso': volume.get('weight'),
            'dimensoes': {
                'altura': volume.get('height'),
                'largura': volume.get('width'),
                'comprimento': volume.get('length')
            },
            'tipo_volume': volume.get('volume_type_code'),
            'natureza_produtos': volume.get('products_nature'),
            'quantidade_produtos': volume.get('products_quantity'),
            'entregue': volume.get('delivered', False),
            'atrasado': volume.get('delivered_late', False),
            'historico': self._processar_historico(historico),
            'produtos': volume.get('products', []),
            'nota_fiscal': volume.get('shipment_order_volume_invoice'),
            'nome': volume.get('name'),
            'cliente_lista_envio': volume.get('client_pre_shipment_list'),
            'lista_envio_status': volume.get('pre_shipment_list_state'),
            'rastreio_hash': volume.get('logistic_provider_label_hash')
        }
    
    def _processar_historico(self, historico: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processa o histórico de eventos do volume"""
        historico_processado = []
        
        for evento in sorted(historico, key=lambda x: x.get('event_date', 0), reverse=True):
            micro_state = evento.get('shipment_volume_micro_state', {})
            
            historico_processado.append({
                'status': evento.get('shipment_order_volume_state_localized'),
                'status_codigo': evento.get('shipment_order_volume_state'),
                'descricao': micro_state.get('description'),
                'data': self._formatar_data(evento.get('event_date')),
                'data_iso': evento.get('event_date_iso'),
                'local': self._formatar_local(evento.get('location', {})),
                'id_historico': evento.get('shipment_order_volume_state_history'),
                'data_criacao': self._formatar_data(evento.get('created'))
            })
        
        return historico_processado
    
    def _formatar_data(self, timestamp: Optional[int]) -> Optional[str]:
        """Formata timestamp para data legível"""
        if not timestamp:
            return None
        
        try:
            # Verifica se timestamp está em milissegundos
            if timestamp > 1e12:
                timestamp = timestamp / 1000
            
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return None
    
    def _formatar_endereco(self, cliente: Dict[str, Any]) -> str:
        """Formata o endereço completo do cliente"""
        partes = [
            cliente.get('shipping_address'),
            cliente.get('shipping_number'),
            cliente.get('shipping_additional'),
            cliente.get('shipping_quarter')
        ]
        
        endereco = ', '.join(filter(None, partes))
        if cliente.get('shipping_reference'):
            endereco += f" ({cliente.get('shipping_reference')})"
        
        return endereco
    
    def _formatar_local(self, local: Dict[str, Any]) -> str:
        """Formata informações de localização"""
        partes = [
            local.get('address'),
            local.get('number'),
            local.get('city'),
            local.get('state_code')
        ]
        
        return ', '.join(filter(None, partes)) or 'Local não informado'
    
    def obter_estatisticas_uso(self) -> Dict[str, Any]:
        """Obtém estatísticas de uso da API"""
        return {
            'cache_itens': len(self.api._cache),
            'api_configurada': bool(self.api.api_key and self.api.api_key != 'sua_chave_api_aqui'),
            'base_url': self.api.base_url
        }