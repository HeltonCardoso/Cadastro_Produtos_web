let currentToken = '';
let allOrders = [];
let currentPage = 1;
const ordersPerPage = 50;
// ✅ NOVAS VARIÁVEIS PARA ORDENAÇÃO
let currentSortField = 'createdAt';
let currentSortDirection = 'DESC';

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
    
    document.getElementById('createdAfter').value = dataInicio;
    document.getElementById('createdBefore').value = dataFim;
}

// ✅ NOVA FUNÇÃO: Exportar pedidos para Excel
async function exportarPedidos() {
    console.log('📤 Iniciando exportação para Excel...');
    
    if (!currentToken) {
        showMessage('Configure o token primeiro', 'error');
        return;
    }

    // Mostrar indicador de processamento
    const exportBtn = document.querySelector('[onclick="exportarPedidos()"]');
    const originalText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exportando...';
    exportBtn.disabled = true;

    try {
        // Coletar todos os filtros atuais
        const dataInicio = document.getElementById('createdAfter')?.value || '';
        const dataFim = document.getElementById('createdBefore')?.value || '';
        const status = document.getElementById('statusFilter')?.value || '';
        const marketplace = document.getElementById('marketplaceFilter')?.value || '';
        const numeroPedido = document.getElementById('numeroPedidoFilter')?.value || '';

        const params = new URLSearchParams({
            dataInicio: dataInicio,
            dataFim: dataFim,
            status: status,
            marketplace: marketplace,
            numeroPedido: numeroPedido
        });

        const response = await fetch(`/api/anymarket/exportar-excel?${params}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP ${response.status}`);
        }

        // Criar blob e download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Nome do arquivo com data
        const dataAtual = new Date().toISOString().split('T')[0];
        a.download = `pedidos_anymarket_${dataAtual}.xlsx`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showMessage('✅ Planilha exportada com sucesso!', 'success');

    } catch (error) {
        console.error('❌ Erro na exportação:', error);
        showMessage('❌ Erro ao exportar: ' + error.message, 'error');
    } finally {
        // Restaurar botão
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
    }
}

// ✅ NOVA FUNÇÃO: Atualização automática
let autoRefreshInterval = null;
let lastUpdateTime = null;

function iniciarAtualizacaoAutomatica() {
    // Parar atualização anterior se existir
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }

    // Atualizar a cada 2 minutos (120000 ms)
    autoRefreshInterval = setInterval(async () => {
        if (currentToken && document.getElementById('ordersContainer') && 
            !document.getElementById('ordersContainer').classList.contains('hidden')) {
            
            console.log('🔄 Atualização automática de pedidos...');
            
            // Mostrar indicador sutil de atualização
            const footer = document.getElementById('autoRefreshFooter');
            if (footer) {
                footer.innerHTML = `
                    <div class="auto-refresh-indicator updating">
                        <i class="fas fa-sync-alt fa-spin"></i>
                        Atualizando...
                    </div>
                `;
            }
            
            await carregarPedidos(currentPage);
        }
    }, 120000); // 2 minutos

    console.log('🔄 Atualização automática iniciada (2 minutos)');
}

function atualizarIndicadorAtualizacao() {
    lastUpdateTime = new Date();
    const footer = document.getElementById('autoRefreshFooter');
    if (footer) {
        footer.innerHTML = `
            <div class="auto-refresh-indicator">
                <i class="fas fa-sync-alt"></i>
                Última atualização: ${lastUpdateTime.toLocaleTimeString()}
                <span class="refresh-badge">Auto</span>
            </div>
        `;
    }
}

function mostrarIndicadorProcessamento(mostrar) {
    let indicator = document.getElementById('processingIndicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'processingIndicator';
        indicator.className = 'processing-indicator hidden';
        document.body.appendChild(indicator);
    }

    if (mostrar) {
        indicator.innerHTML = `
            <div class="processing-content">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Processando planilha...</span>
            </div>
        `;
        indicator.classList.remove('hidden');
    } else {
        indicator.classList.add('hidden');
    }
}

// ✅ FUNÇÃO: Detectar tipo de envio ML (APENAS para Mercado Livre)
function detectarTipoEnvioML(order) {
    if (order.marketPlace !== 'MERCADO_LIVRE') {
        return 'NÃO_ML';
    }
    
    console.log('🔍 Analisando pedido ML:', {
        id: order.id,
        accountName: order.accountName,
        orderTypeName: order.orderTypeName,
        logisticType: order.logisticType,
        shippingType: order.items?.[0]?.shippings?.[0]?.shippingtype,
        metadata: order.metadata
    });
    
    // ✅ 1. PRIMEIRO: Verificar orderTypeName (mais confiável)
    if (order.orderTypeName === 'ME1' || order.orderTypeName === 'ME2') {
        console.log('✅ Detectado por orderTypeName:', order.orderTypeName);
        return order.orderTypeName;
    }
    
    // ✅ 2. SEGUNDO: Verificar orderTypeName como string
    if (order.orderTypeName === 'CROSS_DOCKING') {
        console.log('✅ Detectado ME2 por CROSS_DOCKING');
        return 'ME2';
    }
    
    // ✅ 3. TERCEIRO: Verificar logisticType
    if (order.logisticType === 'MARKETPLACE') {
        console.log('✅ Detectado ME1 por MARKETPLACE');
        return 'ME1';
    }
    
    if (order.logisticType === 'SELLER') {
        console.log('✅ Detectado FULL por SELLER');
        return 'FULL';
    }
    
    // ✅ 4. QUARTO: Verificar nos itens (shippingtype)
    if (order.items && order.items.length > 0) {
        const shippingType = order.items[0]?.shippings?.[0]?.shippingtype || '';
        const shippingLower = shippingType.toLowerCase();
        
        if (shippingLower.includes('me1') || shippingLower.includes('expresso') || shippingLower.includes('água') || shippingLower.includes('aguia')) {
            console.log('✅ Detectado ME1 por shippingType:', shippingType);
            return 'ME1';
        }
        if (shippingLower.includes('me2') || shippingLower.includes('cross') || shippingLower.includes('coleta')) {
            console.log('✅ Detectado ME2 por shippingType:', shippingType);
            return 'ME2';
        }
        if (shippingLower.includes('full') || shippingLower.includes('próprio') || shippingLower.includes('proprio')) {
            console.log('✅ Detectado FULL por shippingType:', shippingType);
            return 'FULL';
        }
    }
    
    // ✅ 5. QUINTO: Verificar metadata
    if (order.metadata?.logistic_type) {
        const logisticType = order.metadata.logistic_type.toLowerCase();
        if (logisticType.includes('me1') || logisticType.includes('fulfillment')) {
            console.log('✅ Detectado ME1 por metadata:', order.metadata.logistic_type);
            return 'ME1';
        }
        if (logisticType.includes('me2') || logisticType.includes('cross')) {
            console.log('✅ Detectado ME2 por metadata:', order.metadata.logistic_type);
            return 'ME2';
        }
        if (logisticType.includes('default') || logisticType.includes('seller')) {
            console.log('✅ Detectado FULL por metadata:', order.metadata.logistic_type);
            return 'FULL';
        }
    }
    
    console.log('❓ Tipo de envio não identificado para pedido:', order.id);
    return 'DESCONHECIDO';
}

