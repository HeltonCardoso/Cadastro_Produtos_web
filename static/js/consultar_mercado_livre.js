// static/js/consultar_mercado_livre.js - VERSÃO COMPLETA E CORRIGIDA

// =========================================
// VARIÁVEIS GLOBAIS
// =========================================
let ultimosResultados = [];
let dadosPlanilha = [];
let filtrosAtivos = {};
let isLoading = false;
let mlbSelecionado = null;
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
                if (data.configurado) {
                    statusElement.innerHTML = 'Mercado Livre: <span class="badge bg-success">Configurado</span>';
                } else {
                    statusElement.innerHTML = 'Mercado Livre: <span class="badge bg-warning">Não configurado</span>';
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

    // Primeiro salva a configuração
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
            // Se tem tokens, faz a autenticação
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
        
        // Validar formato MLB
        mlbs = mlbs.map(mlb => {
            if (!mlb.toUpperCase().startsWith('MLB')) {
                return 'MLB' + mlb.replace(/[^0-9]/g, '');
            }
            return mlb.toUpperCase();
        });
    }
    
    // Mostrar loading CORRETAMENTE
    mostrarLoading(true);
    limparResultados(true); // Passa true para manter o container visível
    
    // Fazer requisição
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
        mostrarLoading(false); // Esconde loading em caso de erro
    });
}

function processarResultadoBusca(data) {
    if (!data.sucesso) {
        mostrarErro(data.erro || 'Erro desconhecido na busca');
        return;
    }
    
    // Salva os resultados globalmente
    ultimosResultados = data.resultados || [];
    
    // Mostrar/ocultar botão de exportação
    const btnExportar = document.getElementById('btnExportar');
    if (ultimosResultados.length > 0) {
        btnExportar.style.display = 'inline-block';
    } else {
        btnExportar.style.display = 'none';
    }
    
    // Mostrar estatísticas
    mostrarEstatisticas(data);
    
    // Aplicar filtros se houver
    if (Object.keys(filtrosAtivos).length > 0) {
        aplicarFiltros();
    } else {
        // Mostrar resultados sem filtros
        mostrarResultados(ultimosResultados);
    }
}

function mostrarEstatisticas(data) {
    const statsDiv = document.getElementById('stats');
    
    let totalEncontrado = data.total_encontrado || 0;
    let totalNaoEncontrado = data.total_nao_encontrado || 0;
    let totalProcessados = data.resultados ? data.resultados.length : 0;
    
    // Ajusta para mostrar filtrados se aplicável
    if (Object.keys(filtrosAtivos).length > 0 && ultimosResultados.length > 0) {
        const resultadosFiltrados = aplicarFiltrosEmMemoria(ultimosResultados);
        statsDiv.innerHTML = `
            <i class="fas fa-chart-bar"></i>
            <strong>Estatísticas:</strong>
            ${resultadosFiltrados.length} de ${totalEncontrado} encontrados (filtrados) • 
            ${totalNaoEncontrado} não encontrados • 
            ${totalProcessados} processados • 
            ${new Date(data.timestamp).toLocaleTimeString()}
        `;
    } else {
        statsDiv.innerHTML = `
            <i class="fas fa-chart-bar"></i>
            <strong>Estatísticas:</strong>
            ${totalEncontrado} encontrados • 
            ${totalNaoEncontrado} não encontrados • 
            ${totalProcessados} processados • 
            ${new Date(data.timestamp).toLocaleTimeString()}
        `;
    }
    
    statsDiv.classList.remove('hidden');
}

function limparFiltros() {
    console.log('Limpando todos os filtros');
    
    // Limpa filtros ativos
    filtrosAtivos = {};
    
    // Reseta todos os selects
    document.querySelectorAll('.filter-select').forEach(select => {
        select.value = 'todos';
    });
    
    // Atualiza badges
    atualizarBadgesFiltrosAtivos();
    
    // Mostra todos os resultados se houver
    if (ultimosResultados.length > 0) {
        mostrarResultados(ultimosResultados);
        
        // Atualiza estatísticas
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

function mostrarResultados(resultados) {
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    const tableBody = document.getElementById('ordersTableBody');
    const tableLoading = document.getElementById('tableLoading');
    
    if (!resultados || resultados.length === 0) {
        // Esconde loading e container, mostra estado vazio
        mostrarLoading(false);
        ordersContainer.classList.add('hidden');
        emptyState.classList.remove('hidden');
        
        // Mensagem específica para quando há filtros ativos
        if (Object.keys(filtrosAtivos).length > 0) {
            emptyState.innerHTML = `
                <i class="fas fa-filter"></i>
                <h3>Nenhum resultado encontrado com os filtros aplicados</h3>
                <p>Nenhum anúncio corresponde aos critérios de filtro selecionados.</p>
                <button class="btn btn-outline-secondary mt-3" onclick="limparFiltros()">
                    <i class="fas fa-times"></i> Limpar Filtros
                </button>
            `;
        }
        return;
    }
    
    // Garante que o container está visível e o loading escondido
    ordersContainer.classList.remove('hidden');
    emptyState.classList.add('hidden');
    
    // Esconde o loading
    if (tableLoading) {
        tableLoading.classList.add('hidden');
    }
    
    // Limpa tabela
    if (tableBody) {
        tableBody.innerHTML = '';
    }
    
    // Preenche resultados
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
// FUNÇÕES DE ANÁLISE DE ENVIO
// =========================================

function analisarEnvioManufacturing() {
    const mlbsText = document.getElementById('mlbs').value.trim();
    
    if (!mlbsText) {
        mostrarMensagem('Digite os códigos MLB para análise', 'error');
        return;
    }
    
    const mlbs = mlbsText.split(/[\n,]+/).map(mlb => mlb.trim()).filter(mlb => mlb);
    
    if (mlbs.length === 0) {
        mostrarMensagem('Nenhum MLB válido encontrado', 'error');
        return;
    }
    
    mostrarLoading(true);
    limparResultados();
    
    fetch('/api/mercadolivre/analisar-envio-manufacturing', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            mlbs: mlbs,
            tipo_busca: 'mlbs'
        })
    })
    .then(response => response.json())
    .then(data => {
        processarAnaliseEnvio(data);
    })
    .catch(error => {
        console.error('Erro na análise:', error);
        mostrarErro('Erro na análise: ' + error.message);
    })
    .finally(() => {
        mostrarLoading(false);
    });
}

