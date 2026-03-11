// static/js/consultar_mercado_livre.js - VERSÃO COM PAGINAÇÃO E EXPORTAÇÃO DIRETA

// =========================================
// VARIÁVEIS GLOBAIS
// =========================================
let ultimosResultados = [];
let resultadosFiltrados = [];
let dadosPlanilha = [];
let filtrosAtivos = {};
let isLoading = false;
let mlbSelecionado = null;

// Variáveis de paginação
let paginaAtual = 1;
let itensPorPagina = 100;
let totalPaginas = 1;

let processoAtualizacao = {
    ativo: false,
    total: 0,
    processados: 0,
    sucesso: 0,
    erros: 0,
    inicio: null,
    atualizacoes: [],
    cancelar: false
};

// =========================================
// FUNÇÕES DE CONFIGURAÇÃO E AUTENTICAÇÃO
// =========================================

function verificarConfiguracao() {
    fetch('/api/mercadolivre/configuracao')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                const statusElement = document.getElementById('statusConfiguracao');
                if (statusElement) {
                    if (data.configurado) {
                        statusElement.innerHTML = 'Mercado Livre: <span class="badge bg-success">Configurado</span>';
                    } else {
                        statusElement.innerHTML = 'Mercado Livre: <span class="badge bg-warning">Não configurado</span>';
                    }
                }
            }
        })
        .catch(error => {
            console.error('Erro ao verificar configuração:', error);
        });
}

function salvarConfiguracaoCompleta() {
    const clientId = document.getElementById('clientId').value.trim();
    const clientSecret = document.getElementById('clientSecret').value.trim();
    const accessToken = document.getElementById('accessToken').value.trim();
    const refreshToken = document.getElementById('refreshToken').value.trim();
    
    if (!clientId || !clientSecret) {
        mostrarMensagem('Preencha pelo menos Client ID e Client Secret', 'error');
        return;
    }

    fetch('/api/mercadolivre/configurar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            client_id: clientId,
            client_secret: clientSecret
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso && (accessToken && refreshToken)) {
            return autenticarMercadoLivre(accessToken, refreshToken);
        }
        return data;
    })
    .then(data => {
        if (data.sucesso) {
            fecharConfigModal();
            mostrarMensagem('Configuração salva com sucesso!', 'success');
            verificarConfiguracao();
        } else {
            mostrarMensagem('Erro na configuração: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro ao salvar configuração: ' + error.message, 'error');
    });
}

function autenticarMercadoLivre(accessToken, refreshToken) {
    return fetch('/api/mercadolivre/autenticar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            access_token: accessToken,
            refresh_token: refreshToken
        })
    })
    .then(response => response.json());
}

function desautenticarMercadoLivre() {
    if (!confirm('Tem certeza que deseja sair?')) {
        return;
    }
    
    fetch('/api/mercadolivre/desautenticar', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem('Desautenticado com sucesso!', 'success');
            fecharConfigModal();
            verificarConfiguracao();
        } else {
            mostrarMensagem('Erro ao desautenticar: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro ao desautenticar: ' + error.message, 'error');
    });
}

// =========================================
// FUNÇÕES DE BUSCA
// =========================================

function buscarMLBs() {
    const mlbsText = document.getElementById('mlbs').value.trim();
    const tipoBusca = document.getElementById('tipoBusca').value;
    
    if (tipoBusca === 'mlbs' && !mlbsText) {
        mostrarMensagem('Digite os códigos MLB para buscar', 'error');
        return;
    }
    
    // Processar MLBs
    let mlbs = [];
    if (tipoBusca === 'mlbs') {
        mlbs = mlbsText.split(/[\n,]+/).map(mlb => mlb.trim()).filter(mlb => mlb);
        
        if (mlbs.length === 0) {
            mostrarMensagem('Nenhum MLB válido encontrado', 'error');
            return;
        }
        
        mlbs = mlbs.map(mlb => {
            if (!mlb.toUpperCase().startsWith('MLB')) {
                return 'MLB' + mlb.replace(/[^0-9]/g, '');
            }
            return mlb.toUpperCase();
        });
    }
    
    mostrarLoading(true);
    limparResultados(true);
    
    fetch('/api/mercadolivre/buscar-mlb', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            mlbs: mlbs,
            tipo_busca: tipoBusca
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Resposta da API:', data);
        processarResultadoBusca(data);
    })
    .catch(error => {
        console.error('Erro na busca:', error);
        mostrarErro('Erro ao buscar MLBs: ' + error.message);
        mostrarLoading(false);
    });
}

function processarResultadoBusca(data) {
    if (!data.sucesso) {
        mostrarErro(data.erro || 'Erro desconhecido na busca');
        return;
    }
    
    ultimosResultados = data.resultados || [];
    
    // Aplicar filtros se houver
    if (Object.keys(filtrosAtivos).length > 0) {
        resultadosFiltrados = aplicarFiltrosEmMemoria(ultimosResultados);
    } else {
        resultadosFiltrados = [...ultimosResultados];
    }
    
    // Mostrar/ocultar botões de exportação
    const btnExportarDireto = document.getElementById('btnExportarDireto');
    const btnExportar = document.getElementById('btnExportar');
    
    if (ultimosResultados.length > 0) {
        btnExportarDireto.style.display = 'inline-block';
        btnExportar.style.display = 'inline-block';
    } else {
        btnExportarDireto.style.display = 'none';
        btnExportar.style.display = 'none';
    }
    
    mostrarEstatisticas(data);
    
    // Resetar paginação
    paginaAtual = 1;
    atualizarPaginacao();
    mostrarResultadosPaginados();
}

function mostrarEstatisticas(data) {
    const statsDiv = document.getElementById('stats');
    
    let totalEncontrado = data.total_encontrado || 0;
    let totalNaoEncontrado = data.total_nao_encontrado || 0;
    let totalProcessados = data.resultados ? data.resultados.length : 0;
    
    statsDiv.innerHTML = `
        <i class="fas fa-chart-bar"></i>
        <strong>Estatísticas:</strong>
        ${totalEncontrado} encontrados • 
        ${totalNaoEncontrado} não encontrados • 
        ${totalProcessados} processados • 
        ${new Date(data.timestamp).toLocaleTimeString()}
    `;
    
    statsDiv.classList.remove('hidden');
}

// =========================================
// FUNÇÕES DE PAGINAÇÃO
// =========================================

