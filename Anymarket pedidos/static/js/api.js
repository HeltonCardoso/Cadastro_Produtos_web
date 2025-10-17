// Variáveis globais para controle de paginação
let paginaAtual = 1;
let totalPaginas = 1;
let pedidosPorPagina = 10; // Mostrar 20 pedidos por página
let totalPedidos = 0;

// Funções relacionadas à API
async function carregarPedidos(novaPagina = 1) {
    const token = document.getElementById('tokenInput').value.trim();
    const statusFilter = document.getElementById('statusFilter').value;
    const marketplaceFilter = document.getElementById('marketplaceFilter').value;
    const dataInicio = document.getElementById('dataInicio').value;
    const dataFim = document.getElementById('dataFim').value;
    
    if (!token) {
        mostrarErro('Por favor, digite seu GumgaToken');
        return;
    }

    if (!dataInicio || !dataFim) {
        mostrarErro('Por favor, selecione um período de data');
        return;
    }

    // Validar período
    const validacao = validarPeriodo(dataInicio, dataFim);
    if (!validacao.valido) {
        mostrarErro(validacao.erro);
        return;
    }

    mostrarLoading(true);
    limparMensagens();
    
    paginaAtual = novaPagina;
    const offset = (paginaAtual - 1) * pedidosPorPagina;

    mostrarDebug(`🚀 Carregando página ${paginaAtual}...`);

    try {
        let url = `https://api.anymarket.com.br/v2/orders?limit=${pedidosPorPagina}&offset=${offset}`;
        
        // Adicionar filtros suportados
        const params = [];
        if (statusFilter) params.push(`status=${statusFilter}`);
        if (marketplaceFilter) params.push(`marketplace=${marketplaceFilter}`);
        if (dataInicio) params.push(`since=${dataInicio}T00:00:00-03:00`);
        if (dataFim) params.push(`until=${dataFim}T23:59:59-03:00`);
        
        if (params.length > 0) {
            url += '&' + params.join('&');
        }

        mostrarDebug(`📤 Página ${paginaAtual}: ${url}`);

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'gumgaToken': token
            }
        });

        mostrarDebug(`📥 Status: ${response.status} ${response.statusText}`);

        if (response.status === 401) {
            throw new Error('Token inválido ou não autorizado');
        }

        if (response.status === 403) {
            throw new Error('Acesso proibido - verifique as permissões do token');
        }

        if (response.status === 400) {
            throw new Error('Requisição inválida - verifique os parâmetros');
        }

        if (!response.ok) {
            const errorText = await response.text();
            mostrarDebug(`❌ Erro completo: ${errorText}`);
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        window.pedidosData = data.content || [];
        totalPedidos = data.page ? data.page.totalElements : window.pedidosData.length;
        totalPaginas = Math.ceil(totalPedidos / pedidosPorPagina);
        
        mostrarDebug(`📊 Página ${paginaAtual}: ${window.pedidosData.length} pedidos de ${totalPedidos} total`);

        if (window.pedidosData.length === 0) {
            mostrarInfo('ℹ️ Nenhum pedido encontrado com os filtros selecionados.');
            mostrarEstadoVazio();
        } else {
           // mostrarInfo(`📄 Página ${paginaAtual} de ${totalPaginas} - ${totalPedidos} pedidos no total`);
            
            atualizarEstatisticas(window.pedidosData);
            ordenarPedidos();
            mostrarInterfacePedidos();
            atualizarControlesPaginacao();
        }

    } catch (error) {
        console.error('Erro:', error);
        mostrarDebug(`❌ Erro completo: ${error.message}`);
        mostrarErro(`Erro ao carregar pedidos: ${error.message}`);
        mostrarEstadoVazio();
    } finally {
        mostrarLoading(false);
    }
}

// Funções de controle de paginação
function proximaPagina() {
    if (paginaAtual < totalPaginas) {
        carregarPedidos(paginaAtual + 1);
    }
}

function paginaAnterior() {
    if (paginaAtual > 1) {
        carregarPedidos(paginaAtual - 1);
    }
}

function irParaPagina(pagina) {
    if (pagina >= 1 && pagina <= totalPaginas) {
        carregarPedidos(pagina);
    }
}

function atualizarControlesPaginacao() {
    const paginacaoDiv = document.getElementById('paginacao');
    if (!paginacaoDiv) return;

    let paginacaoHTML = `
        <div class="paginacao-info">
            Página ${paginaAtual} de ${totalPaginas} - ${totalPedidos} pedidos
        </div>
        <div class="paginacao-controles">
            <button class="btn-paginacao" onclick="paginaAnterior()" ${paginaAtual === 1 ? 'disabled' : ''}>
                ◀ Anterior
            </button>
    `;

    // Mostrar números de página (máximo 7 páginas)
    const inicio = Math.max(1, paginaAtual - 3);
    const fim = Math.min(totalPaginas, paginaAtual + 3);

    for (let i = inicio; i <= fim; i++) {
        paginacaoHTML += `
            <button class="btn-paginacao ${i === paginaAtual ? 'ativo' : ''}" onclick="irParaPagina(${i})">
                ${i}
            </button>
        `;
    }

    paginacaoHTML += `
            <button class="btn-paginacao" onclick="proximaPagina()" ${paginaAtual === totalPaginas ? 'disabled' : ''}>
                Próximo ▶
            </button>
        </div>
        <div class="paginacao-tamanho">
            <label>Pedidos por página:</label>
            <select onchange="alterarPedidosPorPagina(this.value)">
                <option value="10" ${pedidosPorPagina === 10 ? 'selected' : ''}>10</option>
                <option value="20" ${pedidosPorPagina === 20 ? 'selected' : ''}>20</option>
                <option value="50" ${pedidosPorPagina === 50 ? 'selected' : ''}>50</option>
                <option value="100" ${pedidosPorPagina === 100 ? 'selected' : ''}>100</option>
            </select>
        </div>
    `;

    paginacaoDiv.innerHTML = paginacaoHTML;
}

function alterarPedidosPorPagina(novoValor) {
    pedidosPorPagina = parseInt(novoValor);
    paginaAtual = 1; // Voltar para primeira página
    carregarPedidos(1);
}