function processarAnaliseEnvio(data) {
    if (!data.sucesso) {
        mostrarErro(data.erro || 'Erro desconhecido na análise');
        return;
    }
    
    const statsDiv = document.getElementById('stats');
    const estatisticas = data.estatisticas;
    
    // Salva os resultados
    ultimosResultados = data.resultados || [];
    
    let html = `
        <i class="fas fa-shipping-fast"></i>
        <strong>Análise de Envio:</strong>
        ${estatisticas.total_analisado} analisados • 
        ${estatisticas.me2} ME2 • 
        ${estatisticas.me1} ME1 • 
        ${estatisticas.com_manufacturing} com manufacturing • 
        ${estatisticas.sem_manufacturing} sem manufacturing
    `;
    
    statsDiv.innerHTML = html;
    statsDiv.classList.remove('hidden');
    
    // Aplicar filtros se houver
    if (Object.keys(filtrosAtivos).length > 0) {
        aplicarFiltros();
    } else {
        // Mostrar resultados sem filtros
        mostrarResultados(ultimosResultados);
    }
}

// =========================================
// FUNÇÃO DE EXPORTAR PARA EXCEL
// =========================================

function exportarParaExcel() {
    if (!ultimosResultados || ultimosResultados.length === 0) {
        mostrarMensagem('Nenhum resultado para exportar', 'error');
        return;
    }

    mostrarLoading(true);

    // Preparar dados para exportação (com filtros aplicados)
    let resultadosParaExportar = ultimosResultados;
    
    // Se há filtros ativos, aplica-os na exportação
    if (Object.keys(filtrosAtivos).length > 0) {
        resultadosParaExportar = aplicarFiltrosEmMemoria(ultimosResultados);
        if (resultadosParaExportar.length === 0) {
            mostrarMensagem('Nenhum resultado após aplicar os filtros', 'error');
            mostrarLoading(false);
            return;
        }
    }

    const dadosExportacao = [];
    
    resultadosParaExportar.forEach(item => {
        if (item.error || item.status === 'error') {
            dadosExportacao.push({
                'MLB Principal': item.id || 'N/A',
                'MLB Variação': '-',
                'Tipo': 'Principal (Erro)',
                'SKU': '-',
                'Título': '-',
                'Preço': '-',
                'Estoque': '-',
                'Modo Envio': '-',
                'Prazo Fabricação': '-',
                'Status': 'Erro',
                'Frete Grátis': '-',
                'Erro': item.error || 'Erro desconhecido',
                'Catálogo': '-',
                'Variações': '-',
                'Quantidade Variações': 0,
                'Tipo Anúncio': '-',
                'Tipo Premium': '-',
                'ID Catálogo': '-',
                'Condição': '-',
                'Vendidos': 0,
                'Categoria': '-',
                'Data Criação': '-',
                'Link': '-'
            });
        } else {
            // Item principal
            dadosExportacao.push({
                'MLB Principal': item.id || 'N/A',
                'MLB Variação': '-',
                'Tipo': 'Principal',
                'SKU': item.meu_sku || 'N/A',
                'Título': item.title || 'N/A',
                'Preço': item.price ? `R$ ${item.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}` : 'R$ 0,00',
                'Estoque': item.available_quantity || 0,
                'Modo Envio': item.shipping_mode || 'N/A',
                'Prazo Fabricação': item.manufacturing_time || 'N/A',
                'Status': item.status || 'N/A',
                'Frete Grátis': item.frete_gratis || 'Não',
                'Erro': '',
                'Catálogo': item.eh_catalogo || 'Não',
                'Variações': item.tem_variacoes || 'Não',
                'Quantidade Variações': item.quantidade_variacoes || 0,
                'Tipo Anúncio': item.tipo_anuncio || 'N/A',
                'Tipo Premium': item.tipo_premium || 'Standard',
                'ID Catálogo': item.catalog_product_id || 'N/A',
                'Condição': item.condition || 'N/A',
                'Vendidos': item.sold_quantity || 0,
                'Categoria': item.category_id || 'N/A',
                'Data Criação': item.date_created || 'N/A',
                'Link': item.permalink || 'N/A'
            });

            // Adicionar variações se existirem
            if (item.variacoes_detalhes && item.variacoes_detalhes.length > 0) {
                item.variacoes_detalhes.forEach(variacao => {
                    const atributos = variacao.attribute_combinations.map(attr => 
                        `${attr.name}: ${attr.value_name}`
                    ).join('; ');
                    
                    dadosExportacao.push({
                        'MLB Principal': item.id || 'N/A',
                        'MLB Variação': variacao.id || 'N/A',
                        'Tipo': 'Variação',
                        'SKU': variacao.seller_custom_field || 'N/A',
                        'Título': `${item.title} - ${atributos}`,
                        'Preço': variacao.price ? `R$ ${variacao.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}` : 'R$ 0,00',
                        'Estoque': variacao.available_quantity || 0,
                        'Modo Envio': item.shipping_mode || 'N/A',
                        'Prazo Fabricação': variacao.manufacturing_time || 'N/A',
                        'Status': item.status || 'N/A',
                        'Frete Grátis': item.frete_gratis || 'Não',
                        'Erro': '',
                        'Catálogo': 'Variação',
                        'Variações': 'Sim',
                        'Quantidade Variações': '1',
                        'Tipo Anúncio': 'Variação',
                        'Tipo Premium': 'Variação',
                        'ID Catálogo': variacao.catalog_product_id || 'N/A',
                        'Condição': item.condition || 'N/A',
                        'Vendidos': variacao.sold_quantity || 0,
                        'Categoria': item.category_id || 'N/A',
                        'Data Criação': item.date_created || 'N/A',
                        'Link': item.permalink || 'N/A',
                        'Atributos Variação': atributos
                    });
                });
            }
        }
    });

    // Calcular estatísticas
    const totalItens = resultadosParaExportar.length;
    const totalEncontrado = resultadosParaExportar.filter(item => !item.error && item.status !== 'error').length;
    const totalNaoEncontrado = totalItens - totalEncontrado;
    const totalPrincipais = dadosExportacao.filter(item => item.Tipo === 'Principal').length;
    const totalVariacoes = dadosExportacao.filter(item => item.Tipo === 'Variação').length;

    // Fazer requisição para exportação
    fetch('/api/mercadolivre/exportar-excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            dados: dadosExportacao,
            total_encontrado: totalEncontrado,
            total_nao_encontrado: totalNaoEncontrado,
            total_principais: totalPrincipais,
            total_variações: totalVariacoes,
            total_geral: dadosExportacao.length,
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
        // Criar URL para download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Nome do arquivo com filtros se aplicável
        let nomeArquivo = 'consulta_mlb';
        if (Object.keys(filtrosAtivos).length > 0) {
            nomeArquivo += '_filtrado';
        }
        nomeArquivo += `_${new Date().toISOString().slice(0, 10)}_${new Date().getHours()}${new Date().getMinutes()}.xlsx`;
        
        a.download = nomeArquivo;
        
        document.body.appendChild(a);
        a.click();
        
        // Limpar
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        mostrarMensagem(`Exportação concluída! ${totalPrincipais} principais + ${totalVariacoes} variações = ${dadosExportacao.length} itens.`, 'success');
    })
    .catch(error => {
        console.error('Erro na exportação:', error);
        mostrarErro('Erro ao exportar para Excel: ' + error.message);
    })
    .finally(() => {
        mostrarLoading(false);
    });
}

