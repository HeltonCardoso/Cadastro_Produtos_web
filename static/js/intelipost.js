/**
 * JavaScript para módulo Intelipost - VERSÃO COMPLETA
 * Cache Buster: ${Date.now()}
 */
class IntelipostTracker {
    constructor() {
        this.baseUrl = '/intelipost';
        console.log('🚀 IntelipostTracker inicializado');
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkAutoSearch();
    }
    
    bindEvents() {
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
        
        // Event delegation para novos botões
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-nova-consulta')) {
                this.showSearchForm();
            }
        });
    }
    
    checkAutoSearch() {
        const urlParams = new URLSearchParams(window.location.search);
        const pedidoParam = urlParams.get('pedido');
        
        if (pedidoParam && pedidoParam.trim()) {
            const searchInput = document.getElementById('intelipost-order-number');
            if (searchInput) {
                searchInput.value = pedidoParam;
                // Busca automática após 500ms
                setTimeout(() => this.buscarRastreio(), 500);
            }
        }
    }
    
    async buscarRastreio() {
        const orderNumber = document.getElementById('intelipost-order-number').value.trim();
        
        if (!orderNumber) {
            this.showError('❌ Digite um número de pedido válido');
            return;
        }
        
        console.log(`🔍 Buscando pedido: ${orderNumber}`);
        
        // Mostrar loading
        this.showLoading();
        this.hideResult();
        this.hideError();
        
        try {
            // Tenta a nova rota primeiro
            const response = await fetch(`${this.baseUrl}/api/rastreio/${encodeURIComponent(orderNumber)}`);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log('📊 Resposta da API:', data);
            
            if (data.sucesso) {
                this.mostrarResultadoCompleto(data.dados);
                this.registrarConsultaLocal(orderNumber);
            } else {
                this.showError(`❌ ${data.erro || 'Erro desconhecido'}`);
            }
        } catch (error) {
            console.error('💥 Erro:', error);
            this.showError('🔌 Erro de conexão com o servidor');
        } finally {
            this.hideLoading();
        }
    }
    
    mostrarResultadoCompleto(dados) {
        console.log('🎨 Renderizando resultado completo:', dados);
        
        const resultadoDiv = document.getElementById('intelipost-result');
        if (!resultadoDiv) {
            console.error('❌ Elemento #intelipost-result não encontrado');
            return;
        }
        
        let html = `
            <div class="card mt-3 border-primary shadow-lg">
                <div class="card-header bg-primary text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h4 class="mb-0">
                                <i class="fas fa-shipping-fast"></i> Pedido Intelipost
                            </h4>
                            <small class="opacity-75">${dados.pedido.plataforma || 'Plataforma não informada'}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-light text-dark fs-5">
                                ${dados.pedido.numero || 'N/D'}
                            </span>
                            <div class="mt-1">
                                <small class="opacity-75">ID: ${dados.pedido.id || 'N/D'}</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card-body">
                    <!-- Status Principal -->
                    <div class="alert ${dados.volumes?.[0]?.entregue ? 'alert-success' : 'alert-primary'} mb-4">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h5 class="mb-1">
                                    <i class="fas fa-truck me-2"></i> Status da Entrega
                                </h5>
                                <div class="d-flex align-items-center">
                                    <span class="badge ${dados.volumes?.[0]?.entregue ? 'bg-success' : 'bg-primary'} me-2 fs-6">
                                        ${dados.volumes?.[0]?.status || 'Status não disponível'}
                                    </span>
                                    <span>
                                        ${dados.volumes?.[0]?.entregue ? 
                                            '✅ Entregue com sucesso' : 
                                            '📦 Em andamento'}
                                    </span>
                                </div>
                            </div>
                            ${dados.pedido.url_rastreio ? `
                            <div>
                                <a href="${dados.pedido.url_rastreio}" 
                                   target="_blank" 
                                   class="btn btn-lg btn-outline-primary">
                                    <i class="fas fa-external-link-alt"></i> Rastrear
                                </a>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <!-- Grid de Informações -->
                    <div class="row g-3">
                        <!-- Informações do Pedido -->
                        <div class="col-md-6">
                            <div class="card h-100 border">
                                <div class="card-header bg-light">
                                    <h6 class="mb-0"><i class="fas fa-receipt me-2"></i>Informações do Pedido</h6>
                                </div>
                                <div class="card-body">
                                    <table class="table table-sm">
                                        <tbody>
                                            <tr>
                                                <td width="45%"><strong>Número Intelipost:</strong></td>
                                                <td><code class="fs-6">${dados.pedido.numero || 'N/D'}</code></td>
                                            </tr>
                                            <tr>
                                                <td><strong>Número de Vendas:</strong></td>
                                                <td>${dados.pedido.numero_vendas || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Transportadora:</strong></td>
                                                <td>
                                                    <span class="badge bg-info fs-6">${dados.pedido.transportadora || 'N/D'}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td><strong>Método de Entrega:</strong></td>
                                                <td>${dados.pedido.metodo_entrega || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Criado em:</strong></td>
                                                <td>${dados.pedido.data_criacao || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Enviado em:</strong></td>
                                                <td>${dados.pedido.data_envio || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Previsão de Entrega:</strong></td>
                                                <td>${dados.pedido.previsao_entrega || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Custo do Frete:</strong></td>
                                                <td class="fw-bold text-success fs-5">${dados.pedido.custo_frete || 'N/D'}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Informações do Cliente -->
                        <div class="col-md-6">
                            <div class="card h-100 border">
                                <div class="card-header bg-light">
                                    <h6 class="mb-0"><i class="fas fa-user me-2"></i>Destinatário</h6>
                                </div>
                                <div class="card-body">
                                    <table class="table table-sm">
                                        <tbody>
                                            <tr>
                                                <td width="45%"><strong>Nome:</strong></td>
                                                <td><strong>${dados.cliente.nome || 'N/D'}</strong></td>
                                            </tr>
                                            <tr>
                                                <td><strong>Endereço:</strong></td>
                                                <td>
                                                    ${dados.cliente.endereco || 'N/D'}
                                                    ${dados.cliente.complemento ? `<br><small>${dados.cliente.complemento}</small>` : ''}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td><strong>Cidade/UF:</strong></td>
                                                <td>
                                                    ${dados.cliente.cidade || 'N/D'} - ${dados.cliente.estado || 'N/D'}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td><strong>CEP:</strong></td>
                                                <td><code>${dados.cliente.cep || 'N/D'}</code></td>
                                            </tr>
                                            <tr>
                                                <td><strong>Contato:</strong></td>
                                                <td>
                                                    ${dados.cliente.telefone ? `<i class="fas fa-phone"></i> ${dados.cliente.telefone}<br>` : ''}
                                                    ${dados.cliente.celular ? `<i class="fas fa-mobile-alt"></i> ${dados.cliente.celular}<br>` : ''}
                                                    ${dados.cliente.email ? `<i class="fas fa-envelope"></i> ${dados.cliente.email}` : ''}
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
        `;
        
        // Adicionar Volumes se existirem
        if (dados.volumes && dados.volumes.length > 0) {
            html += `
                <div class="mt-4">
                    <h5 class="border-bottom pb-2">
                        <i class="fas fa-cubes me-2"></i>Volumes (${dados.volumes.length})
                    </h5>
                    
                    ${dados.volumes.map((volume, index) => `
                    <div class="card mt-3 border-secondary">
                        <div class="card-header bg-light">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">
                                        <i class="fas fa-box me-2"></i>Volume ${index + 1}
                                        <span class="badge bg-dark ms-2">${volume.numero}</span>
                                    </h6>
                                    <small class="text-muted">
                                        ${volume.codigo_rastreio ? `Rastreio: ${volume.codigo_rastreio}` : ''}
                                    </small>
                                </div>
                                <div>
                                    <span class="badge ${volume.entregue ? 'bg-success' : 'bg-warning'} fs-6">
                                        ${volume.status || 'N/D'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-info-circle me-2"></i>Informações</h6>
                                    <table class="table table-sm">
                                        <tbody>
                                            <tr>
                                                <td><strong>Peso:</strong></td>
                                                <td>${volume.peso_str || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Dimensões:</strong></td>
                                                <td>${volume.dimensoes_str || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Tipo:</strong></td>
                                                <td>${volume.tipo_volume || 'N/D'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Entregue:</strong></td>
                                                <td>
                                                    ${volume.entregue ? 
                                                        '<span class="badge bg-success">Sim</span>' : 
                                                        '<span class="badge bg-warning">Não</span>'}
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                
                                <div class="col-md-6">
                                    ${volume.produtos && volume.produtos.length > 0 ? `
                                    <h6><i class="fas fa-shopping-cart me-2"></i>Produtos (${volume.produtos.length})</h6>
                                    <div class="table-responsive">
                                        <table class="table table-sm table-hover">
                                            <thead>
                                                <tr>
                                                    <th>Produto</th>
                                                    <th>Qtd</th>
                                                    <th>Preço</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${volume.produtos.map(produto => `
                                                <tr>
                                                    <td>
                                                        <strong>${produto.descricao || 'N/D'}</strong>
                                                        ${produto.sku ? `<br><small class="text-muted">SKU: ${produto.sku}</small>` : ''}
                                                    </td>
                                                    <td class="text-center">
                                                        <span class="badge bg-primary">${produto.quantidade || 1}</span>
                                                    </td>
                                                    <td class="fw-bold">
                                                        ${produto.preco || 'N/D'}
                                                    </td>
                                                </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                    ` : '<p class="text-muted">Nenhum produto listado</p>'}
                                </div>
                            </div>
                            
                            ${volume.historico && volume.historico.length > 0 ? `
                            <div class="mt-4">
                                <h6><i class="fas fa-history me-2"></i>Histórico (${volume.historico.length} eventos)</h6>
                                <div class="timeline mt-3">
                                    ${volume.historico.slice(0, 5).map((evento, idx) => `
                                    <div class="timeline-item ${idx === 0 ? 'current' : ''} mb-3">
                                        <div class="d-flex">
                                            <div class="timeline-marker ${idx === 0 ? 'bg-primary' : 'bg-secondary'}"></div>
                                            <div class="timeline-content ms-3">
                                                <div class="d-flex justify-content-between">
                                                    <strong>${evento.status || 'N/D'}</strong>
                                                    <small class="text-muted">${evento.data || ''}</small>
                                                </div>
                                                ${evento.descricao ? `
                                                <p class="mb-0 mt-1 small">${evento.descricao}</p>
                                                ` : ''}
                                            </div>
                                        </div>
                                    </div>
                                    `).join('')}
                                    
                                    ${volume.historico.length > 5 ? `
                                    <div class="text-center mt-2">
                                        <small class="text-muted">
                                            + ${volume.historico.length - 5} eventos anteriores
                                        </small>
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Botões de ação
        html += `
                    <div class="mt-4 text-center">
                        <div class="btn-group" role="group">
                            <button onclick="window.print()" class="btn btn-outline-secondary">
                                <i class="fas fa-print"></i> Imprimir
                            </button>
                            <button class="btn btn-outline-primary btn-nova-consulta">
                                <i class="fas fa-search"></i> Nova Consulta
                            </button>
                            <button onclick="location.reload()" class="btn btn-outline-success">
                                <i class="fas fa-redo"></i> Recarregar
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="card-footer bg-light text-muted">
                    <div class="d-flex justify-content-between small">
                        <div>
                            <i class="fas fa-clock"></i> ${dados.metadata?.tempo_resposta || 'Tempo não disponível'}
                        </div>
                        <div>
                            <i class="fas fa-check-circle text-success"></i> Consulta realizada com sucesso
                        </div>
                        <div>
                            <i class="fas fa-calendar"></i> ${new Date().toLocaleString()}
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .timeline {
                position: relative;
                padding-left: 30px;
            }
            .timeline::before {
                content: '';
                position: absolute;
                left: 9px;
                top: 0;
                bottom: 0;
                width: 2px;
                background: #dee2e6;
            }
            .timeline-item {
                position: relative;
                margin-bottom: 20px;
            }
            .timeline-marker {
                position: absolute;
                left: -30px;
                top: 5px;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                border: 3px solid white;
                z-index: 1;
            }
            .timeline-item.current .timeline-marker {
                background: #0d6efd;
                box-shadow: 0 0 0 4px rgba(13, 110, 253, 0.2);
            }
            .timeline-item:not(.current) .timeline-marker {
                background: #6c757d;
            }
            .timeline-content {
                padding-left: 15px;
                border-left: 2px solid #dee2e6;
            }
            .timeline-item:last-child .timeline-content {
                border-left: none;
            }
            .card {
                border-radius: 10px;
                overflow: hidden;
            }
            .card-header {
                border-bottom: 2px solid rgba(0,0,0,0.1);
            }
            .table-sm td, .table-sm th {
                padding: 0.5rem;
            }
            </style>
        `;
        
        resultadoDiv.innerHTML = html;
        resultadoDiv.style.display = 'block';
        
        // Scroll suave para o resultado
        resultadoDiv.scrollIntoView({ behavior: 'smooth' });
    }
    
    showLoading() {
        const loadingDiv = document.getElementById('intelipost-loading');
        if (loadingDiv) {
            loadingDiv.style.display = 'block';
            loadingDiv.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="mt-3 fs-5">Buscando informações de rastreio...</p>
                    <div class="progress mt-2" style="height: 5px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                    </div>
                </div>
            `;
        }
    }
    
    hideLoading() {
        const loadingDiv = document.getElementById('intelipost-loading');
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
    
    showError(message) {
        const errorDiv = document.getElementById('intelipost-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            errorDiv.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        }
    }
    
    hideError() {
        const errorDiv = document.getElementById('intelipost-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
            errorDiv.innerHTML = '';
        }
    }
    
    hideResult() {
        const resultadoDiv = document.getElementById('intelipost-result');
        if (resultadoDiv) resultadoDiv.style.display = 'none';
    }
    
    showSearchForm() {
        const resultadoDiv = document.getElementById('intelipost-result');
        const searchInput = document.getElementById('intelipost-order-number');
        
        if (resultadoDiv) resultadoDiv.style.display = 'none';
        if (searchInput) {
            searchInput.value = '';
            searchInput.focus();
        }
        
        this.hideError();
    }
    
    registrarConsultaLocal(orderNumber) {
        try {
            let historico = JSON.parse(localStorage.getItem('intelipost_historico') || '[]');
            historico.unshift({
                numero_pedido: orderNumber,
                data: new Date().toISOString(),
                timestamp: Date.now()
            });
            historico = historico.slice(0, 20);
            localStorage.setItem('intelipost_historico', JSON.stringify(historico));
        } catch (error) {
            console.error('Erro ao salvar histórico local:', error);
        }
    }
}

// Inicializa quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('📦 Módulo Intelipost carregado');
    window.intelipostTracker = new IntelipostTracker();
    
    // Força recarregamento do JavaScript se detectar cache antigo
    if (window.performance && window.performance.navigation) {
        if (window.performance.navigation.type === 1) {
            console.log('🔄 Página carregada via refresh');
            // Força recarregamento de recursos
            const scripts = document.querySelectorAll('script[src*="intelipost"]');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.src = script.src + '?v=' + Date.now();
                document.head.appendChild(newScript);
            });
        }
    }
});