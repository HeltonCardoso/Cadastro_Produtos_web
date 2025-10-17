// Funções de interface do usuário
function ordenarPedidos() {
    const sortValue = document.getElementById('sortSelect').value;
    const [campo, direcao] = sortValue.split('_');
    
    window.pedidosData.sort((a, b) => {
        let valorA = a[campo];
        let valorB = b[campo];
        
        if (campo === 'createdAt') {
            valorA = new Date(valorA);
            valorB = new Date(valorB);
        }
        
        if (valorA < valorB) return direcao === 'asc' ? -1 : 1;
        if (valorA > valorB) return direcao === 'asc' ? 1 : -1;
        return 0;
    });
    
    renderizarListaPedidos();
}

function renderizarListaPedidos() {
    const ordersList = document.getElementById('ordersList');
    
    if (window.pedidosData.length === 0) {
        ordersList.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">Nenhum pedido encontrado</div>';
        return;
    }

    ordersList.innerHTML = window.pedidosData.map((pedido, index) => `
        <div class="order-card" onclick="abrirModalDetalhes(${index})">
            <div>${pedido.id}</div>
            <div>${MARKETPLACES[pedido.marketPlace] || pedido.marketPlace}</div>
            <div><span class="status-badge ${getStatusClass(pedido.status)}">${getStatusText(pedido.status)}</span></div>
            <div>${pedido.marketPlaceNumber || 'N/A'}</div>
            <div>${pedido.buyer?.name || 'N/A'}</div>
            <div>${formatarData(pedido.createdAt)}</div>
            <div>${pedido.items?.length || 0} itens</div>
            <div><strong>${formatarMoeda(pedido.total)}</strong></div>
            <div><button class="btn" onclick="event.stopPropagation(); abrirModalDetalhes(${index})">Ver</button></div>
        </div>
    `).join('');
}

function mostrarInterfacePedidos() {
    document.getElementById('ordersContainer').classList.remove('hidden');
    document.getElementById('emptyState').classList.add('hidden');
    
    // Criar ou atualizar controles de paginação
    let paginacaoDiv = document.getElementById('paginacao');
    if (!paginacaoDiv) {
        paginacaoDiv = document.createElement('div');
        paginacaoDiv.id = 'paginacao';
        paginacaoDiv.className = 'paginacao';
        document.getElementById('ordersContainer').appendChild(paginacaoDiv);
    }
    
    atualizarControlesPaginacao();
}

function mostrarEstadoVazio() {
    document.getElementById('ordersContainer').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');
    
    const paginacaoDiv = document.getElementById('paginacao');
    if (paginacaoDiv) {
        paginacaoDiv.innerHTML = '';
    }
}

// Nova função auxiliar para formatar data simples
function formatarDataSimples(dataString) {
    if (!dataString) return 'N/A';
    try {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR');
    } catch {
        return dataString;
    }
}

function atualizarEstatisticas(pedidos) {
    const total = pedidos.length;
    const valorTotal = pedidos.reduce((sum, p) => sum + (p.total || 0), 0);
    const valorMedio = total > 0 ? valorTotal / total : 0;
    
    // Agrupar por status
    const statusCount = {};
    pedidos.forEach(p => {
        statusCount[p.status] = (statusCount[p.status] || 0) + 1;
    });
    
    // Agrupar por marketplace
    const marketplaceCount = {};
    pedidos.forEach(p => {
        const mp = MARKETPLACES[p.marketPlace] || p.marketPlace;
        marketplaceCount[mp] = (marketplaceCount[mp] || 0) + 1;
    });

    document.getElementById('stats').innerHTML = `
        <div class="stat-card">
            <div class="stat-number">${total}</div>
            <div class="stat-label">Total de Pedidos</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${formatarMoeda(valorTotal)}</div>
            <div class="stat-label">Valor Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${formatarMoeda(valorMedio)}</div>
            <div class="stat-label">Ticket Médio</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${Object.keys(marketplaceCount).length}</div>
            <div class="stat-label">Marketplaces</div>
        </div>
    `;
  // document.getElementById('stats').classList.remove('hidden');
}