let contaPendenteTokens = null;

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
    // Atualiza lista de contas
    renderizarContas(data.contas, data.conta_atual);
    
    // Atualiza status na barra inferior
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
            <button class="btn btn-sm btn-outline-secondary ms-2" onclick="trocarContaRapido()">
                <i class="fas fa-sync-alt"></i> Trocar
            </button>
        `;
    } else {
        statusElement.innerHTML = `
            Mercado Livre: 
            <span class="badge bg-warning">${contaAtual.name} (pendente)</span>
            <button class="btn btn-sm btn-outline-warning ms-2" onclick="completarAutenticacao('${contaAtual.id}')">
                <i class="fas fa-key"></i> Completar
            </button>
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
                ${!isAtual ? `
                    <button class="btn btn-sm btn-outline-primary" onclick="selecionarConta('${conta.id}')">
                        <i class="fas fa-play-circle"></i> Usar
                    </button>
                ` : ''}
                
                ${conta.has_token ? `
                    <button class="btn btn-sm btn-outline-info" onclick="testarConta('${conta.id}')">
                        <i class="fas fa-vial"></i> Testar
                    </button>
                ` : `
                    <button class="btn btn-sm btn-outline-success" onclick="completarAutenticacao('${conta.id}')">
                        <i class="fas fa-key"></i> Completar Auth
                    </button>
                `}
                
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

// FUNÇÃO PRINCIPAL: Adicionar nova conta
function abrirAdicionarConta() {
    document.getElementById('adicionarContaSection').innerHTML = `
        <h5><i class="fas fa-plus-circle"></i> Adicionar Nova Conta</h5>
        
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            <strong>O sistema tentará obter tokens automaticamente!</strong><br>
            Apenas forneça App ID e Secret Key. O sistema tentará autenticar automaticamente.
        </div>
        
        <div class="mb-3">
            <label>Nome da Conta</label>
            <input type="text" id="novaContaNome" class="form-control" 
                   placeholder="Ex: Minha Segunda Loja" required>
        </div>
        
        <div class="mb-3">
            <label>App ID (Client ID)</label>
            <input type="text" id="novaContaAppId" class="form-control" 
                   placeholder="Seu App ID do Mercado Livre" required>
        </div>
        
        <div class="mb-3">
            <label>Secret Key (Client Secret)</label>
            <input type="password" id="novaContaSecretKey" class="form-control" 
                   placeholder="Sua Secret Key" required>
        </div>
        
        <div class="d-flex gap-2">
            <button class="btn btn-secondary" onclick="cancelarAdicionar()">
                <i class="fas fa-times"></i> Cancelar
            </button>
            <button class="btn btn-primary" onclick="adicionarContaAutomatica()">
                <i class="fas fa-magic"></i> Adicionar e Autenticar
            </button>
        </div>
    `;
    
    document.getElementById('adicionarContaSection').style.display = 'block';
    document.getElementById('authSection').style.display = 'none';
}

function adicionarContaAutomatica() {
    const nome = document.getElementById('novaContaNome').value.trim();
    const appId = document.getElementById('novaContaAppId').value.trim();
    const secretKey = document.getElementById('novaContaSecretKey').value.trim();
    
    if (!nome || !appId || !secretKey) {
        mostrarMensagem('Preencha todos os campos', 'error');
        return;
    }
    
    mostrarMensagem('Adicionando conta e tentando autenticar automaticamente...', 'info');
    
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
            if (data.autenticada_automaticamente) {
                mostrarMensagem('🎉 Conta adicionada e autenticada automaticamente!', 'success');
                document.getElementById('adicionarContaSection').style.display = 'none';
                carregarContas();
            } else {
                // Autenticação automática falhou, oferece completar manualmente
                mostrarMensagem('Conta criada! Mas precisamos completar a autenticação manualmente.', 'warning');
                contaPendenteTokens = data.account_id;
                mostrarModalCompletarAuth();
            }
        } else {
            mostrarMensagem('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarMensagem('Erro: ' + error.message, 'error');
    });
}

function mostrarModalCompletarAuth() {
    document.getElementById('authSection').innerHTML = `
        <h5><i class="fas fa-key"></i> Completar Autenticação</h5>
        
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>A autenticação automática não funcionou, mas não se preocupe!</strong><br>
            Siga estes passos para obter os tokens manualmente:
        </div>
        
        <div class="auth-steps mb-3">
            <ol>
                <li>Acesse: <a href="https://developers.mercadolivre.com.br/devcenter" target="_blank">Mercado Livre DevCenter</a></li>
                <li>Clique em "Minhas aplicações"</li>
                <li>Selecione sua aplicação</li>
                <li>Vá na aba "Test"</li>
                <li>Clique em "Obtenha seu token de teste"</li>
                <li>Copie o <strong>Access Token</strong> e <strong>Refresh Token</strong></li>
            </ol>
        </div>
        
        <div class="mb-3">
            <label><i class="fas fa-lock"></i> Access Token</label>
            <input type="text" id="manualAccessToken" class="form-control" 
                   placeholder="APP_USR-..." style="font-family: monospace;">
        </div>
        
        <div class="mb-3">
            <label><i class="fas fa-redo"></i> Refresh Token</label>
            <input type="text" id="manualRefreshToken" class="form-control" 
                   placeholder="TG-..." style="font-family: monospace;">
        </div>
        
        <div class="d-flex gap-2">
            <button class="btn btn-secondary" onclick="cancelarAuthManual()">
                <i class="fas fa-times"></i> Cancelar
            </button>
            <button class="btn btn-success" onclick="salvarTokensManuais()">
                <i class="fas fa-save"></i> Salvar Tokens
            </button>
        </div>
    `;
    
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('adicionarContaSection').style.display = 'none';
}