function atualizarPaginacao() {
    totalPaginas = Math.ceil(resultadosFiltrados.length / itensPorPagina) || 1;
    
    if (paginaAtual > totalPaginas) {
        paginaAtual = totalPaginas;
    }
    
    const paginacaoContainer = document.getElementById('paginacaoContainer');
    if (resultadosFiltrados.length === 0) {
        paginacaoContainer.style.display = 'none';
        return;
    }
    
    paginacaoContainer.style.display = 'flex';
    
    // Atualizar informações
    const inicio = ((paginaAtual - 1) * itensPorPagina) + 1;
    const fim = Math.min(paginaAtual * itensPorPagina, resultadosFiltrados.length);
    
    document.getElementById('mostrandoDe').textContent = inicio;
    document.getElementById('mostrandoAte').textContent = fim;
    document.getElementById('totalRegistros').textContent = resultadosFiltrados.length;
    document.getElementById('paginaAtual').textContent = paginaAtual;
    document.getElementById('totalPaginas').textContent = totalPaginas;
    
    // Habilitar/desabilitar botões
    document.getElementById('btnPaginaAnterior').disabled = paginaAtual <= 1;
    document.getElementById('btnProximaPagina').disabled = paginaAtual >= totalPaginas;
}

function paginaAnterior() {
    if (paginaAtual > 1) {
        paginaAtual--;
        mostrarResultadosPaginados();
    }
}

function proximaPagina() {
    if (paginaAtual < totalPaginas) {
        paginaAtual++;
        mostrarResultadosPaginados();
    }
}

function alterarLimitePagina() {
    itensPorPagina = parseInt(document.getElementById('limitPorPagina').value);
    paginaAtual = 1;
    mostrarResultadosPaginados();
}

function mostrarResultadosPaginados() {
    const inicio = (paginaAtual - 1) * itensPorPagina;
    const fim = inicio + itensPorPagina;
    const resultadosPagina = resultadosFiltrados.slice(inicio, fim);
    
    mostrarResultados(resultadosPagina);
    atualizarPaginacao();
}

