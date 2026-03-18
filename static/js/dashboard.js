// ============================================
// DASHBOARD - SEQUÊNCIA DE CADASTROS
// JavaScript principal
// ============================================

console.log('🚀 Dashboard iniciado');

// Estado global
let atualizando = false;

// Função principal
window.carregarDados = async function() {
    if (atualizando) return;
    
    atualizando = true;
    console.log('🔄 Carregando dados...');
    
    const refreshIcon = document.getElementById('refresh-icon');
    if (refreshIcon) refreshIcon.classList.add('refreshing');
    
    try {
        const response = await fetch('/api/dashboard/sequencia-cadastros-corrigido');
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log('📊 Dados recebidos:', data);
        
        if (data.sucesso && data.dados) {
            atualizarDashboard(data.dados);
            atualizarStatus('Online', 'online');
        } else {
            throw new Error(data.erro || 'Erro ao carregar dados');
        }
        
    } catch (error) {
        console.error('❌ Erro:', error);
        atualizarStatus('Offline', 'offline');
        mostrarErro(error.message);
    } finally {
        atualizando = false;
        if (refreshIcon) refreshIcon.classList.remove('refreshing');
    }
};

// Atualizar dashboard
function atualizarDashboard(dados) {
    console.log('📝 Atualizando dashboard...');
    
    // KPI Cards
    const total = dados.total_cadastros || 0;
    const situacoes = dados.situacoes || {};
    const emAndamento = situacoes['EM ANDAMENTO'] || 0;
    const ticket = situacoes['TICKET'] || 0;
    const prazos = dados.prazos || {};
    
    setTexto('total-cadastros', total);
    setTexto('em-andamento', emAndamento);
    setTexto('ticket', ticket);
    setTexto('com-prazo', prazos.com_prazo || 0);
    
    // Percentuais
    if (total > 0) {
        const percAndamento = ((emAndamento / total) * 100).toFixed(1);
        const percElement = document.querySelector('#percentual-andamento span');
        if (percElement) percElement.textContent = `${percAndamento}% do total`;
    }
    
    const semPrazoElement = document.getElementById('sem-prazo');
    if (semPrazoElement) semPrazoElement.textContent = `${prazos.sem_prazo || 0} sem prazo`;
    
    // Situações
    atualizarSituacoes(situacoes, total);
    
    // Responsáveis
    atualizarResponsaveis(dados.responsaveis || {});
    
    // Marcas por situação
    atualizarMarcas(dados.marcas_por_situacao || {});
    
    // Tabela
    if (dados.ultimos_cadastros) {
        atualizarTabela(dados.ultimos_cadastros);
        setTexto('total-exibido', `${dados.ultimos_cadastros.length} de ${total}`);
    }
    
    // Timestamp
    const agora = new Date();
    setTexto('ultima-atualizacao', `Última atualização: ${agora.toLocaleString('pt-BR')}`);
    
    // Debug
    atualizarDebug('Conectado', 'success');
}

// Atualizar situações
function atualizarSituacoes(situacoes, total) {
    const container = document.getElementById('situacoes-container');
    if (!container) return;
    
    if (!situacoes || Object.keys(situacoes).length === 0) {
        container.innerHTML = '<div class="loading-container"><div class="spinner"></div><p>Nenhuma situação encontrada</p></div>';
        return;
    }
    
    let html = '<div class="status-list">';
    const cores = ['#4361ee', '#06d6a0', '#ffb703', '#ef476f', '#4cc9f0'];
    let i = 0;
    
    for (const [situacao, quantidade] of Object.entries(situacoes)) {
        const percent = total > 0 ? (quantidade / total * 100).toFixed(1) : 0;
        const cor = cores[i % cores.length];
        
        html += `
            <div class="status-item">
                <div class="status-color" style="background: ${cor};"></div>
                <div class="status-info">
                    <span class="status-name">${situacao}</span>
                    <span class="status-count">${quantidade}</span>
                </div>
            </div>
            <div class="status-bar">
                <div class="status-bar-fill" style="width: ${percent}%; background: ${cor};"></div>
            </div>
        `;
        i++;
    }
    
    html += '</div>';
    container.innerHTML = html;
    setTexto('total-situacoes', `${Object.keys(situacoes).length} situações`);
}