function salvarTokensManuais() {
    if (!contaPendenteTokens) return;
    
    const accessToken = document.getElementById('manualAccessToken').value.trim();
    const refreshToken = document.getElementById('manualRefreshToken').value.trim();
    
    if (!accessToken || !refreshToken) {
        mostrarMensagem('Preencha ambos os tokens', 'error');
        return;
    }
    
    fetch(`/api/mercadolivre/contas/${contaPendenteTokens}/adicionar-tokens-manual`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            access_token: accessToken,
            refresh_token: refreshToken
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem('✅ Tokens salvos com sucesso! Conta pronta para uso.', 'success');
            document.getElementById('authSection').style.display = 'none';
            contaPendenteTokens = null;
            carregarContas();
        } else {
            mostrarMensagem('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarMensagem('Erro: ' + error.message, 'error');
    });
}

// Funções auxiliares
function completarAutenticacao(accountId) {
    contaPendenteTokens = accountId;
    mostrarModalCompletarAuth();
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
                mostrarMensagem(`❌ Problema na conta: ${data.erro}`, 'error');
            }
        });
}

function removerConta(accountId) {
    if (!confirm('Tem certeza que deseja remover esta conta?')) return;
    
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

function cancelarAdicionar() {
    document.getElementById('adicionarContaSection').style.display = 'none';
}

function cancelarAuthManual() {
    document.getElementById('authSection').style.display = 'none';
    contaPendenteTokens = null;
}

// Trocar conta rapidamente (modal rápido)
function trocarContaRapido() {
    fetch('/api/mercadolivre/contas')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso && data.contas.length > 1) {
                let options = '';
                data.contas.forEach(conta => {
                    const isCurrent = conta.id === data.conta_atual;
                    options += `<option value="${conta.id}" ${isCurrent ? 'selected' : ''}>
                        ${conta.name} ${conta.has_token ? '✓' : '⚠️'} ${conta.nickname ? `(${conta.nickname})` : ''}
                    </option>`;
                });
                
                const contaEscolhida = prompt(
                    `Trocar conta atual:\n\n${data.contas.map(c => 
                        `${c.id === data.conta_atual ? '→ ' : '  '}${c.name} ${c.nickname ? `(${c.nickname})` : ''}`
                    ).join('\n')}\n\nDigite o ID da conta:`,
                    data.conta_atual
                );
                
                if (contaEscolhida && contaEscolhida !== data.conta_atual) {
                    selecionarConta(contaEscolhida);
                }
            } else {
                mostrarMensagem('Apenas uma conta disponível', 'info');
            }
        });
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Carrega contas ao abrir modal
    const configModal = document.getElementById('configModal');
    if (configModal) {
        configModal.addEventListener('shown.bs.modal', function() {
            carregarContas();
        });
    }
    
    // Carrega contas periodicamente
    setInterval(carregarContas, 60000); // Atualiza a cada 1 minuto
});


// =========================================
// TROCA DE CONTA NA PÁGINA DE CONSULTA
// =========================================

function trocarContaConsulta(accountId) {
    fetch(`/api/mercadolivre/contas/${accountId}/selecionar`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem(`Conta alterada para a selecionada`, 'success');
            
            // Recarrega a página para refletir a mudança
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            mostrarMensagem(`Erro: ${data.erro}`, 'error');
        }
    })
    .catch(error => {
        mostrarMensagem(`Erro: ${error.message}`, 'error');
    });
}

