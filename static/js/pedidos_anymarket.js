// pedidos_anymarket.js - Versão corrigida e robusta

let allOrders = [];
let currentPage = 1;
const ordersPerPage = 20;

// Funções principais
async function carregarPedidos(page = 1) {
    const token = document.getElementById('tokenInput').value.trim();
    if (!token) {
        mostrarErro('Por favor, digite seu GumgaToken');
        return;
    }

    currentPage = page;
    mostrarLoading(true);
    limparMensagens();

    try {
        const params = new URLSearchParams({
            page: page,
            limit: ordersPerPage
        });

        // Adicionar filtros
        const statusFilter = document.getElementById('statusFilter').value;
        const marketplaceFilter = document.getElementById('marketplaceFilter').value;
        const dataInicio = document.getElementById('dataInicio').value;
        const dataFim = document.getElementById('dataFim').value;

        if (statusFilter) params.append('status', statusFilter);
        if (marketplaceFilter) params.append('marketplace', marketplaceFilter);
        if (dataInicio) params.append('dataInicio', dataInicio);
        if (dataFim) params.append('dataFim', dataFim);

        console.log('Buscando pedidos com parâmetros:', params.toString());

        const response = await fetch(`/api/anymarket/pedidos?${params}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log('Resposta da API:', data);
        
        if (data.success) {
            allOrders = Array.isArray(data.orders) ? data.orders : [];
            console.log(`${allOrders.length} pedidos recebidos`);
            exibirPedidos(allOrders);
            atualizarEstatisticas(data.stats);
            atualizarPaginacao(data.pagination);
            mostrarInfo(`${allOrders.length} pedidos carregados com sucesso!`);
        } else {
            throw new Error(data.error || 'Erro ao carregar pedidos');
        }

    } catch (error) {
        console.error('Erro ao carregar pedidos:', error);
        mostrarErro(`Erro ao carregar pedidos: ${error.message}`);
    } finally {
        mostrarLoading(false);
    }
}

function exibirPedidos(orders) {
    const container = document.getElementById('ordersContainer');
    const tableBody = document.getElementById('ordersTableBody');
    const emptyState = document.getElementById('emptyState');

    if (!Array.isArray(orders) || orders.length === 0) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    container.classList.remove('hidden');
    emptyState.classList.add('hidden');

    tableBody.innerHTML = orders.map(order => {
        // Garantir que os dados existam
        const orderId = safeToString(order.id);
        const marketplace = safeToString(order.marketPlace);
        const status = safeToString(order.status);
        const marketplaceNumber = safeToString(order.marketPlaceNumber);
        const buyerName = safeToString(order.buyer?.name);
        const buyerEmail = safeToString(order.buyer?.email);
        const createdAt = safeToString(order.createdAt);
        const itemsCount = Array.isArray(order.items) ? order.items.length : 0;
        const totalAmount = parseFloat(order.totalAmount || 0);

        return `
            <tr onclick="abrirDetalhesPedido('${orderId}')" style="cursor: pointer;">
                <td>
                    <div style="font-family: 'Courier New', monospace; font-size: 12px;" title="${orderId}">
                        ${truncateText(orderId, 10)}
                    </div>
                </td>
                <td>
                    <span class="marketplace-badge">${formatMarketplace(marketplace)}</span>
                </td>
                <td>
                    <span class="status-badge status-${status}">${formatStatus(status)}</span>
                </td>
                <td>${marketplaceNumber}</td>
                <td>
                    <div style="max-width: 150px;">
                        <div style="font-weight: 500;">${buyerName}</div>
                        <div style="font-size: 11px; color: #6c757d;">${buyerEmail}</div>
                    </div>
                </td>
                <td>${formatDate(createdAt)}</td>
                <td>
                    <div style="text-align: center;">
                        <span style="background: #e9ecef; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                            ${itemsCount}
                        </span>
                    </div>
                </td>
                <td style="font-weight: 600; color: #198754;">R$ ${formatCurrency(totalAmount)}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); abrirDetalhesPedido('${orderId}')">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    console.log('Pedidos exibidos na tabela');
}

function abrirDetalhesPedido(orderId) {
    console.log('Abrindo detalhes do pedido:', orderId);
    
    const order = allOrders.find(o => safeToString(o.id) === orderId);
    
    if (!order) {
        console.error('Pedido não encontrado:', orderId);
        mostrarErro('Pedido não encontrado');
        return;
    }

    const modalContent = document.getElementById('modalContent');
    
    // Garantir que os dados existam
    const safeOrder = {
        id: safeToString(order.id),
        marketPlace: safeToString(order.marketPlace),
        marketPlaceNumber: safeToString(order.marketPlaceNumber),
        status: safeToString(order.status),
        createdAt: safeToString(order.createdAt),
        updatedAt: safeToString(order.updatedAt),
        totalAmount: parseFloat(order.totalAmount || 0),
        buyer: {
            name: safeToString(order.buyer?.name),
            email: safeToString(order.buyer?.email),
            document: safeToString(order.buyer?.document),
            phone: safeToString(order.buyer?.phone)
        },
        shipping: order.shipping ? {
            carrier: safeToString(order.shipping.carrier),
            cost: parseFloat(order.shipping.cost || 0),
            address: order.shipping.address ? {
                street: safeToString(order.shipping.address.street),
                number: safeToString(order.shipping.address.number),
                complement: safeToString(order.shipping.address.complement),
                neighborhood: safeToString(order.shipping.address.neighborhood),
                city: safeToString(order.shipping.address.city),
                state: safeToString(order.shipping.address.state),
                zipCode: safeToString(order.shipping.address.zipCode)
            } : null
        } : null,
        items: Array.isArray(order.items) ? order.items.map(item => ({
            title: safeToString(item.title),
            sku: safeToString(item.sku),
            quantity: parseInt(item.quantity || 0),
            price: parseFloat(item.price || 0)
        })) : [],
        // Novos campos adicionados
        payment: order.payment ? {
            method: safeToString(order.payment.method),
            status: safeToString(order.payment.status),
            installments: parseInt(order.payment.installments || 1)
        } : null,
        notes: safeToString(order.notes)
    };

    modalContent.innerHTML = `
        <div class="modal-header">
            <h2><i class="fas fa-receipt me-2"></i>Pedido #${safeOrder.id}</h2>
            <button class="close-modal" onclick="fecharModal()">×</button>
        </div>
        <div class="modal-body">
            <div class="detail-grid">
                <!-- Informações Gerais -->
                <div class="detail-card">
                    <h3><i class="fas fa-info-circle"></i> Informações Gerais</h3>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-store"></i> Marketplace</span>
                        <span class="detail-value">${formatMarketplace(safeOrder.marketPlace)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-hashtag"></i> Nº Marketplace</span>
                        <span class="detail-value">${safeOrder.marketPlaceNumber}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-tag"></i> Status</span>
                        <span class="detail-value status-badge status-${safeOrder.status}">${formatStatus(safeOrder.status)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-calendar-plus"></i> Data Criação</span>
                        <span class="detail-value">${formatDateTime(safeOrder.createdAt)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-calendar-check"></i> Última Atualização</span>
                        <span class="detail-value">${safeOrder.updatedAt ? formatDateTime(safeOrder.updatedAt) : 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-money-bill-wave"></i> Valor Total</span>
                        <span class="detail-value" style="font-weight: 600; color: #198754; font-size: 16px;">R$ ${formatCurrency(safeOrder.totalAmount)}</span>
                    </div>
                </div>

                <!-- Dados do Comprador -->
                <div class="detail-card">
                    <h3><i class="fas fa-user"></i> Dados do Comprador</h3>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-user-circle"></i> Nome</span>
                        <span class="detail-value">${safeOrder.buyer.name}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-envelope"></i> Email</span>
                        <span class="detail-value">${safeOrder.buyer.email}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-id-card"></i> Documento</span>
                        <span class="detail-value">${formatDocument(safeOrder.buyer.document)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-phone"></i> Telefone</span>
                        <span class="detail-value">${formatPhone(safeOrder.buyer.phone)}</span>
                    </div>
                </div>

                <!-- Informações de Pagamento -->
                ${safeOrder.payment ? `
                <div class="detail-card">
                    <h3><i class="fas fa-credit-card"></i> Pagamento</h3>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-wallet"></i> Método</span>
                        <span class="detail-value">${formatPaymentMethod(safeOrder.payment.method)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-check-circle"></i> Status</span>
                        <span class="detail-value">${formatPaymentStatus(safeOrder.payment.status)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-calendar-alt"></i> Parcelas</span>
                        <span class="detail-value">${safeOrder.payment.installments}x</span>
                    </div>
                </div>
                ` : ''}
            </div>

            <!-- Entrega -->
            ${safeOrder.shipping ? `
            <div class="detail-card">
                <h3><i class="fas fa-truck"></i> Entrega</h3>
                <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-shipping-fast"></i> Transportadora</span>
                    <span class="detail-value">${safeOrder.shipping.carrier}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-dollar-sign"></i> Valor do Frete</span>
                    <span class="detail-value">R$ ${formatCurrency(safeOrder.shipping.cost)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-map-marker-alt"></i> Endereço</span>
                    <span class="detail-value">${formatEndereco(safeOrder.shipping.address)}</span>
                </div>
            </div>
            ` : ''}

            <!-- Observações -->
            ${safeOrder.notes && safeOrder.notes !== 'N/A' ? `
            <div class="detail-card">
                <h3><i class="fas fa-sticky-note"></i> Observações</h3>
                <div class="detail-item">
                    <span class="detail-value" style="background: white; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
                        ${safeOrder.notes}
                    </span>
                </div>
            </div>
            ` : ''}

            <!-- Itens do Pedido -->
            <div class="items-section">
                <h3><i class="fas fa-boxes"></i> Itens do Pedido (${safeOrder.items.length})</h3>
                ${safeOrder.items.length > 0 ? 
                    safeOrder.items.map((item, index) => {
                        const subtotal = item.quantity * item.price;
                        return `
                        <div class="item-card">
                            <div class="item-info">
                                <div class="item-title">
                                    <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 8px;">${index + 1}</span>
                                    ${item.title}
                                </div>
                                <div class="item-sku">SKU: ${item.sku}</div>
                                <div class="item-details">
                                    <div>
                                        <strong>Quantidade</strong>
                                        <span>${item.quantity} un.</span>
                                    </div>
                                    <div>
                                        <strong>Preço unitário</strong>
                                        <span>R$ ${formatCurrency(item.price)}</span>
                                    </div>
                                    <div>
                                        <strong>Subtotal</strong>
                                        <span style="font-weight: 600;">R$ ${formatCurrency(subtotal)}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="item-price">
                                R$ ${formatCurrency(subtotal)}
                            </div>
                        </div>
                        `;
                    }).join('') : 
                    '<div class="empty-state" style="padding: 40px; margin: 0;">' +
                    '<i class="fas fa-inbox"></i>' +
                    '<p>Nenhum item encontrado neste pedido</p>' +
                    '</div>'
                }
            </div>
        </div>
    `;

    document.getElementById('orderModal').style.display = 'block';
}

// Adicione estas funções de formatação adicionais
function formatDocument(doc) {
    const safeDoc = safeToString(doc);
    if (safeDoc === 'N/A') return 'N/A';
    
    // CPF: 000.000.000-00
    if (safeDoc.length === 11) {
        return safeDoc.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    // CNPJ: 00.000.000/0000-00
    if (safeDoc.length === 14) {
        return safeDoc.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    return safeDoc;
}

function formatPhone(phone) {
    const safePhone = safeToString(phone);
    if (safePhone === 'N/A') return 'N/A';
    
    // Remove caracteres não numéricos
    const cleaned = safePhone.replace(/\D/g, '');
    
    // Formata como (00) 00000-0000
    if (cleaned.length === 11) {
        return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    }
    // Formata como (00) 0000-0000
    if (cleaned.length === 10) {
        return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
    return safePhone;
}

function formatPaymentMethod(method) {
    const safeMethod = safeToString(method);
    const methods = {
        'CREDIT_CARD': 'Cartão de Crédito',
        'BOLETO': 'Boleto Bancário',
        'PIX': 'PIX',
        'DEBIT_CARD': 'Cartão de Débito'
    };
    return methods[safeMethod] || safeMethod;
}

function formatPaymentStatus(status) {
    const safeStatus = safeToString(status);
    const statusMap = {
        'APPROVED': 'Aprovado',
        'PENDING': 'Pendente',
        'DECLINED': 'Recusado',
        'CANCELED': 'Cancelado'
    };
    return statusMap[safeStatus] || safeStatus;
}

function fecharModal() {
    document.getElementById('orderModal').style.display = 'none';
}

// Funções de utilidade - ROBUSTAS
function safeToString(value) {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value.toString();
    return String(value);
}

function truncateText(text, maxLength) {
    const safeText = safeToString(text);
    return safeText.length > maxLength ? safeText.substring(0, maxLength) + '...' : safeText;
}

function formatMarketplace(marketplace) {
    const safeMarketplace = safeToString(marketplace);
    const marketplaces = {
        'MERCADOLIVRE': 'Mercado Livre', 
        'SHOPEE': 'Shopee', 
        'AMAZON': 'Amazon',
        'NUVEMSHOP': 'Nuvem Shop', 
        'VTEX': 'VTEX', 
        'TRAY': 'Tray',
        'MERCADOPAGO': 'Mercado Pago'
    };
    return marketplaces[safeMarketplace] || safeMarketplace;
}

function formatStatus(status) {
    const safeStatus = safeToString(status);
    const statusMap = {
        'PENDING': 'Pendente', 
        'PAID_WAITING_SHIP': 'Pago - Aguardando Envio',
        'INVOICED': 'Faturado', 
        'SHIPPED': 'Enviado',
        'DELIVERED': 'Entregue',
        'CONCLUDED': 'Concluído', 
        'CANCELED': 'Cancelado'
    };
    return statusMap[safeStatus] || safeStatus;
}

function formatDate(dateString) {
    try {
        const safeDate = safeToString(dateString);
        if (safeDate === 'N/A') return 'N/A';
        return new Date(safeDate).toLocaleDateString('pt-BR');
    } catch {
        return 'Data inválida';
    }
}

function formatDateTime(dateString) {
    try {
        const safeDate = safeToString(dateString);
        if (safeDate === 'N/A') return 'N/A';
        return new Date(safeDate).toLocaleString('pt-BR');
    } catch {
        return 'Data/hora inválida';
    }
}

function formatCurrency(value) {
    try {
        const numValue = typeof value === 'number' ? value : parseFloat(value || 0);
        return numValue.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } catch {
        return '0,00';
    }
}

function formatEndereco(address) {
    if (!address) return 'N/A';
    const parts = [
        address.street,
        address.number,
        address.complement,
        address.neighborhood,
        `${address.city || ''}${address.state ? '/' + address.state : ''}`,
        address.zipCode
    ].filter(part => part && safeToString(part).trim() !== 'N/A' && safeToString(part).trim() !== '');
    return parts.join(', ') || 'N/A';
}

function limparTela() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('marketplaceFilter').value = '';
    document.getElementById('dataInicio').value = '';
    document.getElementById('dataFim').value = '';
    
    document.getElementById('ordersContainer').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');
    document.getElementById('stats').classList.add('hidden');
    
    limparMensagens();
    allOrders = [];
}

function atualizarEstatisticas(stats) {
    const statsElement = document.getElementById('stats');
    if (statsElement && stats) {
        statsElement.innerHTML = `
            <i class="fas fa-chart-bar"></i>
            <strong>Estatísticas:</strong> 
            ${stats.total || 0} pedidos • 
            ${stats.pendentes || 0} pendentes • 
            R$ ${formatCurrency(stats.valorTotal || 0)} total
        `;
        statsElement.classList.remove('hidden');
    }
}

function atualizarPaginacao(pagination) {
    const paginationElement = document.querySelector('.pagination');
    if (!paginationElement) return;

    const { currentPage, totalPages, hasNext, hasPrev } = pagination;
    
    paginationElement.innerHTML = `
        <button class="page-btn" ${!hasPrev ? 'disabled' : ''} onclick="carregarPedidos(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i> Anterior
        </button>
        <span class="page-info">Página ${currentPage} de ${totalPages}</span>
        <button class="page-btn" ${!hasNext ? 'disabled' : ''} onclick="carregarPedidos(${currentPage + 1})">
            Próxima <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

function mostrarLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.toggle('hidden', !show);
        if (show) {
            loading.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-2">Buscando pedidos...</p>
            `;
        }
    }
}

function mostrarErro(mensagem) {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${mensagem}`;
        errorElement.className = 'alert alert-error';
        errorElement.classList.remove('hidden');
    }
}

function mostrarInfo(mensagem) {
    const infoElement = document.getElementById('infoMessage');
    if (infoElement) {
        infoElement.innerHTML = `<i class="fas fa-check-circle"></i> ${mensagem}`;
        infoElement.className = 'alert alert-success';
        infoElement.classList.remove('hidden');
        setTimeout(() => infoElement.classList.add('hidden'), 3000);
    }
}

function limparMensagens() {
    ['errorMessage', 'infoMessage'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.classList.add('hidden');
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema de pedidos AnyMarket inicializado');
    
    window.addEventListener('click', function(event) {
        if (event.target === document.getElementById('orderModal')) {
            fecharModal();
        }
    });
    
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') fecharModal();
    });

    // Debug: verificar estrutura dos dados
    window.debugOrders = function() {
        console.log('Todos os pedidos:', allOrders);
        if (allOrders.length > 0) {
            console.log('Primeiro pedido:', allOrders[0]);
            console.log('Tipo do ID:', typeof allOrders[0].id);
            console.log('ID value:', allOrders[0].id);
        }
    };
});