function mostrarResultados(resultados) {
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    const tableBody = document.getElementById('ordersTableBody');
    const tableLoading = document.getElementById('tableLoading');
    
    if (!resultados || resultados.length === 0) {
        mostrarLoading(false);
        ordersContainer.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }
    
    ordersContainer.classList.remove('hidden');
    emptyState.classList.add('hidden');
    
    if (tableLoading) {
        tableLoading.classList.add('hidden');
    }
    
    if (tableBody) {
        tableBody.innerHTML = '';
    }
    
    resultados.forEach(item => {
        const temErro = item.error || item.status === 'error';
        
        const linha = `
            <tr onclick="abrirDetalhes('${item.id}')">
                <td><strong>${!temErro ? (item.meu_sku || 'N/A') : '-'}</strong></td>
                <td>
                    <strong>${item.id || 'N/A'}</strong>
                    ${temErro ? '<br><small class="text-danger">' + item.error + '</small>' : ''}
                </td>
                <td>${!temErro ? (item.title ? item.title.substring(0, 40) + (item.title.length > 40 ? '...' : '') : 'N/A') : '-'}</td>
                <td>${!temErro ? ('R$ ' + (item.price || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})) : '-'}</td>
                <td>${!temErro ? (item.available_quantity || 0) : '-'}</td>
                <td>
                    ${!temErro ? `<span class="badge ${item.shipping_mode === 'me2' ? 'badge-me2' : 'badge-me1'}">${item.shipping_mode || 'N/A'}</span>` : '-'}
                </td>
                <td>
                    ${!temErro ? (item.manufacturing_time && item.manufacturing_time !== 'N/A' ? 
                        `<span class="badge bg-info">${item.manufacturing_time}</span>` : 
                        '<span class="badge bg-warning">Sem prazo</span>') : '-'}
                </td>
                <td>
                    ${!temErro ? `<span class="badge ${getStatusBadgeClass(item.status)}">${item.status || 'N/A'}</span>` : '-'}
                </td>
                <td>
                    ${!temErro ? `<span class="badge ${item.frete_gratis === 'Sim' ? 'bg-success' : 'bg-secondary'}">${item.frete_gratis || 'Não'}</span>` : '-'}
                </td>
                <td>
                    ${!temErro ? `
                        <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); abrirDetalhes('${item.id}')" title="Ver detalhes">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="event.stopPropagation(); abrirModalManufacturing('${item.id}')" title="Editar prazo">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${item.tem_variacoes === 'Sim' ? `
                            <button class="btn btn-sm btn-outline-warning" onclick="event.stopPropagation(); abrirDetalhes('${item.id}')" title="Tem ${item.quantidade_variacoes} variações">
                                <i class="fas fa-layer-group"></i>
                            </button>
                        ` : ''}
                        <a href="${item.permalink || '#'}" target="_blank" class="btn btn-sm btn-outline-secondary" onclick="event.stopPropagation()" title="Abrir no ML">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    ` : '-'}
                </td>
            </tr>
        `;
        tableBody.innerHTML += linha;
    });
    
    mostrarLoading(false);
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'active': return 'bg-success';
        case 'paused': return 'bg-warning';
        case 'closed': return 'bg-secondary';
        default: return 'bg-light text-dark';
    }
}

// =========================================
// NOVA FUNÇÃO: EXPORTAÇÃO DIRETA PARA EXCEL
// =========================================

function exportarDiretoParaExcel() {
    if (!ultimosResultados || ultimosResultados.length === 0) {
        mostrarMensagem('Nenhum resultado para exportar', 'error');
        return;
    }

    mostrarLoading(true);

    // Usar resultados filtrados (se houver filtros ativos)
    const dadosParaExportar = resultadosFiltrados.length > 0 ? resultadosFiltrados : ultimosResultados;
    
    // Preparar dados para exportação
    const dadosExportacao = [];
    
    // Estatísticas de vendas
    let totalVendasAPI = 0;
    let totalVendasReal = 0;
    
    dadosParaExportar.forEach(item => {
        if (item.error || item.status === 'error') {
            dadosExportacao.push({
                'MLB Principal': item.id || 'N/A',
                'MLB Variação': '-',
                'Tipo': 'Principal (Erro)',
                'SKU': '-',
                'Título': '-',
                'Preço': '-',
                'Estoque': '-',
                'Vendidos (API)': '-',
                'Vendidos (Real)': '-',
                'Vendidos (Variações)': '-',
                'Modo Envio': '-',
                'Prazo Fabricação': '-',
                'Status': 'Erro',
                'Frete Grátis': '-',
                'Erro': item.error || 'Erro desconhecido'
            });
        } else {
            // CALCULAR VENDAS CORRETAMENTE
            const vendidosAPI = item.sold_quantity || 0;  // O que vem no campo sold_quantity do principal
            let vendidosReal = 0;  // Soma REAL das variações
            let vendidosVariacoes = 0;  // Detalhe das variações
            
            // Verificar se tem variações
            if (item.variacoes_detalhes && item.variacoes_detalhes.length > 0) {
                // SOMAR as vendas de TODAS as variações
                vendidosVariacoes = item.variacoes_detalhes.reduce((total, variacao) => {
                    return total + (variacao.sold_quantity || 0);
                }, 0);
                
                // O valor REAL é a soma das variações
                vendidosReal = vendidosVariacoes;
                
                // DEBUG: Mostrar quando há diferença
                if (vendidosAPI !== vendidosReal) {
                    console.log(`⚠️ MLB ${item.id}: API=${vendidosAPI}, Real=${vendidosReal} (diferença: ${vendidosAPI - vendidosReal})`);
                }
            } else {
                // Anúncio SEM variações - usar o sold_quantity do principal
                vendidosReal = vendidosAPI;
            }
            
            totalVendasAPI += vendidosAPI;
            totalVendasReal += vendidosReal;
            
            // Item principal
            dadosExportacao.push({
                'MLB Principal': item.id || 'N/A',
                'MLB Variação': '-',
                'Tipo': 'Principal',
                'SKU': item.meu_sku || 'N/A',
                'Título': item.title || 'N/A',
                'Preço': item.price ? `R$ ${item.price.toFixed(2)}` : 'R$ 0,00',
                'Estoque': item.available_quantity || 0,
                'Vendidos (API)': vendidosAPI,
                'Vendidos (Real)': vendidosReal,
                'Vendidos (Variações)': vendidosVariacoes,
                'Modo Envio': item.shipping_mode || 'N/A',
                'Prazo Fabricação': item.manufacturing_time || 'N/A',
                'Status': item.status || 'N/A',
                'Frete Grátis': item.frete_gratis || 'Não',
                'Qtd Variações': item.variacoes_detalhes?.length || 0,
                'Catálogo': item.eh_catalogo || 'Não',
                'Tipo Anúncio': item.tipo_anuncio || 'N/A',
                'Data Criação': item.date_created || 'N/A',
                'Link': item.permalink || 'N/A',
                'Erro': ''
            });

            // Adicionar variações INDIVIDUALMENTE
            if (item.variacoes_detalhes && item.variacoes_detalhes.length > 0) {
                item.variacoes_detalhes.forEach((variacao, index) => {
                    const atributos = variacao.attribute_combinations.map(attr => 
                        `${attr.name}: ${attr.value_name}`
                    ).join('; ');
                    
                    dadosExportacao.push({
                        'MLB Principal': item.id || 'N/A',
                        'MLB Variação': variacao.id || 'N/A',
                        'Tipo': `Variação ${index + 1}`,
                        'SKU': variacao.seller_custom_field || 'N/A',
                        'Título': `${item.title} - ${atributos.substring(0, 50)}`,
                        'Preço': variacao.price ? `R$ ${variacao.price.toFixed(2)}` : 'R$ 0,00',
                        'Estoque': variacao.available_quantity || 0,
                        'Vendidos (API)': '-',
                        'Vendidos (Real)': variacao.sold_quantity || 0,
                        'Vendidos (Variações)': variacao.sold_quantity || 0,
                        'Modo Envio': item.shipping_mode || 'N/A',
                        'Prazo Fabricação': variacao.manufacturing_time || 'N/A',
                        'Status': item.status || 'N/A',
                        'Frete Grátis': item.frete_gratis || 'Não',
                        'Qtd Variações': '-',
                        'Catálogo': 'Variação',
                        'Tipo Anúncio': 'Variação',
                        'Data Criação': item.date_created || 'N/A',
                        'Link': item.permalink || 'N/A',
                        'Erro': ''
                    });
                });
            }
        }
    });

    // Fazer requisição para exportação
    fetch('/api/mercadolivre/exportar-excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            dados: dadosExportacao,
            total_principais: dadosParaExportar.length,
            total_variações: dadosExportacao.length - dadosParaExportar.length,
            total_geral: dadosExportacao.length,
            total_vendas_api: totalVendasAPI,
            total_vendas_real: totalVendasReal,
            timestamp: new Date().toISOString()
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        const nomeArquivo = `mlb_vendas_${new Date().toISOString().slice(0,10)}_${new Date().getHours()}${new Date().getMinutes()}.xlsx`;
        a.download = nomeArquivo;
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Mostrar estatísticas detalhadas
        const diff = totalVendasAPI - totalVendasReal;
        const diffPercentual = totalVendasReal > 0 ? ((diff / totalVendasReal) * 100).toFixed(1) : 0;
        
        let mensagem = `✅ Exportação concluída!\n`;
        mensagem += `📊 Total itens: ${dadosExportacao.length}\n`;
        mensagem += `📈 Vendas (API Principal): ${totalVendasAPI.toLocaleString()}\n`;
        mensagem += `✅ Vendas (Real - Soma Variações): ${totalVendasReal.toLocaleString()}\n`;
        
        if (diff !== 0) {
            mensagem += `⚠️ Diferença: ${diff > 0 ? '+' : ''}${diff.toLocaleString()} (${diffPercentual}%)`;
        }
        
        mostrarMensagem(mensagem, diff === 0 ? 'success' : 'warning');
    })
    .catch(error => {
        console.error('Erro na exportação:', error);
        mostrarErro('Erro ao exportar: ' + error.message);
    })
    .finally(() => {
        mostrarLoading(false);
    });
}

// =========================================
// FUNÇÕES DE FILTROS
// =========================================

function inicializarFiltros() {
    console.log('Inicializando filtros...');
    
    const filtros = ['tipoBusca', 'filtroEnvio', 'filtroManufacturing', 'filtroStatus'];
    
    filtros.forEach(filtroId => {
        const select = document.getElementById(filtroId);
        if (select) {
            select.addEventListener('change', function() {
                const valor = this.value;
                const tipo = this.id;
                
                console.log(`Filtro alterado: ${tipo} = ${valor}`);
                atualizarFiltroAtivo(tipo, valor);
                
                if (ultimosResultados.length > 0) {
                    aplicarFiltros();
                }
            });
        }
    });
}

function atualizarFiltroAtivo(tipo, valor) {
    if (valor === 'todos' || valor === '') {
        delete filtrosAtivos[tipo];
    } else {
        filtrosAtivos[tipo] = valor;
    }
    
    atualizarBadgesFiltrosAtivos();
}

function atualizarBadgesFiltrosAtivos() {
    const container = document.getElementById('activeFilters');
    if (!container) return;
    
    container.innerHTML = '';
    
    const entries = Object.entries(filtrosAtivos);
    
    if (entries.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    
    entries.forEach(([tipo, valor]) => {
        let label = '';
        let displayValor = valor;
        
        switch(tipo) {
            case 'tipoBusca':
                label = 'Busca:';
                displayValor = valor === 'mlbs' ? 'Por MLB' : 'Meus anúncios';
                break;
            case 'filtroEnvio':
                label = 'Envio:';
                displayValor = valor === 'me2' ? 'Apenas ME2' : 'Apenas ME1';
                break;
            case 'filtroManufacturing':
                label = 'Manufacturing:';
                displayValor = valor === 'com' ? 'Com prazo' : 'Sem prazo';
                break;
            case 'filtroStatus':
                label = 'Status:';
                displayValor = valor.charAt(0).toUpperCase() + valor.slice(1);
                break;
        }
        
        const badge = document.createElement('div');
        badge.className = 'filter-badge';
        badge.innerHTML = `
            <span>${label} ${displayValor}</span>
            <button class="remove-filter" onclick="removerFiltro('${tipo}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(badge);
    });
}