function toggleConfigSection() {
    // Em vez de abrir modal local, redireciona para página de configurações
    window.location.href = '/configuracoes/tokens#mercadolivre';
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
    
    // Mostrar loading
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
            
            // Atualiza a linha na tabela se estiver visível
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
        // Restaurar botão
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

function atualizarLinhaTabela(mlbId, novosDias) {
    // Encontra a linha na tabela e atualiza o badge
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

// =========================================
// FUNÇÕES PARA GERENCIAMENTO DE FILTROS
// =========================================
function inicializarFiltros() {
    console.log('Inicializando filtros...');
    
    // Configura eventos para todos os selects de filtro
    const filtros = ['tipoBusca', 'filtroEnvio', 'filtroManufacturing', 'filtroStatus'];
    
    filtros.forEach(filtroId => {
        const select = document.getElementById(filtroId);
        if (select) {
            // Remove event listeners antigos
            const newSelect = select.cloneNode(true);
            select.parentNode.replaceChild(newSelect, select);
            
            // Adiciona novo event listener
            document.getElementById(filtroId).addEventListener('change', function() {
                const valor = this.value;
                const tipo = this.id;
                
                console.log(`Filtro alterado: ${tipo} = ${valor}`);
                atualizarFiltroAtivo(tipo, valor);
                
                // Aplica os filtros imediatamente
                if (ultimosResultados.length > 0) {
                    aplicarFiltros();
                }
            });
        }
    });
    
    console.log('Filtros inicializados:', filtros);
}


function toggleFilters() {
    const filtersHeader = document.getElementById('filtersHeader');
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    
    if (!filtersHeader || !toggleBtn) {
        console.error('Elementos do toggle não encontrados');
        return;
    }
    
    // Alterna entre recolhido e expandido
    const isCollapsed = filtersHeader.classList.contains('collapsed');
    const icon = toggleBtn.querySelector('i');
    const text = toggleBtn.querySelector('span');
    
    if (isCollapsed) {
        // EXPANDE os filtros
        filtersHeader.classList.remove('collapsed');
        if (icon) icon.className = 'fas fa-chevron-up';
        if (text) text.textContent = 'Recolher Filtros';
    } else {
        // RECOLHE os filtros
        filtersHeader.classList.add('collapsed');
        if (icon) icon.className = 'fas fa-chevron-down';
        if (text) text.textContent = 'Expandir Filtros';
    }
    
    console.log('Filtros ' + (isCollapsed ? 'expandidos' : 'recolhidos'));
}

function atualizarFiltroAtivo(tipo, valor) {
    console.log(`Atualizando filtro: ${tipo} = ${valor}`);
    
    if (valor === 'todos' || valor === '') {
        // Remove o filtro se for "todos" ou vazio
        delete filtrosAtivos[tipo];
    } else {
        // Adiciona/atualiza o filtro
        filtrosAtivos[tipo] = valor;
    }
    
    console.log('Filtros ativos:', filtrosAtivos);
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
            case 'envio':
                label = 'Envio:';
                displayValor = valor === 'me2' ? 'Apenas ME2' : 'Apenas ME1';
                break;
            case 'manufacturing':
                label = 'Manufacturing:';
                displayValor = valor === 'com' ? 'Com prazo' : 'Sem prazo';
                break;
            case 'status':
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
    console.log(`Removendo filtro: ${tipo}`);
    
    delete filtrosAtivos[tipo];
    
    // Reseta o select correspondente
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
    
    // Reaplica filtros se houver resultados
    if (ultimosResultados.length > 0) {
        aplicarFiltros();
    }
}

function aplicarFiltros() {
    console.log('Aplicando filtros...', filtrosAtivos);
    
    if (Object.keys(filtrosAtivos).length === 0) {
        // Se não há filtros, mostra todos os resultados
        console.log('Nenhum filtro ativo, mostrando todos os resultados');
        mostrarResultados(ultimosResultados);
        
        // Atualiza estatísticas
        if (ultimosResultados.length > 0) {
            const statsDiv = document.getElementById('stats');
            if (statsDiv && !statsDiv.classList.contains('hidden')) {
                const totalEncontrado = ultimosResultados.filter(item => !item.error && item.status !== 'error').length;
                statsDiv.innerHTML = statsDiv.innerHTML.replace(
                    /(\d+) de \d+ encontrados \(filtrados\)/,
                    `${totalEncontrado} encontrados`
                );
            }
        }
        return;
    }
    
    const resultadosFiltrados = aplicarFiltrosEmMemoria(ultimosResultados);
    console.log(`Resultados após filtro: ${resultadosFiltrados.length} de ${ultimosResultados.length}`);
    
    mostrarResultados(resultadosFiltrados);
    
    // Atualiza estatísticas
    const statsDiv = document.getElementById('stats');
    if (statsDiv && !statsDiv.classList.contains('hidden')) {
        const totalEncontrado = ultimosResultados.filter(item => !item.error && item.status !== 'error').length;
        const totalFiltrado = resultadosFiltrados.filter(item => !item.error && item.status !== 'error').length;
        
        // Atualiza o texto das estatísticas
        const htmlAtual = statsDiv.innerHTML;
        const novaHtml = htmlAtual.replace(
            /(\d+) (encontrados|de \d+ encontrados)/,
            `${totalFiltrado} de ${totalEncontrado} encontrados (filtrados)`
        );
        statsDiv.innerHTML = novaHtml;
    }
}

function aplicarFiltrosEmMemoria(resultados) {
    if (Object.keys(filtrosAtivos).length === 0 || !resultados || resultados.length === 0) {
        return resultados || [];
    }
    
    console.log('Aplicando filtros em memória:', filtrosAtivos);
    
    return resultados.filter(item => {
        // Pula itens com erro
        if (item.error || item.status === 'error') return false;
        
        // Verifica cada filtro
        for (const [tipo, valor] of Object.entries(filtrosAtivos)) {
            let passaFiltro = true;
            
            switch(tipo) {
                case 'filtroEnvio':
                    // Filtro ME2/ME1
                    if (valor === 'me2') {
                        passaFiltro = item.shipping_mode === 'me2';
                    } else if (valor === 'me1') {
                        passaFiltro = item.shipping_mode === 'me1';
                    }
                    break;
                    
                case 'filtroManufacturing':
                    // Filtro com/sem prazo
                    if (valor === 'com') {
                        // Tem manufacturing time
                        passaFiltro = item.manufacturing_time && 
                                     item.manufacturing_time !== 'N/A' && 
                                     item.manufacturing_time !== '0' && 
                                     item.manufacturing_time !== 0 &&
                                     item.manufacturing_time !== '';
                    } else if (valor === 'sem') {
                        // Não tem manufacturing time
                        passaFiltro = !item.manufacturing_time || 
                                     item.manufacturing_time === 'N/A' || 
                                     item.manufacturing_time === '0' || 
                                     item.manufacturing_time === 0 ||
                                     item.manufacturing_time === '';
                    }
                    break;
                    
                case 'filtroStatus':
                    // Filtro status
                    if (valor !== 'todos') {
                        passaFiltro = item.status === valor;
                    }
                    break;
                    
                case 'tipoBusca':
                    // Este filtro é aplicado na busca, não no resultado
                    passaFiltro = true;
                    break;
                    
                default:
                    passaFiltro = true;
            }
            
            // Se não passar em um filtro, rejeita o item
            if (!passaFiltro) {
                console.log(`Item ${item.id} rejeitado pelo filtro ${tipo}=${valor}`);
                return false;
            }
        }
        
        return true;
    });
}

// =========================================
// SISTEMA DE PROGRESSO DE ATUALIZAÇÃO
// =========================================

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
    
    // Prepara as atualizações
    const atualizacoes = mlbs.map(mlb => ({
        mlb: mlb.toUpperCase().startsWith('MLB') ? mlb.toUpperCase() : 'MLB' + mlb,
        dias: parseInt(dias)
    }));
    
    // MOSTRA O MODAL PRIMEIRO
    abrirModalProgresso(atualizacoes);
}

function abrirModalProgresso(atualizacoes) {
    // Prepara a interface
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
    
    // Abre o modal
    document.getElementById('modalProgresso').style.display = 'block';
    
    // Inicia o processamento APÓS o modal estar visível
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
    
    // Inicia o processamento
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
    
    // SEMPRE mostrar MLB atual sendo processado
    document.getElementById('currentMlb').textContent = atualizacao.mlb;
    document.getElementById('currentStatus').textContent = 'Processando...';
    document.getElementById('currentStatus').className = 'status-badge status-processing';
    
    try {
        // Faz a requisição para a API
        const response = await fetch('/api/mercadolivre/atualizar-manufacturing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mlb: atualizacao.mlb,
                dias: atualizacao.dias
            })
        });
        
        const data = await response.json();
        
        // Atualiza estatísticas
        processoAtualizacao.processados++;
        
        if (data.sucesso) {
            processoAtualizacao.sucesso++;
            // SEMPRE mostrar log de sucesso
            adicionarLog(`✅ ${atualizacao.mlb} - ${atualizacao.dias} dias`, 'log-success');
            document.getElementById('currentStatus').textContent = 'Sucesso';
            document.getElementById('currentStatus').className = 'status-badge status-success';
        } else {
            processoAtualizacao.erros++;
            // SEMPRE mostrar log de erro
            adicionarLog(`❌ ${atualizacao.mlb} - Erro: ${data.erro}`, 'log-error');
            document.getElementById('currentStatus').textContent = 'Erro';
            document.getElementById('currentStatus').className = 'status-badge status-error';
        }
        
        // SEMPRE atualizar barra de progresso
        atualizarBarraProgresso();
        
        // Pequeno delay para evitar rate limit (0.5 segundos)
        setTimeout(processarProximaAtualizacao, 500);
        
    } catch (error) {
        processoAtualizacao.processados++;
        processoAtualizacao.erros++;
        // SEMPRE mostrar log de erro de conexão
        adicionarLog(`❌ ${atualizacao.mlb} - Erro: ${error.message}`, 'log-error');
        document.getElementById('currentStatus').textContent = 'Erro';
        document.getElementById('currentStatus').className = 'status-badge status-error';
        
        // SEMPRE atualizar barra mesmo em caso de erro
        atualizarBarraProgresso();
        
        setTimeout(processarProximaAtualizacao, 500);
    }
}

