// pedidos_anymarket.js - Versão SEGURA sem localStorage
// Sistema de gestão de pedidos AnyMarket - Token sempre manual

let currentToken = '';
let allOrders = [];
let currentPage = 1;
const ordersPerPage = 20;

// =============================================
// 🔐 INICIALIZAÇÃO INTELIGENTE
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔐 Sistema de pedidos AnyMarket inicializado');
    inicializarSistemaInteligente();
});

async function inicializarSistemaInteligente() {
    console.log('🔄 Verificando token seguro...');
    
    // ✅ PRIMEIRO: Tentar carregar token do backend seguro
    try {
        const tokenData = await carregarTokenSeguro();
        if (tokenData.success) {
            currentToken = tokenData.token;
            console.log('✅ Token carregado do backend seguro');
            
            // Preencher o input visualmente (apenas para feedback)
            const tokenInput = document.getElementById('tokenInput');
            if (tokenInput) {
                tokenInput.value = '••••••••••••••••'; // Apenas máscara
                tokenInput.placeholder = 'Token configurado (carregado automaticamente)';
            }
            
            // Configurar datas padrão
            configurarDatasPadrao();
            
            // ✅ Carregar pedidos automaticamente
            await carregarPedidos(1);
            return;
        }
    } catch (error) {
        console.log('ℹ️ Token não encontrado no backend:', error.message);
    }
    
    // ❌ SE NÃO ENCONTRAR TOKEN: Mostrar estado de configuração
    console.log('📝 Token não encontrado - Solicitar configuração');
    mostrarEstadoSemToken();
    configurarDatasPadrao();
}

async function carregarTokenSeguro() {
    try {
        const response = await fetch('/api/tokens/anymarket/obter');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.token) {
            return {
                success: true,
                token: data.token,
                source: 'backend'
            };
        } else {
            throw new Error(data.error || 'Token não encontrado');
        }
    } catch (error) {
        throw new Error(`Erro ao carregar token: ${error.message}`);
    }
}

function configurarDatasPadrao() {
    const dataFim = new Date().toISOString().split('T')[0];
    const dataInicio = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    document.getElementById('dataInicio').value = dataInicio;
    document.getElementById('dataFim').value = dataFim;
}

// =============================================
// 🔐 GERENCIAMENTO DE TOKEN - FLEXÍVEL
// =============================================

function validarEConfigurarToken() {
    const tokenInput = document.getElementById('tokenInput');
    if (!tokenInput) {
        showMessage('Campo de token não encontrado', 'error');
        return;
    }
    
    const token = tokenInput.value.trim();
    
    // Se o campo está mascarado, significa que já tem token configurado
    if (token === '••••••••••••••••') {
        showMessage('Token já está configurado e funcionando', 'info');
        return;
    }
    
    if (!token) {
        showMessage('Digite o token de acesso AnyMarket', 'error');
        tokenInput.focus();
        return;
    }
    
    if (token.length < 20) {
        showMessage('Token parece muito curto. Verifique se está completo.', 'warning');
        return;
    }
    
    // ✅ Configurar token manualmente
    configurarTokenManual(token);
}

async function configurarTokenManual(token) {
    console.log('🔑 Configurando token manualmente...');
    
    currentToken = token.trim();
    
    try {
        // ✅ Salvar token no backend seguro
        const response = await fetch('/api/tokens/anymarket/salvar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: currentToken
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ Token salvo com segurança! Carregando pedidos...', 'success');
            
            // Atualizar visual do input
            const tokenInput = document.getElementById('tokenInput');
            if (tokenInput) {
                tokenInput.value = '••••••••••••••••';
                tokenInput.placeholder = 'Token configurado e salvo com segurança';
            }
        } else {
            showMessage('⚠️ Token configurado, mas não foi salvo: ' + data.error, 'warning');
        }
    } catch (error) {
        showMessage('⚠️ Token configurado, mas erro ao salvar: ' + error.message, 'warning');
    }
    
    // Esconder estado vazio e carregar pedidos
    EmptyState();
    await carregarPedidos(1);
}