function removerFiltro(tipo) {
    delete filtrosAtivos[tipo];
    
    const selectId = {
        'tipoBusca': 'tipoBusca',
        'filtroEnvio': 'filtroEnvio',
        'filtroManufacturing': 'filtroManufacturing',
        'filtroStatus': 'filtroStatus'
    }[tipo];
    
    if (selectId) {
        const select = document.getElementById(selectId);
        if (select) {
            select.value = 'todos';
        }
    }
    
    atualizarBadgesFiltrosAtivos();
    
    if (ultimosResultados.length > 0) {
        aplicarFiltros();
    }
}

function aplicarFiltros() {
    if (Object.keys(filtrosAtivos).length === 0) {
        resultadosFiltrados = [...ultimosResultados];
    } else {
        resultadosFiltrados = aplicarFiltrosEmMemoria(ultimosResultados);
    }
    
    paginaAtual = 1;
    mostrarResultadosPaginados();
    
    // Atualizar estatísticas
    const statsDiv = document.getElementById('stats');
    if (statsDiv && !statsDiv.classList.contains('hidden')) {
        const totalEncontrado = ultimosResultados.filter(item => !item.error && item.status !== 'error').length;
        const totalFiltrado = resultadosFiltrados.filter(item => !item.error && item.status !== 'error').length;
        
        const htmlAtual = statsDiv.innerHTML;
        const novaHtml = htmlAtual.replace(
            /(\d+) encontrados/,
            `${totalFiltrado} de ${totalEncontrado} encontrados (filtrados)`
        );
        statsDiv.innerHTML = novaHtml;
    }
}

function aplicarFiltrosEmMemoria(resultados) {
    if (Object.keys(filtrosAtivos).length === 0 || !resultados || resultados.length === 0) {
        return resultados || [];
    }
    
    return resultados.filter(item => {
        if (item.error || item.status === 'error') return false;
        
        for (const [tipo, valor] of Object.entries(filtrosAtivos)) {
            let passaFiltro = true;
            
            switch(tipo) {
                case 'filtroEnvio':
                    if (valor === 'me2') {
                        passaFiltro = item.shipping_mode === 'me2';
                    } else if (valor === 'me1') {
                        passaFiltro = item.shipping_mode === 'me1';
                    }
                    break;
                    
                case 'filtroManufacturing':
                    if (valor === 'com') {
                        passaFiltro = item.manufacturing_time && 
                                     item.manufacturing_time !== 'N/A' && 
                                     item.manufacturing_time !== '0' && 
                                     item.manufacturing_time !== 0;
                    } else if (valor === 'sem') {
                        passaFiltro = !item.manufacturing_time || 
                                     item.manufacturing_time === 'N/A' || 
                                     item.manufacturing_time === '0' || 
                                     item.manufacturing_time === 0;
                    }
                    break;
                    
                case 'filtroStatus':
                    if (valor !== 'todos') {
                        passaFiltro = item.status === valor;
                    }
                    break;
                    
                default:
                    passaFiltro = true;
            }
            
            if (!passaFiltro) return false;
        }
        
        return true;
    });
}

function limparFiltros() {
    filtrosAtivos = {};
    
    document.querySelectorAll('.filter-select').forEach(select => {
        select.value = 'todos';
    });
    
    atualizarBadgesFiltrosAtivos();
    
    if (ultimosResultados.length > 0) {
        resultadosFiltrados = [...ultimosResultados];
        paginaAtual = 1;
        mostrarResultadosPaginados();
        
        const statsDiv = document.getElementById('stats');
        if (statsDiv && !statsDiv.classList.contains('hidden')) {
            const totalEncontrado = ultimosResultados.filter(item => !item.error && item.status !== 'error').length;
            statsDiv.innerHTML = statsDiv.innerHTML.replace(
                /(\d+) de \d+ encontrados \(filtrados\)/,
                `${totalEncontrado} encontrados`
            );
        }
    }
    
    mostrarMensagem('Filtros limpos', 'success');
}

function toggleFilters() {
    const filtersHeader = document.getElementById('filtersHeader');
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    
    if (!filtersHeader || !toggleBtn) return;
    
    const isCollapsed = filtersHeader.classList.contains('collapsed');
    const icon = toggleBtn.querySelector('i');
    const text = toggleBtn.querySelector('span');
    
    if (isCollapsed) {
        filtersHeader.classList.remove('collapsed');
        if (icon) icon.className = 'fas fa-chevron-up';
        if (text) text.textContent = 'Recolher Filtros';
    } else {
        filtersHeader.classList.add('collapsed');
        if (icon) icon.className = 'fas fa-chevron-down';
        if (text) text.textContent = 'Expandir Filtros';
    }
}

// =========================================
// FUNÇÕES DE ATUALIZAÇÃO DE MANUFACTURING
// =========================================

function abrirModalManufacturing(mlbId) {
    mlbSelecionado = mlbId;
    document.getElementById('manufacturingMlb').value = mlbId;
    document.getElementById('modalManufacturing').style.display = 'block';
}

function fecharManufacturingModal() {
    document.getElementById('modalManufacturing').style.display = 'none';
    mlbSelecionado = null;
}