function atualizarBarraProgresso() {
    const percentual = (processoAtualizacao.processados / processoAtualizacao.total) * 100;
    const progresso = Math.round(percentual);
    
    // Atualiza barra visual
    document.getElementById('progressFill').style.width = percentual + '%';
    document.getElementById('progressText').textContent = 
        `${progresso}% (${processoAtualizacao.processados}/${processoAtualizacao.total})`;
    
    // Atualiza estatísticas em tempo real
    document.getElementById('progressSucesso').textContent = processoAtualizacao.sucesso;
    document.getElementById('progressErros').textContent = processoAtualizacao.erros;
    document.getElementById('progressRestantes').textContent = processoAtualizacao.total - processoAtualizacao.processados;
    
    // Calcula velocidade e tempo restante
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
    
    // Atualiza visual da barra conforme o estado
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
    
    // Auto-scroll para o final
    logContainer.scrollTop = logContainer.scrollHeight;
}

function cancelarAtualizacao() {
    if (confirm('Deseja cancelar a atualização?')) {
        processoAtualizacao.cancelar = true;
        processoAtualizacao.ativo = false;
        adicionarLog('⏹️ Atualização cancelada pelo usuário', 'log-warning');
        document.getElementById('btnCancelar').style.display = 'none';
        document.getElementById('btnConcluir').style.display = 'block';
    }
}

function finalizarProcesso() {
    processoAtualizacao.ativo = false;
    
    document.getElementById('btnCancelar').style.display = 'none';
    document.getElementById('btnConcluir').style.display = 'block';
    
    // Mensagem final no log
    if (processoAtualizacao.cancelar) {
        adicionarLog('📊 Processo interrompido pelo usuário', 'log-warning');
    } else {
        adicionarLog(`🎯 Processo concluído: ${processoAtualizacao.sucesso} sucesso, ${processoAtualizacao.erros} erros`, 'log-info');
        
        // Mostra mensagem de resumo
        setTimeout(() => {
            mostrarMensagem(
                `Atualização concluída: ${processoAtualizacao.sucesso} sucesso, ${processoAtualizacao.erros} erros`,
                processoAtualizacao.erros === 0 ? 'success' : 'warning'
            );
        }, 500);
    }
}

function fecharModalProgresso() {
    document.getElementById('modalProgresso').style.display = 'none';
    processoAtualizacao.ativo = false;
    
    // Se o processo foi concluído com sucesso, recarrega os dados
    if (processoAtualizacao.sucesso > 0 && ultimosResultados.length > 0) {
        setTimeout(() => buscarMLBs(), 1000);
    }
}

// =========================================
// FUNÇÕES DE PLANILHA
// =========================================

function baixarModeloPlanilha() {
    console.log('Baixando modelo...');
    
    try {
        // Criar workbook
        const workbook = XLSX.utils.book_new();
        
        // Dados do modelo
        const dados = [
            ['MLB', 'DIAS', 'OBSERVAÇÃO'],
            ['MLB1234567890', '5', '← Prazo de 5 dias'],
            ['MLB9876543210', '10', '← Prazo de 10 dias'],
            ['MLB5555555555', '0', '← Remove o prazo (0 dias)'],
            ['', '', ''],
            ['INSTRUÇÕES:', '', ''],
            ['• MLB: Código do anúncio no Mercado Livre', '', ''],
            ['• DIAS: Prazo de fabricação em dias (0 para remover)', '', ''],
            ['• Mantenha o cabeçalho MLB, DIAS', '', ''],
            ['• Pode usar apenas números no MLB (ex: 1234567890)', '', '']
        ];
        
        // Criar worksheet
        const worksheet = XLSX.utils.aoa_to_sheet(dados);
        
        // Ajustar largura das colunas
        worksheet['!cols'] = [
            { wch: 15 }, // MLB
            { wch: 8 },  // DIAS
            { wch: 30 }  // OBSERVAÇÃO
        ];
        
        // Adicionar worksheet ao workbook
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Modelo');
        
        // Gerar arquivo e fazer download
        XLSX.writeFile(workbook, 'modelo_atualizacao_prazo.xlsx');
        
        console.log('✅ Modelo baixado com sucesso');
        
    } catch (error) {
        console.error('❌ Erro ao baixar modelo:', error);
        mostrarMensagem('Erro ao baixar modelo: ' + error.message, 'error');
        
        // Fallback para CSV se XLSX falhar
        baixarModeloCSV();
    }
}