// ✅ FUNÇÃO: Obter informações detalhadas do envio (APENAS ML)
function obterInfoEnvioDetalhada(order) {
    const tipoEnvio = detectarTipoEnvioML(order);
    
    const info = {
        tipo: tipoEnvio,
        descricao: '',
        prazoCrossDocking: null,
        transportadora: order.tracking?.carrier || 'N/A',
        servico: order.items?.[0]?.shippings?.[0]?.shippingtype || 'N/A',
        accountName: order.accountName || 'N/A'
    };
    
    switch(tipoEnvio) {
        case 'ME1':
            info.descricao = 'Mercado Envios Fulfillment (ME1)';
            info.cor = 'warning';
            info.icone = '🏭';
            info.detalhes = 'ML cuida do armazenamento e envio';
            break;
            
        case 'ME2':
            info.descricao = 'Mercado Envios Cross Docking (ME2)';
            info.cor = 'info';
            info.icone = '📦';
            info.detalhes = 'Você posta nos correios';
            // Buscar prazo de cross docking
            if (order.items?.[0]?.shippings?.[0]?.crossdockingDeadline) {
                info.prazoCrossDocking = order.items[0].shippings[0].crossdockingDeadline;
            }
            break;
            
        case 'FULL':
            info.descricao = 'Envio Próprio (Full)';
            info.cor = 'success';
            info.icone = '🚚';
            info.detalhes = 'Sua logística própria';
            break;
            
        case 'NÃO_ML':
            return info; // Não faz nada para outros marketplaces
            
        default:
            info.descricao = 'Tipo de envio não identificado';
            info.cor = 'dark';
            info.icone = '❓';
            info.detalhes = 'Verificar manualmente';
    }
    
    return info;
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
    console.log(`📦 SOLICITANDO página ${page}...`);
    
    if (!currentToken) {
        showMessage('Configure o token primeiro', 'error');
        mostrarEstadoSemToken();
        return;
    }
    
    showLoading(true);
    hideEmptyState();
    
    // Mostrar indicador de processamento na tabela
    const tableLoading = document.getElementById('tableLoading');
    if (tableLoading) {
        tableLoading.classList.remove('hidden');
    }

    try {
        // Coletar filtros (INCLUI NÚMERO PEDIDO)
        const dataInicio = document.getElementById('createdAfter')?.value || '';
        const dataFim = document.getElementById('createdBefore')?.value || '';
        const status = document.getElementById('statusFilter')?.value || '';
        const marketplace = document.getElementById('marketplaceFilter')?.value || '';
        const numeroPedido = document.getElementById('numeroPedidoFilter')?.value || '';
        
        const sortField = document.getElementById('sortField')?.value || 'createdAt';
        const sortDirection = document.getElementById('sortDirection')?.value || 'DESC';
        
        currentSortField = sortField;
        currentSortDirection = sortDirection;
        
        const params = new URLSearchParams({
            page: page,
            limit: 50,
            sort: sortField,
            sortDirection: sortDirection
        });
        
        // Adicionar filtros se preenchidos
        if (status) params.append('status', status);
        if (marketplace) params.append('marketplace', marketplace);
        if (dataInicio) params.append('createdAfter', dataInicio);
        if (dataFim) params.append('createdBefore', dataFim);
        if (numeroPedido) params.append('marketPlaceNumber', numeroPedido); // ✅ NOVO FILTRO
        
        const apiUrl = `/api/anymarket/pedidos?${params}`;
        console.log(`🔗 SOLICITANDO: Página ${page} | Filtros: ${params.toString()}`);
        
        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        const data = await response.json();
        
        console.log('📄 RESPOSTA PAGINAÇÃO:', {
            paginaSolicitada: page,
            paginaAtual: data.pagination?.currentPage,
            totalPaginas: data.pagination?.totalPages,
            totalElementos: data.pagination?.totalElements,
            ordenacao: `${sortField} ${sortDirection}`,
            debug: data.debug
        });
        
        if (!response.ok) {
            throw new Error(data.error || `Erro HTTP ${response.status}`);
        }

        if (data.success) {
            // ✅ ATUALIZAR PÁGINA ATUAL
            currentPage = data.pagination.currentPage;
            
            exibirPedidos(data.orders);
            exibirEstatisticas(data.stats, data.filters);
            exibirPaginacao(data.pagination);
            atualizarIndicadorOrdenacao();
            
            // ✅ INICIAR ATUALIZAÇÃO AUTOMÁTICA APÓS PRIMEIRO CARREGAMENTO
            if (!autoRefreshInterval) {
                iniciarAtualizacaoAutomatica();
            }
            
            // ✅ ATUALIZAR INDICADOR DE ÚLTIMA ATUALIZAÇÃO
            atualizarIndicadorAtualizacao();
            
            showMessage(`✅ Página ${currentPage} de ${data.pagination.totalPages} carregada - ${data.orders.length} pedidos (Ordenado por: ${getSortFieldLabel(sortField)} ${sortDirection === 'ASC' ? 'Crescente' : 'Decrescente'})`, 'success');
        } else {
            throw new Error(data.error || 'Erro desconhecido na API');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar pedidos:', error);
        showMessage('❌ Erro: ' + error.message, 'error');
        
        // Mostrar estado vazio em caso de erro
        mostrarEstadoSemToken();
    } finally {
        showLoading(false);
        // Esconder indicador da tabela
        const tableLoading = document.getElementById('tableLoading');
        if (tableLoading) {
            tableLoading.classList.add('hidden');
        }
    }
}

// ✅ NOVA FUNÇÃO: Aplicar ordenação
function aplicarOrdenacao() {
    console.log('🔄 Aplicando ordenação...');
    carregarPedidos(1); // Sempre voltar para a página 1 ao reordenar
}

// ✅ NOVA FUNÇÃO: Atualizar indicador visual de ordenação
function atualizarIndicadorOrdenacao() {
    const sortFieldSelect = document.getElementById('sortField');
    const sortDirectionSelect = document.getElementById('sortDirection');
    
    if (sortFieldSelect && sortDirectionSelect) {
        // Remover indicadores anteriores
        const options = sortFieldSelect.querySelectorAll('option');
        options.forEach(opt => {
            opt.textContent = opt.textContent.replace(' ↑', '').replace(' ↓', '');
        });
        
        // Adicionar indicador atual
        const currentOption = sortFieldSelect.querySelector(`option[value="${currentSortField}"]`);
        if (currentOption) {
            const indicator = currentSortDirection === 'ASC' ? ' ↑' : ' ↓';
            currentOption.textContent += indicator;
        }
    }
}

// ✅ NOVA FUNÇÃO: Obter label amigável para o campo de ordenação
function getSortFieldLabel(field) {
    const labels = {
        'createdAt': 'Data Criação',
        'paymentDate': 'Data Pagamento',
        'total': 'Valor Total',
        'marketPlaceNumber': 'Nº Marketplace',
        'status': 'Status'
    };
    return labels[field] || field;
}

// ✅ NOVA FUNÇÃO: Ordenação rápida por clique no cabeçalho (opcional)
function ordenarPorCampo(field) {
    const sortFieldSelect = document.getElementById('sortField');
    const sortDirectionSelect = document.getElementById('sortDirection');
    
    if (sortFieldSelect && sortDirectionSelect) {
        // Se já está ordenando por este campo, inverte a direção
        if (currentSortField === field) {
            sortDirectionSelect.value = currentSortDirection === 'ASC' ? 'DESC' : 'ASC';
        } else {
            // Se é um campo diferente, muda o campo e mantém DESC como padrão
            sortFieldSelect.value = field;
            sortDirectionSelect.value = 'DESC';
        }
        
        aplicarOrdenacao();
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
            dataInicio: document.getElementById('createdAfter').value || '',
            dataFim: document.getElementById('createdBefore').value || '',
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

// ✅ MODIFICAR: Função buscarComFiltros para incluir novo filtro
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
// ✅ ADICIONAR: Função getMarketplaceStatusInfo que está faltando
function getMarketplaceStatusInfo(order) {
    const isMercadoLivre = order.marketPlace === 'MERCADO_LIVRE';
    const isMadeiraMadeira = order.marketPlace === 'MADEIRA_MADEIRA';
    
    if (isMercadoLivre && order.marketPlaceShipmentStatus) {
        return `<br><small class="text-muted shipment-status">${formatShipmentStatus(order.marketPlaceShipmentStatus)}</small>`;
    }
    
    if (isMadeiraMadeira && order.marketPlaceStatus) {
        return `<br><small class="text-muted">${order.marketPlaceStatus}</small>`;
    }
    
    return '';
}

function exibirPedidos(orders) {
    const tbody = document.getElementById('ordersTableBody');
    
    if (!orders || orders.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 15px; opacity: 0.5;"></i>
                    <br>
                    Nenhum pedido encontrado para os filtros selecionados
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = orders.map(order => {
        // ✅ DETECTAR MARKETPLACE E APLICAR LÓGICA ESPECÍFICA
        const isMercadoLivre = order.marketPlace === 'MERCADO_LIVRE';
        const isMadeiraMadeira = order.marketPlace === 'MADEIRA_MADEIRA';
        const isShopee = order.marketPlace === 'SHOPEE';
        
        return `
        <tr onclick="abrirDetalhesPedido(${order.id})" style="cursor: pointer;">
            <td>
                <strong class="text-primary">${order.id}</strong>
            </td>
            <td>
                <span class="marketplace-badge">${formatMarketplace(order.marketPlace)}</span>
                ${getMarketplaceSpecificBadge(order)}
            </td>
            <td>
                <span class="status-badge status-${order.status}">${formatStatus(order.status)}</span>
                ${getMarketplaceStatusInfo(order)}
            </td>
            <td>${order.marketPlaceNumber || '-'}</td>
            <td>
                <strong>${order.buyer?.name || 'N/A'}</strong>
                ${order.shipping?.city ? `<br><small class="text-muted">${order.shipping.city}/${order.shipping.state}</small>` : ''}
                ${order.buyer?.phone ? `<br><small class="text-muted">${formatPhone(order.buyer.phone)}</small>` : ''}
            </td>
            <td>
                <strong>${formatDate(order.createdAt)}</strong>
                <br>
                <small class="text-muted">${formatTime(order.createdAt)}</small>
                ${order.paymentDate ? `
                    <br>
                    <small class="text-success">
                        Pago: ${formatDate(order.paymentDate)} ${formatTime(order.paymentDate)}
                    </small>
                ` : ''}
            </td>
            <td>
                ${order.items ? order.items.length : 0} item(s)
                ${order.items && order.items[0] ? `<br><small class="text-muted">${order.items[0].sku?.partnerId || ''}</small>` : ''}
            </td>
            <td>
                <strong class="text-success">R$ ${parseFloat(order.total || 0).toFixed(2)}</strong>
                ${order.freight ? `<br><small class="text-muted">Frete: R$ ${parseFloat(order.freight).toFixed(2)}</small>` : ''}
                ${getPaymentInfo(order)}
            </td>
            <td>
                ${getShippingInfo(order)}
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
        `;
    }).join('');
}


function getMarketplaceSpecificBadge(order) {
    if (order.marketPlace === 'MERCADO_LIVRE') {
        const infoEnvio = obterInfoEnvioDetalhada(order);
        
        let badge = '';
        
        switch(infoEnvio.tipo) {
            case 'ME1':
                badge = `<span class="me1-badge" title="${infoEnvio.descricao} - ${infoEnvio.detalhes}">ME1</span>`;
                break;
            case 'ME2':
                badge = `<span class="me2-badge" title="${infoEnvio.descricao} - ${infoEnvio.detalhes}">ME2</span>`;
                break;
            case 'FULL':
                badge = `<span class="full-badge" title="${infoEnvio.descricao} - ${infoEnvio.detalhes}">FULL</span>`;
                break;
            default:
                badge = `<span class="unknown-badge" title="Tipo de envio não identificado">?</span>`;
        }
        
        // Adicionar badge da conta se for Pozelar
        if (order.accountName === 'POZELAR') {
            badge += `<span class="poz-badge" title="Conta Pozelar">POZELAR</span>`;
        } else if (order.accountName === 'MPOZENATO') {
            badge += `<span class="mpoz-badge" title="Conta MPOZENATO">MPOZENATO</span>`;
        }
        
        return badge;
    }
    
    // Para outros marketplaces, mantém o comportamento atual
    if (order.marketPlace === 'MADEIRA_MADEIRA') {
        return `<span class="mm-badge">MM</span>`;
    }
    
    return '';
}

function getPaymentInfo(order) {
    if (order.payments && order.payments[0]) {
        const payment = order.payments[0];
        let info = '';
        
        if (payment.installments && payment.installments > 1) {
            info += `<br><small class="text-info">${payment.installments}x</small>`;
        }
        
        if (payment.method) {
            info += `<br><small class="text-muted">${formatPaymentMethod(payment.method)}</small>`;
        }
        
        return info;
    }
    
    return '';
}


function getShippingInfo(order) {
    const isMercadoLivre = order.marketPlace === 'MERCADO_LIVRE';
    
    if (isMercadoLivre) {
        const infoEnvio = obterInfoEnvioDetalhada(order);
        let html = '';
        
        // Badge do tipo de envio
        if (infoEnvio.tipo !== 'DESCONHECIDO') {
            html += `<small class="envio-badge envio-${infoEnvio.cor}" title="${infoEnvio.descricao} - ${infoEnvio.detalhes}">
                ${infoEnvio.icone} ${infoEnvio.tipo}
            </small>`;
        }
        
        // Serviço específico (muito importante para Pozelar)
        if (infoEnvio.servico && infoEnvio.servico !== 'N/A') {
            html += `<br><small class="text-muted" title="Serviço de envio">${infoEnvio.servico}</small>`;
        }
        
        // Transportadora
        if (infoEnvio.transportadora && infoEnvio.transportadora !== 'N/A') {
            html += `<br><small class="tracking-info"><i class="fas fa-truck"></i> ${infoEnvio.transportadora}</small>`;
        }
        
        // Prazo de cross docking (CRÍTICO para ME2)
        if (infoEnvio.tipo === 'ME2' && infoEnvio.prazoCrossDocking) {
            const agora = new Date();
            const prazo = new Date(infoEnvio.prazoCrossDocking);
            const diasRestantes = Math.ceil((prazo - agora) / (1000 * 60 * 60 * 24));
            
            let corPrazo = 'success';
            if (diasRestantes <= 1) corPrazo = 'danger';
            else if (diasRestantes <= 2) corPrazo = 'warning';
            
            html += `
                <br>
                <small class="crossdock-prazo ${corPrazo}">
                    <i class="fas fa-clock"></i> Postar até: ${formatDate(infoEnvio.prazoCrossDocking)} (${diasRestantes} dias)
                </small>
            `;
        }
        
        // Previsão de entrega
        if (order.tracking?.estimateDate) {
            html += `
                <br>
                <small class="text-warning">
                    <i class="fas fa-calendar"></i> Prev: ${formatDate(order.tracking.estimateDate)}
                </small>
            `;
        }
        
        return html;
    }
    
    // ✅ PARA OUTROS MARKETPLACES - MANTÉM O CÓDIGO ORIGINAL
    const isMadeiraMadeira = order.marketPlace === 'MADEIRA_MADEIRA';
    
    if (isMadeiraMadeira && order.shipping?.promisedShippingTime) {
        return `
            <small class="text-warning">
                <i class="fas fa-calendar"></i> Prev: ${formatDate(order.shipping.promisedShippingTime)}
            </small>
        `;
    }
    
    if (order.items?.[0]?.shippings?.[0]?.shippingtype) {
        return `<small class="text-muted">${order.items[0].shippings[0].shippingtype}</small>`;
    }
    
    return '<small class="text-muted">-</small>';
}

function formatTime(dateString) {
    try {
        const safeDate = safeToString(dateString);
        if (safeDate === 'N/A') return 'N/A';
        return new Date(safeDate).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return 'Horário inválido';
    }
}
// ✅ FUNÇÃO DE PAGINAÇÃO CORRIGIDA
function exibirPaginacao(pagination) {
    const paginationContainer = document.querySelector('.pagination');
    
    console.log('🔢 EXIBINDO PAGINAÇÃO:', pagination);
    
    if (!pagination || !pagination.totalPages || pagination.totalPages <= 1) {
        paginationContainer.innerHTML = `
            <div class="pagination-controls">
                <span class="page-info">
                    <strong>Página 1 de 1</strong>
                    <br>
                    <small class="text-muted">${pagination?.totalElements || 0} pedidos no total</small>
                </span>
            </div>
        `;
        return;
    }

    const { currentPage, totalPages, hasNext, hasPrev, totalElements } = pagination;
    
    console.log(`🎯 Estado Paginação: Página ${currentPage} de ${totalPages} | Anterior: ${hasPrev} | Próxima: ${hasNext}`);
    
    let paginationHTML = `
        <div class="pagination-controls">
    `;
    
    // Botão Anterior
    if (hasPrev) {
        paginationHTML += `
            <button class="page-btn active" onclick="carregarPedidos(${currentPage - 1})" id="prevPage">
                <i class="fas fa-chevron-left"></i> Anterior
            </button>
        `;
    } else {
        paginationHTML += `
            <button class="page-btn disabled" disabled>
                <i class="fas fa-chevron-left"></i> Anterior
            </button>
        `;
    }
    
    // Informação da Página
    paginationHTML += `
        <span class="page-info">
            <strong>Página ${currentPage} de ${totalPages}</strong>
            <br>
            <small class="text-muted">${totalElements} pedidos no total</small>
        </span>
    `;
    
    // Botão Próxima
    if (hasNext) {
        paginationHTML += `
            <button class="page-btn active" onclick="carregarPedidos(${currentPage + 1})" id="nextPage">
                Próxima <i class="fas fa-chevron-right"></i>
            </button>
        `;
    } else {
        paginationHTML += `
            <button class="page-btn disabled" disabled>
                Próxima <i class="fas fa-chevron-right"></i>
            </button>
        `;
    }
    
    paginationHTML += `</div>`;
    
    paginationContainer.innerHTML = paginationHTML;
    
    console.log('✅ Paginação renderizada com sucesso');
}

function exibirEstatisticas(stats, filters) {
    const statsContainer = document.getElementById('stats');
    
    let statsHTML = `
        <div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center;">
            <div><strong>📊 Total:</strong> ${stats.totalGeral || stats.total} pedidos</div>
            <div><strong>💰 Valor Total:</strong> R$ ${(stats.valorTotal || 0).toFixed(2)}</div>
            ${filters.dataInicio ? `<div><strong>📅 Período:</strong> ${filters.dataInicio} à ${filters.dataFim}</div>` : ''}
        </div>
    `;
    
    statsContainer.innerHTML = statsHTML;
    statsContainer.classList.remove('hidden');
}

// ✅ FUNÇÃO PARA CARREGAR PRÓXIMA PÁGINA
function carregarProximaPagina() {
    if (currentPage < totalPages) {
        carregarPedidos(currentPage + 1);
    }
}

// ✅ FUNÇÃO PARA CARREGAR PÁGINA ANTERIOR
function carregarPaginaAnterior() {
    if (currentPage > 1) {
        carregarPedidos(currentPage - 1);
    }
}

// =============================================
// 🛠️ FUNÇÕES UTILITÁRIAS
// =============================================

// Formatação de dados
function formatMarketplace(marketplace) {
    const safeMarketplace = safeToString(marketplace);
    const marketplaces = {
        'MERCADO_LIVRE': {
            image: '/static/img/mercadolivre.png',
            name: 'Mercado Livre'
        },
        
        'SHOPEE': {
            image: '/static/img/shoppe.png',
            name: 'Shopee'
        },
        'MAGAZINE_LUIZA': {
            image: '/static/img/magalu.jpeg',
            name: 'Magalu'
        },
        'MOBLY': {
            image: '/static/img/mobly.png',
            name: 'Mobly'
        },
        'MADEIRA_MADEIRA': {
            image: '/static/img/madeiramadeira.png',
            name: 'Madeira Madeira'
        },
        'LEROY_MERLIN': {
            image: '/static/img/leroy.png',
            name: 'Leroy Merlin'
        },
    };
    const marketplaceData = marketplaces[safeMarketplace];
    if (marketplaceData) {
        return `
            <img src="${marketplaceData.image}" 
                 alt="${marketplaceData.name}"
                 title="${marketplaceData.name}"
                 class="marketplace-logo">
        `;
    }
    
    // Fallback para ícone se imagem não existir
    return `<i class="fas fa-store text-muted" title="${safeMarketplace}"></i>`;
}

function formatStatus(status) {
    const safeStatus = safeToString(status);
    const statusMap = {
        'PENDING': 'Pendente',
        'PAID_WAITING_SHIP': 'Pago',
        'INVOICED': 'Faturado',
        'SHIPPED': 'Enviadoo',
        'DELIVERED': 'Entregue',
        'CONCLUDED': 'Concluído',
        'CANCELED': 'Cancelado',
        'DELIVERY_ISSUE': 'Problema na Entrega',
        'PAID_WAITING_DELIVERY': 'Enviado'
    };
    return statusMap[safeStatus] || safeStatus;
}

function formatPaymentStatus(status) {
    const safeStatus = safeToString(status);
    const statusMap = {
        'APPROVED': 'Aprovado',
        'APROVED': 'Aprovado', // ❗ Possível typo na API
        'PENDING': 'Pendente',
        'DECLINED': 'Recusado',
        'CANCELED': 'Cancelado',
        'CANCELLED': 'Cancelado', // ❗ Possível variação
        'Aprovado': 'Aprovado', // ❗ Já em português
        'Pendente': 'Pendente', // ❗ Já em português
        'Cancelado': 'Cancelado', // ❗ Já em português
        'Paid': 'Pago', // ❗ Outra possível variação
        'Refused': 'Recusado' // ❗ Outra possível variação
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
    document.getElementById('createdAfter').value = '';
    document.getElementById('createdBefore').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('marketplaceFilter').value = '';
    
    showMessage('Filtros limpos! Aplique os filtros para atualizar.', 'info');
}

function limparTela() {
    currentToken = '';
    document.getElementById('tokenInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('marketplaceFilter').value = '';
    document.getElementById('createdAfter').value = '';
    document.getElementById('createdBefore').value = '';
    
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

// ✅ ADICIONAR: Event listener para Enter no filtro de número do pedido
document.addEventListener('DOMContentLoaded', function() {
    const numeroPedidoFilter = document.getElementById('numeroPedidoFilter');
    if (numeroPedidoFilter) {
        numeroPedidoFilter.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                buscarComFiltros();
            }
        });
    }
    
    // Iniciar atualização automática após carregamento inicial
    setTimeout(() => {
        if (currentToken) {
            iniciarAtualizacaoAutomatica();
        }
    }, 5000);
});
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

// =============================================
// 📋 MODAL DE DETALHES DO PEDIDO
// =============================================

async function abrirDetalhesPedido(orderId) {
    console.log(`📋 Abrindo detalhes do pedido: ${orderId}`);
    
    if (!currentToken) {
        showMessage('Configure o token primeiro', 'error');
        return;
    }
    
    try {
        showMessage('Carregando detalhes do pedido...', 'info');
        
        const response = await fetch(`/api/anymarket/pedidos/${orderId}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            exibirDetalhesPedido(data.order);
        } else {
            throw new Error(data.error || 'Erro ao carregar detalhes');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar detalhes:', error);
        showMessage('❌ Erro ao carregar detalhes: ' + error.message, 'error');
    }
}

function exibirDetalhesPedido(order) {
    const modalContent = document.getElementById('modalContent');
    
    const isMercadoLivre = order.marketPlace === 'MERCADO_LIVRE';
    const isMadeiraMadeira = order.marketPlace === 'MADEIRA_MADEIRA';
    
    const formattedOrder = {
        formattedTotal: parseFloat(order.total || 0).toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }),
        formattedFreight: parseFloat(order.freight || 0).toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }),
        formattedDiscount: parseFloat(order.discount || 0).toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }),
        formattedGross: parseFloat(order.gross || 0).toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }),
        formattedDate: formatDateTime(order.createdAt),
        formattedPaymentDate: order.paymentDate ? formatDateTime(order.paymentDate) : 'N/A',
        formattedShippingPromise: order.shipping?.promisedShippingTime ? formatDateTime(order.shipping.promisedShippingTime) : 'N/A',
        formattedTrackingEstimate: order.tracking?.estimateDate ? formatDateTime(order.tracking.estimateDate) : 'N/A'
    };
    
    // ✅ SEÇÕES ESPECÍFICAS POR MARKETPLACE
    const mlSpecificSections = isMercadoLivre ? `
        <!-- Status de Envio ML -->
        <div class="order-section">
            <h3>📦 Status Mercado Livre</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Status Envio:</label>
                    <span class="shipment-status">${formatShipmentStatus(order.marketPlaceShipmentStatus)}</span>
                </div>
                ${order.marketPlaceShipmentSubstatus ? `
                <div class="info-item">
                    <label>Substatus:</label>
                    <span>${order.marketPlaceShipmentSubstatus}</span>
                </div>
                ` : ''}
                <div class="info-item">
                    <label>Tipo Logística:</label>
                    <span>${formatLogisticType(order.logisticType)}</span>
                </div>
                <div class="info-item">
                    <label>Tipo Pedido:</label>
                    <span>${formatOrderType(order.orderTypeName)}</span>
                </div>
            </div>
        </div>
        
        <!-- Metadados ML -->
        ${order.metadata ? `
        <div class="order-section">
            <h3>⚙️ Metadados ML</h3>
            <div class="info-grid">
                ${order.metadata.needInvoiceXML ? `
                <div class="info-item">
                    <label>Precisa XML NF:</label>
                    <span class="${order.metadata.needInvoiceXML === 'true' ? 'text-warning' : 'text-success'}">
                        ${order.metadata.needInvoiceXML === 'true' ? '✓ Sim' : 'Não'}
                    </span>
                </div>
                ` : ''}
                ${order.metadata.printTag ? `
                <div class="info-item">
                    <label>Imprimir Tag:</label>
                    <span class="${order.metadata.printTag === 'true' ? 'text-info' : 'text-secondary'}">
                        ${order.metadata.printTag === 'true' ? '✓ Sim' : 'Não'}
                    </span>
                </div>
                ` : ''}
                ${order.metadata.logistic_type ? `
                <div class="info-item">
                    <label>Tipo Logística:</label>
                    <span>${order.metadata.logistic_type}</span>
                </div>
                ` : ''}
            </div>
        </div>
        ` : ''}
    ` : '';
    
    const madeiraMadeiraSpecificSections = isMadeiraMadeira ? `
        <!-- Informações Madeira Madeira -->
        <div class="order-section">
            <h3>🏠 Informações Madeira Madeira</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Status MM:</label>
                    <span>${order.marketPlaceStatus || 'N/A'}</span>
                </div>
                ${order.buyer?.phone ? `
                <div class="info-item">
                    <label>Telefone:</label>
                    <span>${formatPhone(order.buyer.phone)}</span>
                </div>
                ` : ''}
            </div>
        </div>
    ` : '';
    
    // ✅ SEÇÃO DE ITENS ADAPTATIVA
    const itemsSection = `
        <div class="order-section">
            <h3>🛍️ Itens do Pedido (${order.items ? order.items.length : 0})</h3>
            <div class="items-list">
                ${order.items && order.items.length > 0 ? order.items.map(item => `
                    <div class="item-card">
                        <div class="item-header">
                            <strong>${item.sku?.partnerId || 'N/A'}</strong>
                            <span class="item-price">R$ ${parseFloat(item.unit || 0).toFixed(2)}</span>
                        </div>
                        <div class="item-details">
                            <span>Qtd: ${item.amount || 1}</span>
                            <span>Total: R$ ${parseFloat(item.total || 0).toFixed(2)}</span>
                            ${item.discount ? `<span class="text-danger">Desc: R$ ${parseFloat(item.discount).toFixed(2)}</span>` : ''}
                            ${isMercadoLivre && item.shippings?.[0]?.crossdockingDeadline ? `
                            <span class="crossdocking-info">
                                <i class="fas fa-clock"></i> Crossdock: ${formatDate(item.shippings[0].crossdockingDeadline)}
                            </span>
                            ` : ''}
                        </div>
                        <div class="item-title">${item.product?.title || item.sku?.title || ''}</div>
                        ${item.sku?.ean ? `<div class="item-ean"><small>EAN: ${item.sku.ean}</small></div>` : ''}
                        ${item.idInMarketPlace ? `<div class="item-ml-id"><small>ID ${order.marketPlace}: ${item.idInMarketPlace}</small></div>` : ''}
                        ${item.officialStoreName ? `<div class="item-store"><small>Loja: ${item.officialStoreName}</small></div>` : ''}
                        ${item.shippings?.[0]?.shippingtype ? `<div class="item-shipping"><small>Transporte: ${item.shippings[0].shippingtype}</small></div>` : ''}
                    </div>
                `).join('') : '<p>Nenhum item encontrado</p>'}
            </div>
        </div>
    `;
    
    modalContent.innerHTML = `
        <div class="modal-header">
            <h2>📦 Pedido #${order.id} - ${formatMarketplaceName(order.marketPlace)}</h2>
            <button class="close-modal" onclick="fecharModal()">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Informações Básicas (COMUNS) -->
            <div class="order-section">
                <h3>📋 Informações do Pedido</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Status:</label>
                        <span class="status-badge status-${order.status}">${formatStatus(order.status)}</span>
                    </div>
                    <div class="info-item">
                        <label>Marketplace:</label>
                        <span>${formatMarketplace(order.marketPlace)} ${getMarketplaceSpecificBadge(order)}</span>
                    </div>
                    <div class="info-item">
                        <label>Nº Marketplace:</label>
                        <span>${order.marketPlaceNumber || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Data de Criação:</label>
                        <span>${formattedOrder.formattedDate}</span>
                    </div>
                    <div class="info-item">
                        <label>Account:</label>
                        <span>${order.accountName || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            ${mlSpecificSections}
            ${madeiraMadeiraSpecificSections}
            
            <!-- Informações do Comprador (COMUM) -->
            <div class="order-section">
                <h3>👤 Dados do Comprador</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Nome:</label>
                        <span>${order.buyer?.name || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Email:</label>
                        <span>${order.buyer?.email || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Documento:</label>
                        <span>${order.buyer?.document ? formatDocument(order.buyer.document) : 'N/A'} (${order.buyer?.documentType || 'N/A'})</span>
                    </div>
                    ${order.buyer?.phone ? `
                    <div class="info-item">
                        <label>Telefone:</label>
                        <span>${formatPhone(order.buyer.phone)}</span>
                    </div>
                    ` : ''}
                    ${order.buyer?.marketPlaceId ? `
                    <div class="info-item">
                        <label>ID ${order.marketPlace}:</label>
                        <span>${order.buyer.marketPlaceId}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Endereço de Entrega (COMUM) -->
            <div class="order-section">
                <h3>🏠 Endereço de Entrega</h3>
                <div class="info-grid">
                    <div class="info-item full-width">
                        <label>Endereço Completo:</label>
                        <span>${formatEnderecoCompleto(order.shipping)}</span>
                    </div>
                    <div class="info-item">
                        <label>Destinatário:</label>
                        <span>${order.shipping?.receiverName || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>CEP:</label>
                        <span>${order.shipping?.zipCode || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Cidade/UF:</label>
                        <span>${order.shipping?.city || 'N/A'}/${order.shipping?.state || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Bairro:</label>
                        <span>${order.shipping?.neighborhood || 'N/A'}</span>
                    </div>
                    ${order.shipping?.comment ? `
                    <div class="info-item full-width">
                        <label>Observações:</label>
                        <span class="shipping-comment">${order.shipping.comment}</span>
                    </div>
                    ` : ''}
                    ${order.shipping?.promisedShippingTime ? `
                    <div class="info-item">
                        <label>Promessa Entrega:</label>
                        <span class="text-info">${formattedOrder.formattedShippingPromise}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            ${itemsSection}
            
            <!-- Valores (COMUM) -->
            <div class="order-section">
                <h3>💰 Valores</h3>
                <div class="values-grid">
                    <div class="value-item">
                        <label>Subtotal:</label>
                        <span>${formattedOrder.formattedGross}</span>
                    </div>
                    ${order.discount ? `
                    <div class="value-item discount">
                        <label>Desconto:</label>
                        <span class="text-danger">-R$ ${parseFloat(order.discount).toFixed(2)}</span>
                    </div>
                    ` : ''}
                    <div class="value-item">
                        <label>Frete:</label>
                        <span>${formattedOrder.formattedFreight}</span>
                    </div>
                    ${order.sellerFreight ? `
                    <div class="value-item">
                        <label>Frete Seller:</label>
                        <span>R$ ${parseFloat(order.sellerFreight).toFixed(2)}</span>
                    </div>
                    ` : ''}
                    <div class="value-item total">
                        <label>Total:</label>
                        <span>${formattedOrder.formattedTotal}</span>
                    </div>
                </div>
            </div>
            
            <!-- Pagamento (COMUM) -->
            <div class="order-section">
                <h3>💳 Pagamento</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Status:</label>
                        <span class="status-badge status-${order.payments?.[0]?.status || 'PENDING'}">
                            ${formatPaymentStatus(order.payments?.[0]?.status)}
                        </span>
                    </div>
                    <div class="info-item">
                        <label>Método:</label>
                        <span>${formatPaymentMethod(order.payments?.[0]?.method)}</span>
                    </div>
                    <div class="info-item">
                        <label>Data Pagamento:</label>
                        <span>${formattedOrder.formattedPaymentDate}</span>
                    </div>
                    <div class="info-item">
                        <label>Parcelas:</label>
                        <span>${order.payments?.[0]?.installments || 1}x</span>
                    </div>
                    <div class="info-item">
                        <label>Valor:</label>
                        <span>R$ ${parseFloat(order.payments?.[0]?.value || order.total || 0).toFixed(2)}</span>
                    </div>
                    ${order.payments?.[0]?.marketplaceFee ? `
                    <div class="info-item">
                        <label>Taxa Marketplace:</label>
                        <span class="text-danger">R$ ${parseFloat(order.payments[0].marketplaceFee).toFixed(2)}</span>
                    </div>
                    ` : ''}
                    ${order.payments?.[0]?.cardOperator ? `
                    <div class="info-item">
                        <label>Operadora:</label>
                        <span>${formatCardOperator(order.payments[0].cardOperator)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Rastreamento (ML específico) -->
            ${order.tracking ? `
            <div class="order-section">
                <h3>🚚 Rastreamento</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Transportadora:</label>
                        <span>${order.tracking.carrier || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Previsão Entrega:</label>
                        <span>${formattedOrder.formattedTrackingEstimate}</span>
                    </div>
                </div>
            </div>
            ` : ''}
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="fecharModal()">Fechar</button>
            <button class="btn btn-primary" onclick="imprimirPedido(${order.id})">
                <i class="fas fa-print"></i> Imprimir
            </button>
            ${order.marketPlaceUrl ? `
            <button class="btn btn-outline" onclick="window.open('${order.marketPlaceUrl}', '_blank')">
                <i class="fas fa-external-link-alt"></i> Ver no ${formatMarketplaceName(order.marketPlace)}
            </button>
            ` : ''}
        </div>
    `;
    
    document.getElementById('orderModal').style.display = 'block';
}


// ✅ NOVA FUNÇÃO: Formatar nome do marketplace
function formatMarketplaceName(marketplace) {
    const names = {
        'MERCADO_LIVRE': 'Mercado Livre',
        'MADEIRA_MADEIRA': 'Madeira Madeira',
        'SHOPEE': 'Shopee',
        'MAGAZINE_LUIZA': 'Magazine Luiza',
        'MOBLY': 'Mobly',
        'LEROY_MERLIN': 'Leroy Merlin'
    };
    return names[marketplace] || marketplace;
}


function fecharModal() {
    document.getElementById('orderModal').style.display = 'none';
}

// Função auxiliar para formatar endereço
function formatEndereco(addressData) {
    if (!addressData) return 'N/A';
    
    const parts = [];
    
    // ✅ CORREÇÃO: Usar os campos corretos do JSON
    if (addressData.address || addressData.street) parts.push(addressData.address || addressData.street);
    if (addressData.number) parts.push(addressData.number);
    if (addressData.complement) parts.push(addressData.complement);
    if (addressData.neighborhood) parts.push(addressData.neighborhood);
    if (addressData.city) parts.push(addressData.city);
    if (addressData.state) parts.push(addressData.state);
    if (addressData.zipCode) parts.push(`CEP: ${addressData.zipCode}`);
    if (addressData.receiverName) parts.push(`Recebedor: ${addressData.receiverName}`);
    
    return parts.length > 0 ? parts.join(', ') : 'N/A';
}
// Fechar modal ao clicar fora
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

// Fechar modal com ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        fecharModal();
        fecharTokenModal();
    }
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

function formatShipmentStatus(status) {
    const statusMap = {
        'pending': 'Pendente',
        'handling': 'Em preparação',
        'ready_to_ship': 'Pronto para envio',
        'shipped': 'Enviado',
        'delivered': 'Entregue',
        'not_delivered': 'Não entregue',
        'manufacturing': 'Em fabricação',
        'PENDING': 'Pendente',
        'HANDLING': 'Em preparação',
        'READY_TO_SHIP': 'Pronto para envio',
        'SHIPPED': 'Enviado',
        'DELIVERED': 'Entregue',
        'NOT_DELIVERED': 'Não entregue',
        'MANUFACTURING': 'Em fabricação'
    };
    return statusMap[status] || status || 'N/A';
}

function formatLogisticType(type) {
    const types = {
        'MARKETPLACE': 'Marketplace',
        'CROSS_DOCKING': 'Cross Docking',
        'FULFILLMENT': 'Fulfillment',
        'UNKNOWN': 'Desconhecido'
    };
    return types[type] || type || 'N/A';
}

function formatOrderType(type) {
    const types = {
        'CROSS_DOCKING': 'Cross Docking',
        'NORMAL': 'Normal',
        'FULFILLMENT': 'Fulfillment'
    };
    return types[type] || type || 'N/A';
}

function formatCardOperator(operator) {
    const operators = {
        'master': 'Mastercard',
        'visa': 'Visa',
        'elo': 'Elo',
        'hipercard': 'Hipercard',
        'amex': 'American Express'
    };
    return operators[operator] || operator || 'N/A';
}

function formatPaymentMethod(method) {
    const methods = {
        'credit_card': 'Cartão de Crédito',
        'debit_card': 'Cartão de Débito',
        'boleto': 'Boleto Bancário',
        'pix': 'PIX',
        'wallet': 'Carteira Digital',
        'CARTAO_CREDITO': 'Cartão de Crédito',
        'CARTAO_DEBITO': 'Cartão de Débito',
        'master': 'Cartão Mastercard',
        'visa': 'Cartão Visa',
        'elo': 'Cartão Elo',
        'Pix': 'PIX',
        'BOLETO': 'Boleto'
    };
    return methods[method] || method || 'N/A';
}

function formatPaymentStatus(status) {
    const statusMap = {
        'approved': 'Aprovado',
        'Aprovado': 'Aprovado',
        'pending': 'Pendente',
        'Pendente': 'Pendente',
        'in_process': 'Em processamento',
        'rejected': 'Rejeitado',
        'cancelled': 'Cancelado',
        'Cancelado': 'Cancelado',
        'refunded': 'Estornado',
        'APPROVED': 'Aprovado',
        'PENDING': 'Pendente',
        'IN_PROCESS': 'Em processamento',
        'REJECTED': 'Rejeitado',
        'CANCELLED': 'Cancelado',
        'REFUNDED': 'Estornado'
    };
    return statusMap[status] || status || 'N/A';
}

function formatEnderecoCompleto(shipping) {
    if (!shipping) return 'N/A';
    
    const parts = [];
    if (shipping.address) parts.push(shipping.address);
    if (shipping.number) parts.push(shipping.number);
    if (shipping.neighborhood) parts.push(shipping.neighborhood);
    if (shipping.city) parts.push(shipping.city);
    if (shipping.state) parts.push(shipping.state);
    if (shipping.zipCode) parts.push(`CEP: ${shipping.zipCode}`);
    
    return parts.length > 0 ? parts.join(', ') : 'N/A';
}

function formatMarketplaceName(marketplace) {
    const names = {
        'MERCADO_LIVRE': 'Mercado Livre',
        'MADEIRA_MADEIRA': 'Madeira Madeira',
        'SHOPEE': 'Shopee',
        'MAGAZINE_LUIZA': 'Magazine Luiza',
        'MOBLY': 'Mobly',
        'LEROY_MERLIN': 'Leroy Merlin',
        'WEB_CONTINENTAL_V2': 'Web Continental'
    };
    return names[marketplace] || marketplace;
}

// ✅ FUNÇÕES DE FORMATAÇÃO BÁSICAS (caso não existam)

function formatDate(dateString) {
    try {
        const safeDate = safeToString(dateString);
        if (safeDate === 'N/A') return 'N/A';
        return new Date(safeDate).toLocaleDateString('pt-BR');
    } catch {
        return 'Data inválida';
    }
}

function formatTime(dateString) {
    try {
        const safeDate = safeToString(dateString);
        if (safeDate === 'N/A') return 'N/A';
        return new Date(safeDate).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return 'Horário inválido';
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

// ✅ FUNÇÃO DE FORMATAÇÃO DE STATUS (caso não exista)
function formatStatus(status) {
    const safeStatus = safeToString(status);
    const statusMap = {
        'PENDING': 'Pendente',
        'PAID_WAITING_SHIP': 'Pago',
        'INVOICED': 'Faturado',
        'SHIPPED': 'Enviado',
        'DELIVERED': 'Entregue',
        'CONCLUDED': 'Concluído',
        'CANCELED': 'Cancelado',
        'DELIVERY_ISSUE': 'Problema na Entrega',
        'PAID_WAITING_DELIVERY': 'Enviado',
        'APPROVED': 'Aprovado'
    };
    return statusMap[safeStatus] || safeStatus;
}

// ✅ FUNÇÃO DE FORMATAÇÃO DE MARKETPLACE (caso não exista)
function formatMarketplace(marketplace) {
    const safeMarketplace = safeToString(marketplace);
    const marketplaces = {
        'MERCADO_LIVRE': {
            image: '/static/img/mercadolivre.png',
            name: 'Mercado Livre'
        },
        'SHOPEE': {
            image: '/static/img/shoppe.png',
            name: 'Shopee'
        },
        'MAGAZINE_LUIZA': {
            image: '/static/img/magalu.jpeg',
            name: 'Magalu'
        },
        'MOBLY': {
            image: '/static/img/mobly.png',
            name: 'Mobly'
        },
        'MADEIRA_MADEIRA': {
            image: '/static/img/madeiramadeira.png',
            name: 'Madeira Madeira'
        },
        'LEROY_MERLIN': {
            image: '/static/img/leroy.png',
            name: 'Leroy Merlin'
        },
        'WEB_CONTINENTAL_V2': {
            image: '/static/img/webcontinental.png',
            name: 'Web Continental'
        }
    };
    
    const marketplaceData = marketplaces[safeMarketplace];
    if (marketplaceData) {
        return `
            <img src="${marketplaceData.image}" 
                 alt="${marketplaceData.name}"
                 title="${marketplaceData.name}"
                 class="marketplace-logo">
        `;
    }
    
    // Fallback para ícone se imagem não existir
    return `<i class="fas fa-store text-muted" title="${safeMarketplace}"></i>`;
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