function confirmarAtualizacaoManufacturing() {
    const dias = document.getElementById('manufacturingDias').value;
    
    if (!mlbSelecionado || !dias) {
        mostrarMensagem('Selecione um MLB e um prazo', 'error');
        return;
    }
    
    if (!confirm(`Deseja atualizar o prazo do MLB ${mlbSelecionado} para ${dias} dias?`)) {
        return;
    }
    
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
    btn.disabled = true;
    
    fetch('/api/mercadolivre/atualizar-manufacturing', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            mlb: mlbSelecionado,
            dias: parseInt(dias)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem(data.mensagem || 'Prazo atualizado com sucesso!', 'success');
            fecharManufacturingModal();
            atualizarLinhaTabela(mlbSelecionado, dias);
        } else {
            mostrarMensagem('Erro na atualização: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro na atualização: ' + error.message, 'error');
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

function atualizarLinhaTabela(mlbId, novosDias) {
    const linhas = document.querySelectorAll('#ordersTableBody tr');
    linhas.forEach(linha => {
        const mlbCell = linha.querySelector('td:nth-child(2) strong');
        if (mlbCell && mlbCell.textContent === mlbId) {
            const prazoCell = linha.querySelector('td:nth-child(7)');
            if (prazoCell) {
                if (novosDias === '0') {
                    prazoCell.innerHTML = '<span class="badge bg-warning">Sem prazo</span>';
                } else {
                    prazoCell.innerHTML = `<span class="badge bg-info">${novosDias} dias</span>`;
                }
            }
        }
    });
}

function atualizarManufacturingEmMassa() {
    const mlbsText = document.getElementById('mlbs').value.trim();
    
    if (!mlbsText) {
        mostrarMensagem('Digite os códigos MLB para atualização em massa', 'error');
        return;
    }
    
    const mlbs = mlbsText.split(/[\n,]+/).map(mlb => mlb.trim()).filter(mlb => mlb);
    const dias = prompt('Digite o número de dias para todos os MLBs:');
    
    if (!dias || isNaN(dias)) {
        mostrarMensagem('Digite um número válido de dias', 'error');
        return;
    }
    
    if (!confirm(`Deseja atualizar ${mlbs.length} MLBs para ${dias} dias?`)) {
        return;
    }
    
    const atualizacoes = mlbs.map(mlb => ({
        mlb: mlb.toUpperCase().startsWith('MLB') ? mlb.toUpperCase() : 'MLB' + mlb,
        dias: parseInt(dias)
    }));
    
    abrirModalProgresso(atualizacoes);
}

// =========================================
// FUNÇÕES DE MODAL DE DETALHES
// =========================================

function abrirDetalhes(mlbId) {
    const item = ultimosResultados.find(r => r.id === mlbId);
    
    if (!item || item.error) {
        mostrarMensagem('Item não encontrado ou com erro', 'error');
        return;
    }

    document.getElementById('detalheMlb').textContent = item.id || 'N/A';
    document.getElementById('detalheSku').textContent = item.meu_sku || 'N/A';
    document.getElementById('detalheStatus').innerHTML = `<span class="badge ${getStatusBadgeClass(item.status)}">${item.status || 'N/A'}</span>`;
    document.getElementById('detalheTipo').textContent = `${item.tipo_anuncio || 'N/A'} (${item.tipo_premium || 'Standard'})`;
    document.getElementById('detalheCatalogo').innerHTML = `<span class="badge ${item.eh_catalogo === 'Sim' ? 'bg-info' : 'bg-secondary'}">${item.eh_catalogo || 'Não'}</span>`;
    
    document.getElementById('detalhePreco').textContent = item.price ? 'R$ ' + item.price.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : 'N/A';
    document.getElementById('detalheEstoque').textContent = item.available_quantity || 0;
    document.getElementById('detalheVendidos').textContent = item.sold_quantity || 0;
    document.getElementById('detalheEnvio').innerHTML = `<span class="badge ${item.shipping_mode === 'me2' ? 'badge-me2' : 'badge-me1'}">${item.shipping_mode || 'N/A'}</span>`;
    document.getElementById('detalheFrete').innerHTML = `<span class="badge ${item.frete_gratis === 'Sim' ? 'bg-success' : 'bg-secondary'}">${item.frete_gratis || 'Não'}</span>`;
    
    document.getElementById('linkAnuncioML').href = item.permalink || '#';

    const temVariacoes = item.variacoes_detalhes && item.variacoes_detalhes.length > 0;
    const secaoVariacoes = document.getElementById('secaoVariacoes');
    const semVariacoes = document.getElementById('semVariacoes');
    const corpoTabela = document.getElementById('corpoTabelaVariacoes');
    
    if (temVariacoes) {
        secaoVariacoes.style.display = 'block';
        semVariacoes.style.display = 'none';
        corpoTabela.innerHTML = '';
        
        item.variacoes_detalhes.forEach(variacao => {
            const atributos = variacao.attribute_combinations.map(attr => 
                `${attr.name}: ${attr.value_name}`
            ).join(', ');
            
            const linha = `
                <tr>
                    <td><small>${variacao.id || 'N/A'}</small></td>
                    <td>${atributos || 'Sem atributos'}</td>
                    <td>R$ ${variacao.price ? variacao.price.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : '0,00'}</td>
                    <td>${variacao.available_quantity || 0}</td>
                    <td>${variacao.sold_quantity || 0}</td>
                    <td>
                        ${variacao.manufacturing_time && variacao.manufacturing_time !== 'N/A' ? 
                            `<span class="badge bg-info">${variacao.manufacturing_time}</span>` : 
                            '<span class="badge bg-warning">Sem prazo</span>'}
                    </td>
                    <td><small>${variacao.seller_custom_field || 'N/A'}</small></td>
                </tr>
            `;
            corpoTabela.innerHTML += linha;
        });
    } else {
        secaoVariacoes.style.display = 'none';
        semVariacoes.style.display = 'block';
    }

    document.getElementById('modalDetalhesMLB').style.display = 'block';
}

// =========================================
// FUNÇÕES DE PLANILHA
// =========================================

function abrirModalPlanilha() {
    console.log('Abrindo modal de planilha...');
    
    document.getElementById('fileUpload').value = '';
    document.getElementById('previewSection').style.display = 'none';
    document.getElementById('btnProcessarPlanilha').disabled = true;
    document.getElementById('previewTableBody').innerHTML = '';
    document.getElementById('previewTotal').textContent = '0';
    dadosPlanilha = [];
    
    document.getElementById('modalPlanilha').style.display = 'block';
}

function fecharModalPlanilha() {
    document.getElementById('modalPlanilha').style.display = 'none';
}

function baixarModeloPlanilha() {
    try {
        const dados = [
            ['MLB', 'DIAS'],
            ['MLB1234567890', '5'],
            ['MLB9876543210', '10'],
            ['MLB5555555555', '0']
        ];
        
        let csvContent = dados.map(row => row.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = 'modelo_atualizacao_prazo.csv';
        link.click();
        
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Erro ao baixar modelo:', error);
        mostrarMensagem('Erro ao baixar modelo: ' + error.message, 'error');
    }
}

function processarArquivoUpload(file) {
    if (!file) return;

    const extensao = file.name.split('.').pop().toLowerCase();
    
    if (!['xlsx', 'xls', 'csv'].includes(extensao)) {
        mostrarMensagem('Formato de arquivo não suportado. Use Excel ou CSV.', 'error');
        return;
    }

    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            if (extensao === 'csv') {
                processarCSV(e.target.result);
            } else {
                processarExcel(e.target.result);
            }
        } catch (error) {
            console.error('Erro ao processar arquivo:', error);
            mostrarMensagem('Erro ao processar arquivo: ' + error.message, 'error');
        }
    };
    
    if (extensao === 'csv') {
        reader.readAsText(file);
    } else {
        reader.readAsArrayBuffer(file);
    }
}

function processarExcel(data) {
    const workbook = XLSX.read(data, { type: 'array' });
    const primeiraPlanilha = workbook.Sheets[workbook.SheetNames[0]];
    const jsonData = XLSX.utils.sheet_to_json(primeiraPlanilha);
    
    const dados = jsonData.map(linha => {
        const mlb = (linha.MLB || linha.mlb || linha['Código'] || '').toString().toUpperCase().trim();
        const dias = parseInt(linha.DIAS || linha.dias || linha.PRAZO || 0);
        return { mlb, dias };
    }).filter(item => item.mlb && !isNaN(item.dias));
    
    exibirPreviaPlanilha(dados);
}

function processarCSV(csvText) {
    const linhas = csvText.split('\n').filter(linha => linha.trim());
    const cabecalho = linhas[0].split(',').map(col => col.trim().toUpperCase());
    const idxMLB = cabecalho.indexOf('MLB');
    const idxDIAS = cabecalho.indexOf('DIAS');
    
    if (idxMLB === -1 || idxDIAS === -1) {
        mostrarMensagem('Colunas MLB e DIAS não encontradas', 'error');
        return;
    }
    
    const dados = [];
    for (let i = 1; i < linhas.length; i++) {
        const colunas = linhas[i].split(',').map(col => col.trim());
        if (colunas.length > Math.max(idxMLB, idxDIAS)) {
            const mlb = colunas[idxMLB];
            const dias = parseInt(colunas[idxDIAS]);
            if (mlb && !isNaN(dias)) {
                dados.push({ mlb, dias });
            }
        }
    }
    
    exibirPreviaPlanilha(dados);
}

function exibirPreviaPlanilha(dados) {
    dadosPlanilha = dados.filter(item => item.mlb && !isNaN(item.dias));
    
    if (dadosPlanilha.length === 0) {
        mostrarMensagem('Nenhum dado válido encontrado', 'error');
        return;
    }
    
    const tbody = document.getElementById('previewTableBody');
    tbody.innerHTML = '';
    
    dadosPlanilha.slice(0, 10).forEach(item => {
        const isValid = validarMLB(item.mlb);
        const linha = `
            <tr class="${isValid ? 'preview-valid' : 'preview-invalid'}">
                <td>${item.mlb}</td>
                <td>${item.dias} dias</td>
                <td>${isValid ? '✅ Válido' : '❌ Inválido'}</td>
            </tr>
        `;
        tbody.innerHTML += linha;
    });
    
    if (dadosPlanilha.length > 10) {
        tbody.innerHTML += `<tr><td colspan="3" style="text-align: center;">... e mais ${dadosPlanilha.length - 10} itens</td></tr>`;
    }
    
    document.getElementById('previewTotal').textContent = dadosPlanilha.length;
    document.getElementById('previewSection').style.display = 'block';
    document.getElementById('btnProcessarPlanilha').disabled = false;
    
    mostrarMensagem(`${dadosPlanilha.length} MLBs encontrados na planilha`, 'success');
}

function validarMLB(mlb) {
    if (!mlb) return false;
    const mlbStr = mlb.toString().toUpperCase().trim();
    return mlbStr.startsWith('MLB') || /^\d+$/.test(mlbStr);
}

function processarPlanilha() {
    if (!dadosPlanilha || dadosPlanilha.length === 0) {
        mostrarMensagem('Nenhum dado para processar', 'error');
        return;
    }
    
    const mlbsValidos = dadosPlanilha.filter(item => validarMLB(item.mlb));
    
    if (mlbsValidos.length === 0) {
        mostrarMensagem('Nenhum MLB válido para processar', 'error');
        return;
    }
    
    if (!confirm(`Deseja atualizar ${mlbsValidos.length} MLBs conforme a planilha?`)) {
        return;
    }
    
    fecharModalPlanilha();
    
    const atualizacoes = mlbsValidos.map(item => ({
        mlb: item.mlb.toUpperCase().startsWith('MLB') ? item.mlb.toUpperCase() : 'MLB' + item.mlb,
        dias: item.dias
    }));
    
    abrirModalProgresso(atualizacoes);
}

// =========================================
// FUNÇÕES DE PROGRESSO
// =========================================

function abrirModalProgresso(atualizacoes) {
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = '0% (0/' + atualizacoes.length + ')';
    document.getElementById('progressSucesso').textContent = '0';
    document.getElementById('progressErros').textContent = '0';
    document.getElementById('progressRestantes').textContent = atualizacoes.length;
    document.getElementById('activityLog').innerHTML = '';
    document.getElementById('btnCancelar').style.display = 'block';
    document.getElementById('btnConcluir').style.display = 'none';
    document.getElementById('currentMlb').textContent = '-';
    document.getElementById('currentStatus').textContent = 'Aguardando...';
    document.getElementById('currentStatus').className = 'status-badge status-processing';
    
    document.getElementById('modalProgresso').style.display = 'block';
    
    setTimeout(() => {
        iniciarProcessoAtualizacao(atualizacoes);
    }, 100);
}

function iniciarProcessoAtualizacao(atualizacoes) {
    processoAtualizacao = {
        ativo: true,
        total: atualizacoes.length,
        processados: 0,
        sucesso: 0,
        erros: 0,
        inicio: new Date(),
        atualizacoes: atualizacoes,
        cancelar: false
    };
    
    processarProximaAtualizacao();
}

async function processarProximaAtualizacao() {
    if (!processoAtualizacao.ativo || processoAtualizacao.cancelar) {
        finalizarProcesso();
        return;
    }
    
    if (processoAtualizacao.processados >= processoAtualizacao.total) {
        finalizarProcesso();
        return;
    }
    
    const atualizacao = processoAtualizacao.atualizacoes[processoAtualizacao.processados];
    
    document.getElementById('currentMlb').textContent = atualizacao.mlb;
    document.getElementById('currentStatus').textContent = 'Processando...';
    document.getElementById('currentStatus').className = 'status-badge status-processing';
    
    try {
        const response = await fetch('/api/mercadolivre/atualizar-manufacturing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mlb: atualizacao.mlb,
                dias: atualizacao.dias
            })
        });
        
        const data = await response.json();
        
        processoAtualizacao.processados++;
        
        if (data.sucesso) {
            processoAtualizacao.sucesso++;
            adicionarLog(`✅ ${atualizacao.mlb} - ${atualizacao.dias} dias`, 'log-success');
            document.getElementById('currentStatus').textContent = 'Sucesso';
            document.getElementById('currentStatus').className = 'status-badge status-success';
        } else {
            processoAtualizacao.erros++;
            adicionarLog(`❌ ${atualizacao.mlb} - Erro: ${data.erro}`, 'log-error');
            document.getElementById('currentStatus').textContent = 'Erro';
            document.getElementById('currentStatus').className = 'status-badge status-error';
        }
        
        atualizarBarraProgresso();
        
        setTimeout(processarProximaAtualizacao, 500);
        
    } catch (error) {
        processoAtualizacao.processados++;
        processoAtualizacao.erros++;
        adicionarLog(`❌ ${atualizacao.mlb} - Erro: ${error.message}`, 'log-error');
        document.getElementById('currentStatus').textContent = 'Erro';
        document.getElementById('currentStatus').className = 'status-badge status-error';
        
        atualizarBarraProgresso();
        
        setTimeout(processarProximaAtualizacao, 500);
    }
}

