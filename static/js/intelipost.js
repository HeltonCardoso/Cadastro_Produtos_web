/**
 * JavaScript para módulo Intelipost
 */
class IntelipostTracker {
    constructor() {
        this.baseUrl = '/intelipost';
        this.init();
    }
    
    init() {
        this.bindEvents();
    }
    
    bindEvents() {
        // Botão de busca
        const searchBtn = document.getElementById('intelipost-search-btn');
        const searchInput = document.getElementById('intelipost-order-number');
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.buscarRastreio());
        }
        
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.buscarRastreio();
                }
            });
        }
        
        // Botão de nova busca
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('intelipost-new-search')) {
                this.showSearchForm();
            }
        });
    }
    
    async buscarRastreio() {
        const orderNumber = document.getElementById('intelipost-order-number').value.trim();
        
        if (!orderNumber) {
            this.showError('Digite um número de pedido válido');
            return;
        }
        
        // Mostrar loading
        this.showLoading();
        
        try {
            const response = await fetch(`${this.baseUrl}/api/buscar-pedido/${orderNumber}`);
            const data = await response.json();
            
            if (data.sucesso) {
                this.exibirResultado(data.dados);
                this.registrarConsultaLocal(orderNumber);
            } else {
                this.showError(data.erro || 'Erro ao buscar rastreio');
            }
        } catch (error) {
            console.error('Erro:', error);
            this.showError('Erro de conexão com o servidor');
        } finally {
            this.hideLoading();
        }
    }
    
    exibirResultado(dados) {
        const resultadoDiv = document.getElementById('intelipost-result');
        resultadoDiv.innerHTML = this.gerarHTMLResultado(dados);
        resultadoDiv.style.display = 'block';
        
        // Scroll para o resultado
        resultadoDiv.scrollIntoView({ behavior: 'smooth' });
    }
    
    gerarHTMLResultado(dados) {
        let html = `
            <div class="intelipost-status-card">
                <div class="intelipost-status-header">
                    <div class="intelipost-order-number">
                        <i class="fas fa-box"></i>
                        Pedido: ${dados.pedido.numero || 'N/D'}
                    </div>
                    <div class="intelipost-status-badge ${this.getStatusClass(dados)}">
                        ${this.getStatusTexto(dados)}
                    </div>
                </div>
                
                <div class="intelipost-info-grid">
                    <div class="intelipost-info-card">
                        <h3><i class="fas fa-truck"></i> Informações da Entrega</h3>
                        ${this.gerarInfoItem('Transportadora', dados.pedido.transportadora)}
                        ${this.gerarInfoItem('Método', dados.pedido.metodo_entrega)}
                        ${this.gerarInfoItem('Enviado em', dados.pedido.data_envio)}
                        ${this.gerarInfoItem('Previsão', dados.pedido.previsao_entrega)}
                        ${dados.pedido.url_rastreio ? 
                            `<a href="${dados.pedido.url_rastreio}" class="intelipost-tracking-button" target="_blank">
                                <i class="fas fa-external-link-alt"></i> Rastrear na transportadora
                            </a>` : ''}
                    </div>
                    
                    <div class="intelipost-info-card">
                        <h3><i class="fas fa-user"></i> Destinatário</h3>
                        ${this.gerarInfoItem('Nome', dados.cliente.nome)}
                        ${this.gerarInfoItem('Telefone', dados.cliente.telefone)}
                        ${this.gerarInfoItem('Cidade', `${dados.cliente.cidade || ''} - ${dados.cliente.estado || ''}`)}
                        ${this.gerarInfoItem('CEP', dados.cliente.cep)}
                    </div>
                    
                    <div class="intelipost-info-card">
                        <h3><i class="fas fa-info-circle"></i> Detalhes</h3>
                        ${this.gerarInfoItem('Origem', `${dados.origem.cidade || ''} - ${dados.origem.estado || ''}`)}
                        ${this.gerarInfoItem('Canal', dados.pedido.canal_venda)}
                        ${this.gerarInfoItem('Valor frete', dados.pedido.custo_frete ? `R$ ${parseFloat(dados.pedido.custo_frete).toFixed(2)}` : 'N/D')}
                        ${this.gerarInfoItem('Volumes', dados.volumes.length)}
                    </div>
                </div>
            </div>
        `;
        
        // Adicionar volumes
        dados.volumes.forEach((volume, index) => {
            html += this.gerarHTMLVolume(volume, index);
        });
        
        // Botão de nova busca
        html += `
            <div class="text-center mt-4 mb-4">
                <button class="btn btn-outline-primary intelipost-new-search">
                    <i class="fas fa-search"></i> Nova Consulta
                </button>
            </div>
        `;
        
        return html;
    }
    
    gerarHTMLVolume(volume, index) {
        const historico = volume.historico || [];
        
        let html = `
            <div class="intelipost-volume-section">
                <div class="intelipost-volume-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <h4 style="margin: 0;">
                            <i class="fas fa-cube"></i> Volume ${volume.numero || index + 1}
                        </h4>
                        ${volume.codigo_rastreio ? 
                            `<span class="intelipost-tracking-code">${volume.codigo_rastreio}</span>` : ''}
                    </div>
                    <div>
                        <span class="intelipost-badge box">
                            <i class="fas fa-box"></i> ${volume.tipo_volume || 'BOX'}
                        </span>
                        ${volume.peso ? 
                            `<span class="intelipost-badge weight">
                                <i class="fas fa-weight-hanging"></i> ${volume.peso} kg
                            </span>` : ''}
                    </div>
                </div>
        `;
        
        // Histórico do volume
        if (historico.length > 0) {
            html += `
                <div class="intelipost-timeline-container">
                    <h5><i class="fas fa-history"></i> Histórico de Rastreamento</h5>
                    <div class="intelipost-timeline">
            `;
            
            historico.forEach((evento, idx) => {
                html += `
                    <div class="intelipost-timeline-item ${idx === 0 ? 'current' : ''}">
                        <div class="intelipost-timeline-content">
                            <div class="intelipost-timeline-header">
                                <div class="intelipost-timeline-title">
                                    <i class="fas fa-${this.getEventIcon(evento.status_codigo)}"></i>
                                    ${evento.status || 'N/D'}
                                </div>
                                <div class="intelipost-timeline-date">
                                    <i class="far fa-clock"></i> ${evento.data || 'N/D'}
                                </div>
                            </div>
                            ${evento.descricao ? 
                                `<div class="intelipost-timeline-description">${evento.descricao}</div>` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += `</div></div>`;
        }
        
        // Produtos do volume
        if (volume.produtos && volume.produtos.length > 0) {
            html += `
                <div class="intelipost-products-container">
                    <h5><i class="fas fa-shopping-cart"></i> Produtos no Volume</h5>
                    <div class="intelipost-products-grid">
            `;
            
            volume.produtos.forEach(produto => {
                html += this.gerarHTMLProduto(produto);
            });
            
            html += `</div></div>`;
        }
        
        html += `</div>`;
        return html;
    }
    
    gerarHTMLProduto(produto) {
        return `
            <div class="intelipost-product-card">
                <div class="intelipost-product-image">
                    ${produto.image_url ? 
                        `<img src="${produto.image_url}" alt="${produto.description}" 
                             onerror="this.onerror=null; this.parentElement.innerHTML='<i class=\\'fas fa-box\\'></i>';">` : 
                        `<i class="fas fa-box"></i>`
                    }
                </div>
                <div class="intelipost-product-info">
                    <h4>${produto.description || 'Produto sem nome'}</h4>
                    ${produto.sku ? `<span class="intelipost-product-sku">${produto.sku}</span>` : ''}
                    <div class="intelipost-product-details">
                        <span>Quantidade:</span>
                        <span>${produto.quantity || 1} un.</span>
                    </div>
                    ${produto.dimensions ? `
                        <div class="intelipost-product-details">
                            <span>Dimensões:</span>
                            <span>${produto.dimensions}</span>
                        </div>
                    ` : ''}
                    ${produto.weight ? `
                        <div class="intelipost-product-details">
                            <span>Peso:</span>
                            <span>${produto.weight} kg</span>
                        </div>
                    ` : ''}
                    ${produto.price ? `
                        <div class="intelipost-product-price">
                            R$ ${parseFloat(produto.price).toFixed(2)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    gerarInfoItem(label, value) {
        if (!value && value !== 0) return '';
        return `
            <div class="intelipost-info-item">
                <span>${label}:</span>
                <span>${value}</span>
            </div>
        `;
    }
    
    getStatusClass(dados) {
        if (!dados.volumes || dados.volumes.length === 0) return 'pending';
        
        const volume = dados.volumes[0];
        if (volume.entregue) return 'delivered';
        if (volume.status_codigo === 'SHIPPED') return 'shipped';
        return 'pending';
    }
    
    getStatusTexto(dados) {
        if (!dados.volumes || dados.volumes.length === 0) return 'Pendente';
        
        const volume = dados.volumes[0];
        if (volume.entregue) return 'Entregue';
        if (volume.status_codigo === 'SHIPPED') return 'Em trânsito';
        return volume.status || 'Pendente';
    }
    
    getEventIcon(statusCodigo) {
        const icons = {
            'SHIPPED': 'shipping-fast',
            'DELIVERED': 'check-circle',
            'NEW': 'plus-circle',
            'CREATED': 'plus-circle',
            'IN_TRANSIT': 'truck',
            'OUT_FOR_DELIVERY': 'truck-loading',
            'FAILED': 'exclamation-circle',
            'RETURNED': 'undo'
        };
        return icons[statusCodigo] || 'info-circle';
    }
    
    showLoading() {
        const loadingDiv = document.getElementById('intelipost-loading');
        if (loadingDiv) loadingDiv.style.display = 'block';
    }
    
    hideLoading() {
        const loadingDiv = document.getElementById('intelipost-loading');
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
    
    showError(message) {
        const errorDiv = document.getElementById('intelipost-error');
        if (errorDiv) {
            errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
            errorDiv.style.display = 'block';
            
            // Auto-esconde após 5 segundos
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    }
    
    showSearchForm() {
        const resultadoDiv = document.getElementById('intelipost-result');
        resultadoDiv.style.display = 'none';
        
        const searchInput = document.getElementById('intelipost-order-number');
        if (searchInput) {
            searchInput.value = '';
            searchInput.focus();
        }
    }
    
    registrarConsultaLocal(orderNumber) {
        try {
            let historico = JSON.parse(localStorage.getItem('intelipost_historico') || '[]');
            
            // Adiciona nova consulta no início
            historico.unshift({
                numero_pedido: orderNumber,
                data: new Date().toISOString()
            });
            
            // Mantém apenas as últimas 20 consultas
            historico = historico.slice(0, 20);
            
            localStorage.setItem('intelipost_historico', JSON.stringify(historico));
        } catch (error) {
            console.error('Erro ao salvar histórico local:', error);
        }
    }
    
    obterHistoricoLocal() {
        try {
            return JSON.parse(localStorage.getItem('intelipost_historico') || '[]');
        } catch (error) {
            return [];
        }
    }
}

// Inicializa quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.intelipostTracker = new IntelipostTracker();
});