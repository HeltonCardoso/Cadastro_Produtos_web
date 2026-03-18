// dashboard_sequencia.js - Dashboard da Sequência de Cadastros
// Mesmo padrão do config_google_sheets.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Inicializando dashboard da sequência...');
    carregarDadosSequencia();
    
    // Configurar botão de atualizar
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            carregarDadosSequencia();
        });
    }
});

function carregarDadosSequencia() {
    console.log('🔄 Carregando dados da sequência...');
    
    // Mostrar loading
    mostrarLoading(true);
    
    fetch('/api/dashboard/sequencia-cadastros')
        .then(response => {
            console.log('📡 Status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 Dados recebidos:', data);
            
            if (data.sucesso && data.dados) {
                atualizarDashboard(data.dados);
                atualizarStatus('Conectado', 'success');
            } else {
                throw new Error(data.erro || 'Erro ao carregar dados');
            }
        })
        .catch(error => {
            console.error('❌ Erro:', error);
            atualizarStatus('Erro: ' + error.message, 'danger');
            mostrarErro(error.message);
        })
        .finally(() => {
            mostrarLoading(false);
        });
}

function atualizarDashboard(dados) {
    console.log('📝 Atualizando dashboard...', dados);
    
    // 1. Cards de resumo
    setElementText('total-cadastros', dados.total_cadastros || 0);
    
    // Contagem por situação
    const situacoes = dados.situacoes || {};
    const emAndamento = situacoes['EM ANDAMENTO'] || 0;
    const ticket = situacoes['TICKET'] || 0;
    
    setElementText('em-andamento', emAndamento);
    setElementText('ticket', ticket);
    
    if (dados.total_cadastros > 0) {
        const percAndamento = ((emAndamento / dados.total_cadastros) * 100).toFixed(1);
        setElementText('percentual-andamento', `${percAndamento}% do total`);
    }
    
    // Prazos
    if (dados.prazos) {
        setElementText('com-prazo', dados.prazos.com_prazo || 0);
        setElementText('sem-prazo', `${dados.prazos.sem_prazo || 0} sem prazo`);
    }
    
    // 2. Distribuição por situação
    atualizarSituacoes(situacoes);
    
    // 3. Distribuição por responsável
    atualizarResponsaveis(dados.responsaveis || {});
    
    // 4. Marcas por situação
    atualizarMarcas(dados.marcas_por_situacao || {});
    
    // 5. Tabela de últimos cadastros
    if (dados.ultimos_cadastros) {
        atualizarTabela(dados.ultimos_cadastros);
        setElementText('total-exibido', `${dados.ultimos_cadastros.length} de ${dados.total_cadastros}`);
    }
    
    // 6. Timestamp
    const agora = new Date();
    setElementText('ultima-atualizacao', `Atualizado em: ${agora.toLocaleString('pt-BR')}`);
}

function atualizarSituacoes(situacoes) {
    const container = document.getElementById('situacoes-container');
    if (!container) return;
    
    if (!situacoes || Object.keys(situacoes).length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-4">Nenhuma situação encontrada</div>';
        return;
    }
    
    let html = '<div class="row">';
    let total = Object.values(situacoes).reduce((a, b) => a + b, 0);
    
    for (const [situacao, quantidade] of Object.entries(situacoes)) {
        const percent = total > 0 ? ((quantidade / total) * 100).toFixed(1) : 0;
        const corClass = getSituacaoClass(situacao);
        
        html += `
            <div class="col-md-6 mb-3">
                <div class="d-flex justify-content-between align-items-center p-3 border rounded ${corClass}">
                    <div>
                        <strong>${situacao}</strong>
                    </div>
                    <div>
                        <span class="badge bg-secondary me-2">${quantidade}</span>
                        <small class="text-muted">${percent}%</small>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function atualizarResponsaveis(responsaveis) {
    const container = document.getElementById('responsaveis-container');
    if (!container) return;
    
    if (!responsaveis || Object.keys(responsaveis).length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-4">Nenhum responsável encontrado</div>';
        return;
    }
    
    let html = '<div class="row">';
    
    for (const [responsavel, quantidade] of Object.entries(responsaveis)) {
        html += `
            <div class="col-md-4 mb-2">
                <div class="d-flex justify-content-between align-items-center p-2 border rounded">
                    <span class="badge bg-light text-dark p-2">${responsavel}</span>
                    <span class="badge bg-primary">${quantidade}</span>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function atualizarMarcas(marcasPorSituacao) {
    const container = document.getElementById('marcas-container');
    if (!container) return;
    
    if (!marcasPorSituacao || Object.keys(marcasPorSituacao).length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-4">Nenhuma marca encontrada</div>';
        return;
    }
    
    let html = '<div class="row">';
    
    for (const [situacao, marcas] of Object.entries(marcasPorSituacao)) {
        if (marcas && marcas.length > 0) {
            const corClass = getSituacaoClass(situacao);
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-header py-2 ${corClass}">
                            <strong>${situacao}</strong>
                            <span class="badge bg-secondary float-end">${marcas.length}</span>
                        </div>
                        <div class="card-body p-2">
                            ${marcas.slice(0, 5).map(m => 
                                `<span class="badge bg-light text-dark me-1 mb-1 p-2">${m}</span>`
                            ).join('')}
                            ${marcas.length > 5 ? 
                                `<small class="d-block mt-1 text-muted">+${marcas.length - 5} outras</small>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function atualizarTabela(cadastros) {
    const tbody = document.getElementById('tabela-body');
    if (!tbody) return;
    
    if (!cadastros || cadastros.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4">Nenhum cadastro encontrado</td></tr>';
        return;
    }
    
    let html = '';
    cadastros.forEach(item => {
        const situacaoClass = getSituacaoClass(item.situacao);
        html += `
            <tr>
                <td><strong>${item.marca || '-'}</strong></td>
                <td><span class="badge ${situacaoClass} p-2">${item.situacao || '-'}</span></td>
                <td><span class="badge bg-light text-dark p-2">${item.responsavel || '-'}</span></td>
                <td>${item.prazo || '-'}</td>
                <td><small>${item.observacao || '-'}</small></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function getSituacaoClass(situacao) {
    if (!situacao) return 'bg-secondary text-white';
    const s = String(situacao).toUpperCase().trim();
    if (s.includes('EM ANDAMENTO')) return 'bg-warning text-dark';
    if (s.includes('TICKET')) return 'bg-success text-white';
    if (s.includes('PENDENTE')) return 'bg-danger text-white';
    if (s.includes('FINALIZADA')) return 'bg-info text-white';
    return 'bg-secondary text-white';
}

function setElementText(id, valor) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = valor;
    }
}

function mostrarLoading(ativo) {
    const refreshIcon = document.getElementById('refresh-icon');
    if (refreshIcon) {
        if (ativo) {
            refreshIcon.classList.add('refreshing');
        } else {
            refreshIcon.classList.remove('refreshing');
        }
    }
}

function atualizarStatus(mensagem, tipo) {
    const statusGeral = document.getElementById('status-geral');
    if (statusGeral) {
        statusGeral.className = `badge bg-${tipo}`;
        statusGeral.textContent = mensagem;
    }
    
    const debugStatus = document.getElementById('debug-status');
    if (debugStatus) {
        debugStatus.innerHTML = `Status: <span class="text-${tipo}">${mensagem}</span>`;
    }
}

function mostrarErro(mensagem) {
    const tbody = document.getElementById('tabela-body');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-3">Erro: ${mensagem}</td></tr>`;
    }
}

// Atualizar a cada 5 minutos
setInterval(carregarDadosSequencia, 300000);