function atualizarBarraProgresso() {
    const percentual = (processoAtualizacao.processados / processoAtualizacao.total) * 100;
    const progresso = Math.round(percentual);
    
    document.getElementById('progressFill').style.width = percentual + '%';
    document.getElementById('progressText').textContent = 
        `${progresso}% (${processoAtualizacao.processados}/${processoAtualizacao.total})`;
    
    document.getElementById('progressSucesso').textContent = processoAtualizacao.sucesso;
    document.getElementById('progressErros').textContent = processoAtualizacao.erros;
    document.getElementById('progressRestantes').textContent = processoAtualizacao.total - processoAtualizacao.processados;
    
    const tempoDecorrido = (new Date() - processoAtualizacao.inicio) / 1000;
    const velocidade = tempoDecorrido > 0 ? (processoAtualizacao.processados / tempoDecorrido).toFixed(1) : 0;
    const tempoRestante = velocidade > 0 ? Math.round((processoAtualizacao.total - processoAtualizacao.processados) / velocidade) : 0;
    
    let infoVelocidade = `${velocidade} MLB/s`;
    if (tempoRestante > 0) {
        const minutos = Math.floor(tempoRestante / 60);
        const segundos = tempoRestante % 60;
        infoVelocidade += ` • ⏱️ ${minutos}:${segundos.toString().padStart(2, '0')}`;
    }
    
    document.getElementById('progressSpeed').textContent = infoVelocidade;
    
    const progressBar = document.getElementById('modalProgresso').querySelector('.progress-bar');
    progressBar.classList.remove('progress-complete', 'progress-error');
    
    if (processoAtualizacao.erros > 0 && processoAtualizacao.processados === processoAtualizacao.total) {
        progressBar.classList.add('progress-error');
    } else if (processoAtualizacao.processados === processoAtualizacao.total) {
        progressBar.classList.add('progress-complete');
    }
}