function baixarModeloCSV() {
    const modelo = [
        'MLB,DIAS',
        'MLB1234567890,5',
        'MLB9876543210,10', 
        'MLB5555555555,0'
    ].join('\n');
    
    const blob = new Blob([modelo], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'modelo_atualizacao_prazo.csv';
    link.click();
    
    URL.revokeObjectURL(url);
}

function abrirModalPlanilha() {
    console.log('Abrindo modal de planilha...');
    
    // Resetar o estado do modal
    document.getElementById('fileUpload').value = '';
    document.getElementById('previewSection').style.display = 'none';
    document.getElementById('btnProcessarPlanilha').disabled = true;
    document.getElementById('previewTableBody').innerHTML = '';
    document.getElementById('previewTotal').textContent = '0';
    dadosPlanilha = [];
    
    // Mostrar o modal
    document.getElementById('modalPlanilha').style.display = 'block';
}

function fecharModalPlanilha() {
    document.getElementById('modalPlanilha').style.display = 'none';
}

function processarArquivoUpload(file) {
    if (!file) {
        console.log('Nenhum arquivo selecionado');
        return;
    }

    const extensao = file.name.split('.').pop().toLowerCase();
    console.log('Processando arquivo:', file.name, 'Extensão:', extensao);
    
    if (!['xlsx', 'xls', 'csv'].includes(extensao)) {
        mostrarMensagem('Formato de arquivo não suportado. Use Excel (.xlsx, .xls) ou CSV.', 'error');
        return;
    }

    mostrarMensagem('Processando planilha...', 'info');

    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            console.log('Arquivo lido, processando...');
            
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
    
    reader.onerror = function(error) {
        console.error('Erro na leitura do arquivo:', error);
        mostrarMensagem('Erro ao ler arquivo', 'error');
    };
    
    if (extensao === 'csv') {
        reader.readAsText(file);
    } else {
        reader.readAsArrayBuffer(file);
    }
}

function processarExcel(data) {
    console.log('Processando Excel...');
    
    try {
        const workbook = XLSX.read(data, { type: 'array' });
        const primeiraPlanilha = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(primeiraPlanilha);
        
        console.log('Dados brutos do Excel:', jsonData);
        
        const dados = jsonData.map(linha => {
            // Tentar diferentes nomes de coluna
            const mlb = (linha.MLB || linha.mlb || linha['Código'] || linha.codigo || linha.MLB?.toString() || '').toString().toUpperCase().trim();
            const dias = parseInt(linha.DIAS || linha.dias || linha.Dias || linha.PRAZO || linha.prazo || linha.Prazo || 0);
            
            return { mlb, dias };
        }).filter(item => item.mlb && item.mlb !== 'MLB' && !isNaN(item.dias));
        
        console.log('Dados filtrados:', dados);
        exibirPreviaPlanilha(dados);
        
    } catch (error) {
        console.error('Erro ao processar Excel:', error);
        mostrarMensagem('Erro ao processar Excel: ' + error.message, 'error');
    }
}

function processarCSV(csvText) {
    console.log('Processando CSV...');
    
    const linhas = csvText.split('\n').filter(linha => linha.trim());
    const dados = [];
    
    // Encontrar índices das colunas
    const cabecalho = linhas[0].split(',').map(col => col.trim().toUpperCase().replace(/"/g, ''));
    const idxMLB = cabecalho.indexOf('MLB');
    const idxDIAS = cabecalho.indexOf('DIAS');
    
    console.log('Cabeçalho encontrado:', cabecalho);
    console.log('Índice MLB:', idxMLB, 'Índice DIAS:', idxDIAS);
    
    if (idxMLB === -1 || idxDIAS === -1) {
        mostrarMensagem('Colunas MLB e DIAS não encontradas no arquivo', 'error');
        return;
    }
    
    // Processar linhas de dados
    for (let i = 1; i < linhas.length; i++) {
        const colunas = linhas[i].split(',').map(col => col.trim().replace(/"/g, ''));
        
        if (colunas.length > Math.max(idxMLB, idxDIAS)) {
            const mlb = colunas[idxMLB];
            const dias = parseInt(colunas[idxDIAS]);
            
            if (mlb && !isNaN(dias)) {
                dados.push({ mlb, dias });
                console.log('MLB encontrado:', mlb, 'Dias:', dias);
            }
        }
    }
    
    console.log('Total de dados processados:', dados.length);
    exibirPreviaPlanilha(dados);
}

function exibirPreviaPlanilha(dados) {
    console.log('Exibindo prévia com', dados.length, 'itens');
    
    dadosPlanilha = dados.filter(item => item.mlb && !isNaN(item.dias));
    
    console.log('Dados válidos:', dadosPlanilha);
    
    if (dadosPlanilha.length === 0) {
        mostrarMensagem('Nenhum dado válido encontrado na planilha. Verifique as colunas MLB e DIAS.', 'error');
        return;
    }
    
    const tbody = document.getElementById('previewTableBody');
    tbody.innerHTML = '';
    
    dadosPlanilha.forEach((item, index) => {
        const isValid = validarMLB(item.mlb);
        const linha = `
            <tr class="${isValid ? 'preview-valid' : 'preview-invalid'}">
                <td>${item.mlb}</td>
                <td>${item.dias} dias</td>
                <td>${isValid ? '✅ Válido' : '❌ Formato inválido'}</td>
            </tr>
        `;
        tbody.innerHTML += linha;
    });
    
    document.getElementById('previewTotal').textContent = dadosPlanilha.length;
    document.getElementById('previewSection').style.display = 'block';
    document.getElementById('btnProcessarPlanilha').disabled = false;
    
    mostrarMensagem(`✅ ${dadosPlanilha.length} MLBs válidos encontrados na planilha`, 'success');
    console.log('Prévia exibida, botão habilitado');
}

function validarMLB(mlb) {
    if (!mlb) return false;
    
    const mlbStr = mlb.toString().toUpperCase().trim();
    
    // Aceita: MLB1234567890 ou apenas 1234567890
    const isValid = mlbStr.startsWith('MLB') || /^\d+$/.test(mlbStr);
    
    console.log('Validando MLB:', mlbStr, 'Resultado:', isValid);
    return isValid;
}

function processarPlanilha() {
    console.log('Clicou em Iniciar Atualização. Dados:', dadosPlanilha);
    
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
    
    console.log('Iniciando processamento de', mlbsValidos.length, 'MLBs');
    fecharModalPlanilha();
    
    // Preparar as atualizações apenas com MLBs válidos
    const atualizacoes = mlbsValidos.map(item => ({
        mlb: item.mlb.toUpperCase().startsWith('MLB') ? item.mlb.toUpperCase() : 'MLB' + item.mlb,
        dias: item.dias
    }));
    
    console.log('Atualizações preparadas:', atualizacoes);
    
    // Usar o mesmo sistema de progresso que já temos
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

    // Preenche informações básicas
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
    
    // Link para o anúncio
    document.getElementById('linkAnuncioML').href = item.permalink || '#';

    // Processa variações
    const temVariacoes = item.variacoes_detalhes && item.variacoes_detalhes.length > 0;
    const secaoVariacoes = document.getElementById('secaoVariacoes');
    const semVariacoes = document.getElementById('semVariacoes');
    const corpoTabela = document.getElementById('corpoTabelaVariacoes');
    
    if (temVariacoes) {
        secaoVariacoes.style.display = 'block';
        semVariacoes.style.display = 'none';
        
        // Limpa tabela
        corpoTabela.innerHTML = '';
        
        // Preenche variações
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

    // Abre o modal
    document.getElementById('modalDetalhesMLB').style.display = 'block';
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
        // Mostra o container de resultados e o loading
        ordersContainer.classList.remove('hidden');
        tableLoading.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
    } else {
        // Esconde apenas o loading, mantém o container visível
        tableLoading.classList.add('hidden');
    }
}

function limparResultados(mantemContainer = false) {
    const statsDiv = document.getElementById('stats');
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    const btnExportar = document.getElementById('btnExportar');
    const activeFilters = document.getElementById('activeFilters');
    const tableBody = document.getElementById('ordersTableBody');
    
    // Limpa a tabela
    if (tableBody) {
        tableBody.innerHTML = '';
    }
    
    // Esconde estatísticas
    if (statsDiv) {
        statsDiv.classList.add('hidden');
    }
    
    // Esconde botão de exportação
    if (btnExportar) {
        btnExportar.style.display = 'none';
    }
    
    // Esconde badges de filtros
    if (activeFilters) {
        activeFilters.style.display = 'none';
    }
    
    // Controla a visibilidade do container e estado vazio
    if (!mantemContainer) {
        if (ordersContainer) {
            ordersContainer.classList.add('hidden');
        }
        if (emptyState) {
            emptyState.classList.remove('hidden');
        }
    } else {
        // Mantém container visível mas esconde estado vazio
        if (ordersContainer) {
            ordersContainer.classList.remove('hidden');
        }
        if (emptyState) {
            emptyState.classList.add('hidden');
        }
    }
    
    // Limpa filtros ativos
    filtrosAtivos = {};
    
    // Reseta os selects apenas se não estamos mantendo o container
    if (!mantemContainer) {
        const tipoBusca = document.getElementById('tipoBusca');
        const filtroEnvio = document.getElementById('filtroEnvio');
        const filtroManufacturing = document.getElementById('filtroManufacturing');
        const filtroStatus = document.getElementById('filtroStatus');
        
        if (tipoBusca) tipoBusca.value = 'mlbs';
        if (filtroEnvio) filtroEnvio.value = 'todos';
        if (filtroManufacturing) filtroManufacturing.value = 'todos';
        if (filtroStatus) filtroStatus.value = 'todos';
    }
    
    ultimosResultados = [];
}

function limparCampos() {
    document.getElementById('mlbs').value = '';
    limparResultados();
    mostrarMensagem('Campos limpos', 'success');
}

function mostrarMensagem(mensagem, tipo) {
    // Cria alerta temporário
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo === 'error' ? 'error' : tipo === 'success' ? 'success' : 'info'}`;
    alertDiv.innerHTML = `
        <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle'}"></i>
        ${mensagem}
    `;
    
    // Adiciona no container
    const container = document.querySelector('.mercado-livre-container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remove após 3 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

function mostrarErro(mensagem) {
    mostrarMensagem(mensagem, 'error');
}

// =========================================
// FUNÇÕES DE MODAL
// =========================================

function fecharConfigModal() {
    document.getElementById('configModal').style.display = 'none';
}

function fecharDetalhesModal() {
    document.getElementById('modalDetalhesMLB').style.display = 'none';
}

// Fechar modais ao clicar fora
window.onclick = function(event) {
    const configModal = document.getElementById('configModal');
    const detalhesModal = document.getElementById('modalDetalhesMLB');
    const manufacturingModal = document.getElementById('modalManufacturing');
    const progressModal = document.getElementById('modalProgresso');
    const planilhaModal = document.getElementById('modalPlanilha');
    
    if (event.target === configModal) {
        configModal.style.display = 'none';
    }
    if (event.target === detalhesModal) {
        detalhesModal.style.display = 'none';
    }
    if (event.target === manufacturingModal) {
        manufacturingModal.style.display = 'none';
    }
    if (event.target === progressModal) {
        progressModal.style.display = 'none';
    }
    if (event.target === planilhaModal) {
        planilhaModal.style.display = 'none';
    }
}

// =========================================
// INICIALIZAÇÃO - ÚNICA E COMPLETA
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado - inicializando todas as funcionalidades');
    
    // 1. Configuração inicial de visibilidade
    const tableLoading = document.getElementById('tableLoading');
    const emptyState = document.getElementById('emptyState');
    const ordersContainer = document.getElementById('ordersContainer');
    
    if (tableLoading) tableLoading.classList.add('hidden');
    if (emptyState) emptyState.classList.remove('hidden');
    if (ordersContainer) ordersContainer.classList.add('hidden');
    
    // 2. Configura o botão toggle
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    if (toggleBtn) {
        toggleBtn.removeAttribute('onclick');
        toggleBtn.addEventListener('click', toggleFilters);
        console.log('✅ Toggle button configurado');
    }
    
    // 3. Inicializa os filtros expandidos
    const filtersHeader = document.getElementById('filtersHeader');
    if (filtersHeader) {
        filtersHeader.classList.remove('collapsed');
    }
    
    // 4. INICIALIZA OS FILTROS (NOVO)
    inicializarFiltros();
    
    // 5. Configura botão de aplicar filtros (mantém para compatibilidade)
    const aplicarBtn = document.querySelector('[onclick*="aplicarFiltros"]');
    if (aplicarBtn) {
        aplicarBtn.addEventListener('click', aplicarFiltros);
    }
    
    // 6. Enter no campo de busca
    const mlbsInput = document.getElementById('mlbs');
    if (mlbsInput) {
        mlbsInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarMLBs();
            }
        });
    }
    
    // 7. Configuração do upload de arquivo
    const fileUpload = document.getElementById('fileUpload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
            if (e.target.files[0]) {
                processarArquivoUpload(e.target.files[0]);
            }
        });
    }
    
    // 8. Inicializa badges de filtros
    atualizarBadgesFiltrosAtivos();
    
    // 9. Verifica configuração
    verificarConfiguracao();
    
    console.log('✅ Inicialização completa - filtros configurados');
});

// =========================================
// FIM DO ARQUIVO - FUNÇÕES COMPLETAS
// =========================================