function criarModalDetalhes(pedido) {
    return `
        <h2>📦 Detalhes do Pedido - ${pedido.marketPlaceNumber || pedido.id}</h2>
        
        <div class="modal-section">
            <h3>📋 Informações Gerais</h3>
            <div class="modal-grid">
                <div class="info-item">
                    <span class="info-label">ID AnyMarket:</span>
                    <span class="info-value">${pedido.id}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Marketplace:</span>
                    <span class="info-value">${MARKETPLACES[pedido.marketPlace] || pedido.marketPlace}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Status:</span>
                    <span class="info-value"><span class="status-badge ${getStatusClass(pedido.status)}">${getStatusText(pedido.status)}</span></span>
                </div>
                <div class="info-item">
                    <span class="info-label">Nº Marketplace:</span>
                    <span class="info-value">${pedido.marketPlaceNumber || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Data Criação:</span>
                    <span class="info-value">${formatarData(pedido.createdAt)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Data Pagamento:</span>
                    <span class="info-value">${formatarData(pedido.paymentDate)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Subcanal:</span>
                    <span class="info-value">${pedido.subChannel || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Account Name:</span>
                    <span class="info-value">${pedido.accountName || 'N/A'}</span>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h3>👤 Dados do Comprador</h3>
            <div class="modal-grid">
                <div class="info-item">
                    <span class="info-label">Nome:</span>
                    <span class="info-value">${pedido.buyer?.name || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Email:</span>
                    <span class="info-value">${pedido.buyer?.email || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Documento:</span>
                    <span class="info-value">${pedido.buyer?.document || 'N/A'} (${pedido.buyer?.documentType || 'N/A'})</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Celular:</span>
                    <span class="info-value">${pedido.buyer?.cellPhone || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Telefone:</span>
                    <span class="info-value">${pedido.buyer?.phone || 'N/A'}</span>
                </div>
            </div>
        </div>

        ${pedido.shipping ? `
        <div class="modal-section">
            <h3>🚚 Endereço de Entrega</h3>
            <div class="modal-grid">
                <div class="info-item">
                    <span class="info-label">Nome:</span>
                    <span class="info-value">${pedido.shipping.receiverName || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Endereço:</span>
                    <span class="info-value">${pedido.shipping.street || ''}, ${pedido.shipping.number || ''}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Bairro:</span>
                    <span class="info-value">${pedido.shipping.neighborhood || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Cidade/Estado:</span>
                    <span class="info-value">${pedido.shipping.city || 'N/A'} - ${pedido.shipping.state || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">CEP:</span>
                    <span class="info-value">${pedido.shipping.zipCode || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">País:</span>
                    <span class="info-value">${pedido.shipping.country || 'Brasil'}</span>
                </div>
            </div>
        </div>
        ` : ''}

        <div class="modal-section">
            <h3>📦 Itens do Pedido (${pedido.items?.length || 0})</h3>
            ${(pedido.items || []).map(item => `
                <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #667eea;">
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                        <div>
                            <strong>${item.sku?.title || item.product?.title || 'Produto'}</strong><br>
                            <small>SKU: ${item.sku?.id || 'N/A'} | ID: ${item.product?.id || 'N/A'}</small>
                        </div>
                        <div>
                            <strong>Quantidade:</strong><br>
                            ${item.amount || 0}
                        </div>
                        <div>
                            <strong>Unitário:</strong><br>
                            ${formatarMoeda(item.unit)}
                        </div>
                        <div>
                            <strong>Total:</strong><br>
                            ${formatarMoeda(item.total)}
                        </div>
                    </div>
                    ${item.discount > 0 ? `<div><strong>Desconto:</strong> ${formatarMoeda(item.discount)}</div>` : ''}
                </div>
            `).join('')}
        </div>

        <div class="modal-section">
            <h3>💰 Resumo Financeiro</h3>
            <div class="modal-grid">
                <div class="info-item">
                    <span class="info-label">Valor Bruto:</span>
                    <span class="info-value">${formatarMoeda(pedido.gross)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Frete:</span>
                    <span class="info-value">${formatarMoeda(pedido.freight)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Desconto:</span>
                    <span class="info-value">${formatarMoeda(pedido.discount)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Juros:</span>
                    <span class="info-value">${formatarMoeda(pedido.interestValue)}</span>
                </div>
                <div class="info-item" style="border-top: 2px solid #667eea; font-size: 1.2rem;">
                    <span class="info-label"><strong>Total:</strong></span>
                    <span class="info-value" style="color: #667eea;"><strong>${formatarMoeda(pedido.total)}</strong></span>
                </div>
            </div>
        </div>

        ${pedido.payments && pedido.payments.length > 0 ? `
        <div class="modal-section">
            <h3>💳 Pagamentos</h3>
            ${pedido.payments.map(pagamento => `
                <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px;">
                        <div>
                            <strong>Método:</strong><br>
                            ${pagamento.method || 'N/A'}
                        </div>
                        <div>
                            <strong>Parcelas:</strong><br>
                            ${pagamento.installments || 1}x
                        </div>
                        <div>
                            <strong>Valor:</strong><br>
                            ${formatarMoeda(pagamento.value)}
                        </div>
                        <div>
                            <strong>Status:</strong><br>
                            ${pagamento.status || 'N/A'}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        ` : ''}
    `;
}

function abrirModalDetalhes(index) {
    const pedido = window.pedidosData[index];
    document.getElementById('modalContent').innerHTML = criarModalDetalhes(pedido);
    document.getElementById('orderModal').classList.add('show');
}

function fecharModal() {
    document.getElementById('orderModal').classList.remove('show');
}

function limparTela() {
    window.pedidosData = [];
    mostrarEstadoVazio();
    document.getElementById('stats').classList.add('hidden');
    limparMensagens();
    limparDebug();
}