// Atualizar responsáveis
function atualizarResponsaveis(responsaveis) {
    const container = document.getElementById('responsaveis-container');
    if (!container) return;
    
    if (!responsaveis || Object.keys(responsaveis).length === 0) {
        container.innerHTML = '<div class="loading-container"><div class="spinner"></div><p>Nenhum responsável encontrado</p></div>';
        return;
    }
    
    let html = '<div class="responsaveis-grid">';
    
    for (const [responsavel, quantidade] of Object.entries(responsaveis)) {
        html += `
            <div class="responsavel-item">
                <div class="responsavel-nome">${responsavel}</div>
                <div class="responsavel-count">${quantidade}</div>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
    setTexto('total-responsaveis', `${Object.keys(responsaveis).length} responsáveis`);
}

// Atualizar marcas
function atualizarMarcas(marcasPorSituacao) {
    const container = document.getElementById('marcas-container');
    if (!container) return;
    
    if (!marcasPorSituacao || Object.keys(marcasPorSituacao).length === 0) {
        container.innerHTML = '<div class="loading-container"><div class="spinner"></div><p>Nenhuma marca encontrada</p></div>';
        return;
    }
    
    let html = '<div class="marcas-grid">';
    let totalMarcas = 0;
    
    for (const [situacao, marcas] of Object.entries(marcasPorSituacao)) {
        if (marcas && marcas.length > 0) {
            totalMarcas += marcas.length;
            const classe = situacao.includes('ANDAMENTO') ? 'andamento' : 
                          (situacao.includes('TICKET') ? 'ticket' : 'outros');
            
            html += `
                <div class="marca-card ${classe}">
                    <div class="marca-header">
                        <strong>${situacao}</strong>
                        <span class="badge">${marcas.length}</span>
                    </div>
                    <div class="marca-tags">
                        ${marcas.slice(0, 8).map(m => 
                            `<span class="marca-tag">${m}</span>`
                        ).join('')}
                        ${marcas.length > 8 ? `<span class="marca-tag">+${marcas.length - 8}</span>` : ''}
                    </div>
                </div>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
    setTexto('total-marcas', `${totalMarcas} marcas`);
}

// Atualizar tabela
function atualizarTabela(cadastros) {
    const tbody = document.getElementById('tabela-body');
    if (!tbody) return;
    
    if (!cadastros || cadastros.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="padding: 40px;">Nenhum cadastro encontrado</td></tr>';
        return;
    }
    
    let html = '';
    cadastros.forEach(item => {
        const situacaoClass = item.situacao?.includes('ANDAMENTO') ? 'situacao-andamento' : 
                             (item.situacao?.includes('TICKET') ? 'situacao-ticket' : 'situacao-outros');
        
        html += `
            <tr>
                <td><strong>${item.marca || '-'}</strong></td>
                <td><span class="situacao-tag ${situacaoClass}">${item.situacao || '-'}</span></td>
                <td><span class="responsavel-tag">${item.responsavel || '-'}</span></td>
                <td>${item.prazo || '-'}</td>
                <td><span style="color: var(--gray);">${item.observacao?.substring(0, 30) || '-'}${item.observacao?.length > 30 ? '...' : ''}</span></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Funções utilitárias
function setTexto(id, valor) {
    const el = document.getElementById(id);
    if (el) el.textContent = valor;
}

function atualizarStatus(status, classe) {
    const statusEl = document.getElementById('status-geral');
    if (statusEl) {
        statusEl.className = `status-badge ${classe}`;
        statusEl.innerHTML = `<i class="fas fa-circle"></i> ${status}`;
    }
}

function atualizarDebug(status, tipo) {
    const debugStatus = document.getElementById('debug-status');
    if (debugStatus) {
        debugStatus.innerHTML = status;
        debugStatus.className = tipo;
    }
    
    const debugTime = document.getElementById('debug-time');
    if (debugTime) {
        debugTime.textContent = new Date().toLocaleTimeString();
    }
}

function mostrarErro(mensagem) {
    const tbody = document.getElementById('tabela-body');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger" style="padding: 40px;">Erro: ${mensagem}</td></tr>`;
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 Página carregada');
    carregarDados();
});

// Atualizar a cada 5 minutos
setInterval(carregarDados, 300000);