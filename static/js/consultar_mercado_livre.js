// static/js/consultar_mercado_livre.js - VERSÃO ATUALIZADA

// Variáveis globais
let ultimosResultados = [];

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
// FUNÇÕES DE BUSCA (ATUALIZADAS)
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
    
    // Mostrar loading
    mostrarLoading(true);
    limparResultados();
    
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
    })
    .finally(() => {
        mostrarLoading(false);
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
    
    // Mostrar resultados
    mostrarResultados(ultimosResultados);
}

function mostrarEstatisticas(data) {
    const statsDiv = document.getElementById('stats');
    
    let html = `
        <i class="fas fa-chart-bar"></i>
        <strong>Estatísticas:</strong>
        ${data.total_encontrado || 0} encontrados • 
        ${data.total_nao_encontrado || 0} não encontrados • 
        ${data.resultados ? data.resultados.length : 0} processados • 
        ${new Date(data.timestamp).toLocaleTimeString()}
    `;
    
    statsDiv.innerHTML = html;
    statsDiv.classList.remove('hidden');
}

function mostrarResultados(resultados) {
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    const tableBody = document.getElementById('ordersTableBody');
    
    if (!resultados || resultados.length === 0) {
        ordersContainer.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }
    
    // Oculta estado vazio e mostra container
    emptyState.classList.add('hidden');
    ordersContainer.classList.remove('hidden');
    
    // Limpa tabela
    tableBody.innerHTML = '';
    
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

// =========================================
// FUNÇÃO DE EXPORTAR PARA EXCEL
// =========================================

// =========================================
// FUNÇÃO DE EXPORTAR PARA EXCEL - ESTRUTURA MELHORADA
// =========================================

function exportarParaExcel() {
    if (!ultimosResultados || ultimosResultados.length === 0) {
        mostrarMensagem('Nenhum resultado para exportar', 'error');
        return;
    }

    mostrarLoading(true);

    // Preparar dados para exportação
    const dadosExportacao = [];
    
    ultimosResultados.forEach(item => {
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
    const totalItens = ultimosResultados.length;
    const totalEncontrado = ultimosResultados.filter(item => !item.error && item.status !== 'error').length;
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
        a.download = `consulta_mlb_${new Date().toISOString().slice(0, 10)}_${new Date().getHours()}${new Date().getMinutes()}.xlsx`;
        
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


function processarAnaliseEnvio(data) {
    if (!data.sucesso) {
        mostrarErro(data.erro || 'Erro desconhecido na análise');
        return;
    }
    
    const statsDiv = document.getElementById('stats');
    const estatisticas = data.estatisticas;
    
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
    
    // Mostrar resultados
    ultimosResultados = data.resultados || [];
    mostrarResultados(ultimosResultados);
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
    const tableLoading = document.getElementById('tableLoading');
    const ordersContainer = document.getElementById('ordersContainer');
    
    if (mostrar) {
        tableLoading.classList.remove('hidden');
        ordersContainer.classList.remove('hidden');
        document.getElementById('emptyState').classList.add('hidden');
    } else {
        tableLoading.classList.add('hidden');
    }
}

function limparResultados() {
    const statsDiv = document.getElementById('stats');
    const ordersContainer = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    const btnExportar = document.getElementById('btnExportar');
    
    statsDiv.classList.add('hidden');
    ordersContainer.classList.add('hidden');
    emptyState.classList.remove('hidden');
    btnExportar.style.display = 'none'; // Oculta botão de exportação
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

function toggleConfigSection() {
    document.getElementById('configModal').style.display = 'block';
}

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
    
    if (event.target === configModal) {
        configModal.style.display = 'none';
    }
    if (event.target === detalhesModal) {
        detalhesModal.style.display = 'none';
    }
}

// =========================================
// EVENT LISTENERS
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    // Enter no campo de busca
    document.getElementById('mlbs').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            buscarMLBs();
        }
    });
    
    // Verificar configuração ao carregar a página
    verificarConfiguracao();
});