function adicionarLog(mensagem, classe) {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${classe}`;
    logEntry.textContent = mensagem;
    
    const logContainer = document.getElementById('activityLog');
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function cancelarAtualizacao() {
    if (confirm('Deseja cancelar a atualização?')) {
        processoAtualizacao.cancelar = true;
        processoAtualizacao.ativo = false;
        adicionarLog('⏹️ Atualização cancelada', 'log-warning');
        document.getElementById('btnCancelar').style.display = 'none';
        document.getElementById('btnConcluir').style.display = 'block';
    }
}

function finalizarProcesso() {
    processoAtualizacao.ativo = false;
    
    document.getElementById('btnCancelar').style.display = 'none';
    document.getElementById('btnConcluir').style.display = 'block';
    
    if (processoAtualizacao.cancelar) {
        adicionarLog('📊 Processo interrompido', 'log-warning');
    } else {
        adicionarLog(`🎯 Concluído: ${processoAtualizacao.sucesso} sucesso, ${processoAtualizacao.erros} erros`, 'log-info');
        
        setTimeout(() => {
            mostrarMensagem(
                `Atualização: ${processoAtualizacao.sucesso} sucesso, ${processoAtualizacao.erros} erros`,
                processoAtualizacao.erros === 0 ? 'success' : 'warning'
            );
        }, 500);
    }
}

function fecharModalProgresso() {
    document.getElementById('modalProgresso').style.display = 'none';
    processoAtualizacao.ativo = false;
    
    if (processoAtualizacao.sucesso > 0 && ultimosResultados.length > 0) {
        setTimeout(() => buscarMLBs(), 1000);
    }
}

// =========================================
// FUNÇÕES AUXILIARES DE UI
// =========================================

function mostrarLoading(mostrar) {
    isLoading = mostrar;
    const tableLoading = document.getElementById('tableLoading');
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (mostrar) {
        ordersContainer.classList.remove('hidden');
        tableLoading.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
    } else {
        tableLoading.classList.add('hidden');
    }
}

function limparResultados(mantemContainer = false) {
    const statsDiv = document.getElementById('stats');
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    const btnExportarDireto = document.getElementById('btnExportarDireto');
    const btnExportar = document.getElementById('btnExportar');
    const tableBody = document.getElementById('ordersTableBody');
    
    if (tableBody) tableBody.innerHTML = '';
    if (statsDiv) statsDiv.classList.add('hidden');
    
    if (btnExportarDireto) btnExportarDireto.style.display = 'none';
    if (btnExportar) btnExportar.style.display = 'none';
    
    if (!mantemContainer) {
        if (ordersContainer) ordersContainer.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
    } else {
        if (ordersContainer) ordersContainer.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
    }
    
    filtrosAtivos = {};
    resultadosFiltrados = [];
    ultimosResultados = [];
    
    const paginacaoContainer = document.getElementById('paginacaoContainer');
    if (paginacaoContainer) paginacaoContainer.style.display = 'none';
}

function limparCampos() {
    document.getElementById('mlbs').value = '';
    limparResultados();
    mostrarMensagem('Campos limpos', 'success');
}

function mostrarMensagem(mensagem, tipo) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo === 'error' ? 'danger' : tipo}`;
    alertDiv.innerHTML = `
        <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle'}"></i>
        ${mensagem}
    `;
    
    const container = document.querySelector('.mercado-livre-container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        if (alertDiv.parentNode) alertDiv.remove();
    }, 3000);
}

function mostrarErro(mensagem) {
    mostrarMensagem(mensagem, 'danger');
}

function fecharConfigModal() {
    document.getElementById('configModal').style.display = 'none';
}