async function testarTokenAtual() {
    if (!currentToken) {
        showMessage('Nenhum token configurado para testar', 'error');
        return;
    }
    
    try {
        showMessage('🧪 Testando token...', 'info');
        
        const response = await fetch('/api/anymarket/testar-token', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ Token válido e funcionando!', 'success');
        } else {
            showMessage('❌ Token inválido: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('❌ Erro ao testar token: ' + error.message, 'error');
    }
}

function toggleTokenSection() {
    document.getElementById('tokenModal').style.display = 'block';
}

function fecharTokenModal() {
    document.getElementById('tokenModal').style.display = 'none';
}

async function limparToken() {
    try {
        // Remover do backend
        const response = await fetch('/api/tokens/anymarket/remover', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('🗑️ Token removido com segurança', 'success');
        }
    } catch (error) {
        console.log('Erro ao remover token:', error);
    }
    
    // Limpar frontend
    currentToken = '';
    const tokenInput = document.getElementById('tokenInput');
    if (tokenInput) {
        tokenInput.value = '';
        tokenInput.placeholder = 'Cole seu GumgaToken aqui...';
    }
    
    mostrarEstadoSemToken();
}

// =============================================
// 📦 FUNÇÕES PRINCIPAIS DE PEDIDOS
// =============================================

async function carregarPedidos(page = 1) {
    console.log(`📦 Carregando página ${page}...`);
    
    // ✅ VERIFICAÇÃO - token deve estar configurado
    if (!currentToken) {
        showMessage('Configure o token primeiro', 'error');
        mostrarEstadoSemToken();
        return;
    }
    
    showLoading(true);
    hideEmptyState();
    
    try {
        const params = new URLSearchParams({
            page: page,
            limit: 50,
            dataInicio: document.getElementById('dataInicio').value || '',
            dataFim: document.getElementById('dataFim').value || '',
            status: document.getElementById('statusFilter').value || '',
            marketplace: document.getElementById('marketplaceFilter').value || ''
        });

        const response = await fetch(`/api/anymarket/pedidos?${params}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            currentPage = page;
            exibirPedidos(data.orders);
            exibirEstatisticas(data.stats, data.filters);
            exibirPaginacao(data.pagination);
            
            if (page === 1) {
                showMessage(`✅ ${data.orders.length} pedidos carregados automaticamente`, 'success');
            }
        } else {
            throw new Error(data.error || 'Erro desconhecido na API');
        }
    } catch (error) {
        console.error('Erro ao carregar pedidos:', error);
        
        if (error.message.includes('401') || error.message.includes('Token')) {
            showMessage('❌ Token inválido ou expirado', 'error');
            // Não limpar automaticamente - deixar usuário decidir
        } else if (error.message.includes('Network') || error.message.includes('Failed to fetch')) {
            showMessage('🌐 Erro de conexão. Verifique sua internet.', 'error');
        } else {
            showMessage('❌ Erro: ' + error.message, 'error');
        }
        
        mostrarEstadoSemToken();
    } finally {
        showLoading(false);
    }
}

async function carregarTodosPedidos() {
    if (!currentToken) {
        showMessage('Configure o token primeiro', 'error');
        return;
    }

    showLoading(true);
    
    try {
        const params = new URLSearchParams({
            dataInicio: document.getElementById('dataInicio').value || '',
            dataFim: document.getElementById('dataFim').value || '',
            status: document.getElementById('statusFilter').value || '',
            marketplace: document.getElementById('marketplaceFilter').value || ''
        });

        const response = await fetch(`/api/anymarket/todos-pedidos?${params}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        const data = await response.json();

        if (data.success) {
            exibirPedidos(data.orders);
            exibirEstatisticas(data.stats, data.filters);
            
            document.querySelector('.pagination').innerHTML = '';
            showMessage(`✅ Todos os ${data.orders.length} pedidos carregados`, 'success');
        } else {
            throw new Error(data.error || 'Erro ao carregar todos os pedidos');
        }
    } catch (error) {
        showMessage('❌ Erro: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function buscarComFiltros() {
    if (!currentToken) {
        showMessage('Configure o token primeiro', 'error');
        return;
    }
    carregarPedidos(1);
}

// =============================================
// 🎯 EXIBIÇÃO DE DADOS (MANTIDO IGUAL)
// =============================================

function exibirPedidos(orders) {
    const tbody = document.getElementById('ordersTableBody');
    
    if (!orders || orders.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 15px; opacity: 0.5;"></i>
                    <br>
                    Nenhum pedido encontrado para os filtros selecionados
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = orders.map(order => `
        <tr onclick="abrirDetalhesPedido(${order.id})" style="cursor: pointer;">
            <td>
                <strong class="text-primary">${order.id}</strong>
                ${order.marketPlaceNumber ? `<br><small class="text-muted">MP: ${order.marketPlaceNumber}</small>` : ''}
            </td>
            <td>
                <span class="marketplace-badge">${formatMarketplace(order.marketPlace)}</span>
                ${order.officialStoreName ? `<br><small class="text-muted">${order.officialStoreName}</small>` : ''}
            </td>
            <td>
                <span class="status-badge status-${order.status}">${formatStatus(order.status)}</span>
                ${order.marketPlaceStatus ? `<br><small class="text-muted">MP: ${order.marketPlaceStatus}</small>` : ''}
            </td>
            <td>${order.marketPlaceNumber || '-'}</td>
            <td>
                <strong>${order.buyer?.name || 'N/A'}</strong>
                ${order.buyer?.city ? `<br><small class="text-muted">${order.buyer.city}/${order.buyer.state}</small>` : ''}
                ${order.buyer?.phone ? `<br><small class="text-muted">${formatPhone(order.buyer.phone)}</small>` : ''}
            </td>
            <td>
                ${formatDate(order.createdAt)}
                ${order.paymentDate ? `<br><small class="text-muted">Pgto: ${formatDate(order.paymentDate)}</small>` : ''}
            </td>
            <td>
                ${order.items ? order.items.length : 0} item(s)
                ${order.items && order.items[0] ? `<br><small class="text-muted">${order.items[0].sku?.partnerId || ''}</small>` : ''}
            </td>
            <td>
                <strong class="text-success">R$ ${parseFloat(order.total || 0).toFixed(2)}</strong>
                ${order.freight ? `<br><small class="text-muted">Frete: R$ ${parseFloat(order.freight).toFixed(2)}</small>` : ''}
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); abrirDetalhesPedido(${order.id})">
                    <i class="fas fa-eye"></i> Detalhes
                </button>
                ${order.marketPlaceUrl ? `
                <button class="btn btn-sm btn-outline-secondary mt-1" onclick="event.stopPropagation(); window.open('${order.marketPlaceUrl}', '_blank')">
                    <i class="fas fa-external-link-alt"></i>
                </button>` : ''}
            </td>
        </tr>
    `).join('');
}

function exibirPaginacao(pagination) {
    const paginationContainer = document.querySelector('.pagination');
    
    if (!pagination || pagination.totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    const { currentPage, totalPages, hasNext, hasPrev } = pagination;
    
    let paginationHTML = `
        <button class="page-btn" ${!hasPrev ? 'disabled' : ''} onclick="carregarPedidos(1)">
            <i class="fas fa-angle-double-left"></i> Primeira
        </button>
        <button class="page-btn" ${!hasPrev ? 'disabled' : ''} onclick="carregarPedidos(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i> Anterior
        </button>
        
        <span class="page-info">Página ${currentPage} de ${totalPages}</span>
        
        <button class="page-btn" ${!hasNext ? 'disabled' : ''} onclick="carregarPedidos(${currentPage + 1})">
            Próxima <i class="fas fa-chevron-right"></i>
        </button>
        <button class="page-btn" ${!hasNext ? 'disabled' : ''} onclick="carregarPedidos(${totalPages})">
            Última <i class="fas fa-angle-double-right"></i>
        </button>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
}

function exibirEstatisticas(stats, filters) {
    const statsContainer = document.getElementById('stats');
    
    let statsHTML = `
        <div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center;">
            <div><strong>📊 Total:</strong> ${stats.totalGeral || stats.total} pedidos</div>
            <div><strong>💰 Valor Total:</strong> R$ ${(stats.valorTotal || 0).toFixed(2)}</div>
            ${filters.dataInicio ? `<div><strong>📅 Período:</strong> ${filters.dataInicio} à ${filters.dataFim}</div>` : ''}
            <div style="margin-left: auto;">
                <button class="btn btn-sm btn-outline-success" onclick="carregarTodosPedidos()">
                    <i class="fas fa-download"></i> Carregar Todos
                </button>
                <button class="btn btn-sm btn-outline-info ms-2" onclick="testarTokenAtual()">
                    <i class="fas fa-test"></i> Testar Token
                </button>
            </div>
        </div>
    `;
    
    statsContainer.innerHTML = statsHTML;
    statsContainer.classList.remove('hidden');
}

// =============================================
// 🛠️ FUNÇÕES UTILITÁRIAS
// =============================================

// Formatação de dados
function formatMarketplace(marketplace) {
    const safeMarketplace = safeToString(marketplace);
    const marketplaces = {
        'MERCADO_LIVRE': 'Mercado Livre',
        'MERCADOLIVRE': 'Mercado Livre',
        'SHOPEE': 'Shopee',
        'AMAZON': 'Amazon',
        'NUVEMSHOP': 'Nuvem Shop',
        'VTEX': 'VTEX',
        'TRAY': 'Tray',
        'MAGAZINE_LUIZA': 'Magazine Luiza',
        'MOBLY': 'Mobly',
        'MADEIRA_MADEIRA': 'Madeira Madeira',
        'LEROY_MERLIN': 'Leroy Merlin'
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
        'CANCELED': 'Cancelado',
        'DELIVERY_ISSUE': 'Problema na Entrega',
        'PAID_WAITING_DELIVERY': 'Pago - Aguardando Entrega'
    };
    return statusMap[safeStatus] || safeStatus;
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

function safeToString(value) {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'string') return value.trim() || 'N/A';
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value.toString();
    return String(value);
}

// Funções de UI
function mostrarEstadoSemToken() {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
        emptyState.classList.remove('hidden');
        emptyState.innerHTML = `
            <i class="fas fa-key" style="font-size: 64px; margin-bottom: 20px; opacity: 0.5; color: #6c757d;"></i>
            <h3 style="color: #6c757d;">Token não configurado</h3>
            <p style="color: #6c757d;">Configure o token do AnyMarket para visualizar os pedidos</p>
            <div style="margin-top: 20px;">
                <button class="btn btn-primary me-2" onclick="document.getElementById('tokenInput')?.focus()">
                    <i class="fas fa-edit me-1"></i> Digitar Token
                </button>
                <button class="btn btn-outline-secondary" onclick="irParaConfiguracoes()">
                    <i class="fas fa-cog me-1"></i> Configurações
                </button>
            </div>
        `;
    }
    document.getElementById('ordersContainer')?.classList.add('hidden');
    document.getElementById('stats')?.classList.add('hidden');
}

function hideEmptyState() {
    document.getElementById('emptyState')?.classList.add('hidden');
    document.getElementById('ordersContainer')?.classList.remove('hidden');
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
        if (show) {
            loading.classList.remove('hidden');
            loading.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-2">Buscando pedidos...</p>
            `;
        } else {
            loading.classList.add('hidden');
        }
    }
}

function showMessage(message, type) {
    const messageDiv = document.getElementById(type === 'error' ? 'errorMessage' : 'infoMessage');
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = `alert alert-${type} alert-dismissible fade show`;
        messageDiv.classList.remove('hidden');
        
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }
}

// Funções de ação
function copiarDadosPedido(orderId) {
    const orderRow = document.querySelector(`tr[onclick*="${orderId}"]`);
    if (orderRow) {
        const text = orderRow.innerText;
        navigator.clipboard.writeText(text).then(() => {
            showToast('Dados copiados para a área de transferência!', 'success');
        }).catch(() => {
            showToast('Erro ao copiar dados', 'error');
        });
    }
}

function imprimirPedido(orderId) {
    const modalContent = document.getElementById('modalContent').innerHTML;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Pedido #${orderId}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.4; }
                    .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 15px; }
                    .section { margin-bottom: 25px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    .item-card { border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    @media print {
                        .no-print { display: none; }
                        body { margin: 0; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Pedido #${orderId}</h1>
                    <p>Emitido em: ${new Date().toLocaleString('pt-BR')}</p>
                </div>
                ${modalContent}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

function limparFiltros() {
    document.getElementById('dataInicio').value = '';
    document.getElementById('dataFim').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('marketplaceFilter').value = '';
    
    showMessage('Filtros limpos! Aplique os filtros para atualizar.', 'info');
}

function limparTela() {
    currentToken = '';
    document.getElementById('tokenInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('marketplaceFilter').value = '';
    document.getElementById('dataInicio').value = '';
    document.getElementById('dataFim').value = '';
    
    document.getElementById('ordersContainer').classList.add('hidden');
    document.getElementById('stats').classList.add('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
    document.getElementById('infoMessage').classList.add('hidden');
    
    mostrarEstadoSemToken();
    allOrders = [];
}

function irParaConfiguracoes() {
    window.location.href = '/configuracoes/tokens';
}

// Toast notification
function showToast(message, type = 'info') {
    // Implementação básica de toast - você pode usar uma biblioteca se preferir
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 4000);
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Enter no input do token
    const tokenInput = document.getElementById('tokenInput');
    if (tokenInput) {
        tokenInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                validarEConfigurarToken();
            }
        });
    }
    
    // Fechar modal com ESC
    document.addEventListener('keydown', function(event) {
        if (event.target === 'Escape') {
            fecharModal();
            fecharTokenModal();
        }
    });
});

// Fechar modais ao clicar fora
window.onclick = function(event) {
    const orderModal = document.getElementById('orderModal');
    const tokenModal = document.getElementById('tokenModal');
    
    if (event.target === orderModal) {
        fecharModal();
    }
    if (event.target === tokenModal) {
        fecharTokenModal();
    }
}

// Debug helper
window.debugSystem = function() {
    console.log('=== DEBUG SISTEMA ===');
    console.log('currentToken:', currentToken ? '***' + currentToken.slice(-4) : 'NÃO CONFIGURADO');
    console.log('allOrders count:', allOrders.length);
    console.log('currentPage:', currentPage);
    console.log('=====================');
};

// =============================================
// 🔐 MODAL DE CONFIGURAÇÃO DE TOKEN
// =============================================

function toggleTokenSection() {
    document.getElementById('tokenModal').style.display = 'block';
    // Limpar campo ao abrir modal
    document.getElementById('tokenConfigInput').value = '';
}

function fecharTokenModal() {
    document.getElementById('tokenModal').style.display = 'none';
}

async function salvarToken() {
    const tokenInput = document.getElementById('tokenConfigInput');
    const token = tokenInput.value.trim();
    
    if (!token) {
        alert('Por favor, digite o token do AnyMarket');
        return;
    }
    
    if (token.length < 20) {
        alert('O token parece muito curto. Verifique se está completo.');
        return;
    }
    
    try {
        console.log('💾 Salvando token do modal...');
        
        const response = await fetch('/api/tokens/anymarket/salvar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: token
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Fechar modal
            fecharTokenModal();
            
            // Atualizar token atual
            currentToken = token;
            
            // Mostrar mensagem de sucesso
            showMessage('✅ Token configurado com sucesso! Carregando pedidos...', 'success');
            
            // Carregar pedidos automaticamente
            hideEmptyState();
            await carregarPedidos(1);
        } else {
            throw new Error(data.error || 'Erro desconhecido ao salvar token');
        }
    } catch (error) {
        console.error('❌ Erro ao salvar token do modal:', error);
        alert('Erro ao salvar token: ' + error.message);
    }
}

// Permitir Enter no modal
document.addEventListener('DOMContentLoaded', function() {
    const tokenConfigInput = document.getElementById('tokenConfigInput');
    if (tokenConfigInput) {
        tokenConfigInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                salvarToken();
            }
        });
    }
});