function fecharDetalhesModal() {
    document.getElementById('modalDetalhesMLB').style.display = 'none';
}

function abrirConfigModal() {
    document.getElementById('configModal').style.display = 'block';
    carregarContas();
}

// =========================================
// FUNÇÕES DE CONTAS
// =========================================

function carregarContas() {
    fetch('/api/mercadolivre/contas')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                atualizarInterfaceContas(data);
            }
        })
        .catch(error => console.error('Erro ao carregar contas:', error));
}

function atualizarInterfaceContas(data) {
    renderizarContas(data.contas, data.conta_atual);
    atualizarStatusContaAtual(data.contas, data.conta_atual);
}

function atualizarStatusContaAtual(contas, contaAtualId) {
    const statusElement = document.getElementById('statusConfiguracao');
    if (!statusElement) return;
    
    const contaAtual = contas.find(c => c.id === contaAtualId);
    
    if (!contaAtual) {
        statusElement.innerHTML = 'Mercado Livre: <span class="badge bg-danger">Nenhuma conta</span>';
        return;
    }
    
    if (contaAtual.has_token) {
        statusElement.innerHTML = `
            Mercado Livre: 
            <span class="badge bg-success">${contaAtual.name}</span>
            ${contaAtual.nickname ? `<small>(${contaAtual.nickname})</small>` : ''}
        `;
    } else {
        statusElement.innerHTML = `
            Mercado Livre: 
            <span class="badge bg-warning">${contaAtual.name} (pendente)</span>
        `;
    }
}

function renderizarContas(contas, contaAtualId) {
    const container = document.getElementById('contasList');
    if (!container) return;
    
    container.innerHTML = '';
    
    contas.forEach(conta => {
        const isAtual = conta.id === contaAtualId;
        const card = document.createElement('div');
        card.className = `account-card ${isAtual ? 'account-current' : ''}`;
        
        card.innerHTML = `
            <div class="account-header">
                <div>
                    <h5>${conta.name}</h5>
                    <small class="text-muted">App ID: ${conta.app_id}</small>
                </div>
                <div>
                    ${isAtual ? '<span class="badge bg-primary"><i class="fas fa-check"></i> Atual</span>' : ''}
                    ${conta.has_token ? 
                        '<span class="badge bg-success"><i class="fas fa-key"></i> Autenticada</span>' : 
                        '<span class="badge bg-warning"><i class="fas fa-clock"></i> Pendente</span>'}
                </div>
            </div>
            
            <div class="account-info">
                ${conta.nickname ? 
                    `<div><i class="fas fa-user"></i> ${conta.nickname}</div>` : 
                    `<div><i class="fas fa-exclamation-triangle"></i> Não autenticada</div>`}
                <div><i class="fas fa-calendar"></i> Criada em: ${new Date(conta.created_at).toLocaleDateString()}</div>
            </div>
            
            <div class="account-actions">
                ${!isAtual && conta.has_token ? `
                    <button class="btn btn-sm btn-outline-primary" onclick="selecionarConta('${conta.id}')">
                        <i class="fas fa-play-circle"></i> Usar
                    </button>
                ` : ''}
                
                ${conta.has_token ? `
                    <button class="btn btn-sm btn-outline-info" onclick="testarConta('${conta.id}')">
                        <i class="fas fa-vial"></i> Testar
                    </button>
                ` : ''}
                
                ${!isAtual ? `
                    <button class="btn btn-sm btn-outline-danger" onclick="removerConta('${conta.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                ` : ''}
            </div>
        `;
        
        container.appendChild(card);
    });
}

function abrirAdicionarConta() {
    const nome = prompt('Nome da conta:');
    if (!nome) return;
    
    const appId = prompt('App ID:');
    if (!appId) return;
    
    const secretKey = prompt('Secret Key:');
    if (!secretKey) return;
    
    fetch('/api/mercadolivre/contas/adicionar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            account_name: nome,
            app_id: appId,
            secret_key: secretKey
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem('Conta adicionada com sucesso!', 'success');
            carregarContas();
        } else {
            mostrarMensagem('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarMensagem('Erro: ' + error.message, 'error');
    });
}

function selecionarConta(accountId) {
    fetch(`/api/mercadolivre/contas/${accountId}/selecionar`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem('Conta selecionada!', 'success');
            carregarContas();
            
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            mostrarMensagem('Erro: ' + data.erro, 'error');
        }
    });
}

function testarConta(accountId) {
    fetch(`/api/mercadolivre/contas/${accountId}/testar`)
        .then(response => response.json())
        .then(data => {
            if (data.sucesso && data.autenticada) {
                mostrarMensagem(`✅ Conta funcionando! Usuário: ${data.nickname}`, 'success');
            } else {
                mostrarMensagem(`❌ Problema: ${data.erro}`, 'error');
            }
        });
}

function removerConta(accountId) {
    if (!confirm('Remover esta conta?')) return;
    
    fetch(`/api/mercadolivre/contas/${accountId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem('Conta removida!', 'success');
            carregarContas();
        } else {
            mostrarMensagem('Erro: ' + data.erro, 'error');
        }
    });
}

function trocarContaConsulta(accountId) {
    selecionarConta(accountId);
}

// =========================================
// INICIALIZAÇÃO
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando sistema com paginação e exportação direta...');
    
    // Configurar estado inicial
    const tableLoading = document.getElementById('tableLoading');
    const emptyState = document.getElementById('emptyState');
    const ordersContainer = document.getElementById('ordersContainer');
    const paginacaoContainer = document.getElementById('paginacaoContainer');
    
    if (tableLoading) tableLoading.classList.add('hidden');
    if (emptyState) emptyState.classList.remove('hidden');
    if (ordersContainer) ordersContainer.classList.add('hidden');
    if (paginacaoContainer) paginacaoContainer.style.display = 'none';
    
    // Configurar toggle
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleFilters);
    }
    
    // Inicializar filtros
    inicializarFiltros();
    
    // Enter no campo de busca
    const mlbsInput = document.getElementById('mlbs');
    if (mlbsInput) {
        mlbsInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarMLBs();
            }
        });
    }
    
    // Upload de arquivo
    const fileUpload = document.getElementById('fileUpload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
            if (e.target.files[0]) {
                processarArquivoUpload(e.target.files[0]);
            }
        });
    }
    
    // Verificar configuração
    verificarConfiguracao();
    
    console.log('Sistema inicializado com sucesso!');
});

// =========================================
// FECHAR MODAIS AO CLICAR FORA
// =========================================

window.onclick = function(event) {
    const modals = [
        'configModal',
        'modalDetalhesMLB',
        'modalManufacturing',
        'modalProgresso',
        'modalPlanilha'
    ];
    
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
};