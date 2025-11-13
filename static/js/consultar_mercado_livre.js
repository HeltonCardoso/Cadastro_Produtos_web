// static/js/consultar_mercado_livre.js

// Funções de configuração
function verificarConfiguracao() {
    fetch('/api/mercadolivre/configuracao')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                const statusElement = document.getElementById('statusConfiguracao');
                if (data.configurado) {
                    statusElement.innerHTML = '<span class="text-success">Configurado</span>';
                } else {
                    statusElement.innerHTML = '<span class="text-warning">Não configurado</span>';
                }
            }
        })
        .catch(error => {
            console.error('Erro ao verificar configuração:', error);
        });
}

function salvarConfiguracao(clientId, clientSecret) {
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
        if (data.sucesso) {
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfiguracao'));
            modal.hide();
            
            // Limpar campos
            document.getElementById('clientId').value = '';
            document.getElementById('clientSecret').value = '';
            
            mostrarMensagem('Configuração salva com sucesso!', 'success');
            verificarConfiguracao();
        } else {
            mostrarMensagem('Erro na configuração: ' + data.erro, 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro ao salvar configuração: ' + error.message, 'danger');
    });
}

// Funções de autenticação
function verificarStatusAutenticacao() {
    fetch('/api/mercadolivre/status')
        .then(response => response.json())
        .then(data => {
            const statusElement = document.getElementById('statusAutenticacao');
            if (data.sucesso && data.autenticado) {
                statusElement.innerHTML = '<span class="badge bg-success">Autenticado</span>';
                if (data.conexao_ativa) {
                    statusElement.innerHTML += ' <span class="badge bg-info">Conexão OK</span>';
                }
            } else {
                statusElement.innerHTML = '<span class="badge bg-danger">Não autenticado</span>';
            }
        })
        .catch(error => {
            console.error('Erro ao verificar status:', error);
        });
}

function autenticarMercadoLivre(accessToken, refreshToken) {
    fetch('/api/mercadolivre/autenticar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            access_token: accessToken,
            refresh_token: refreshToken
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalAutenticacao'));
            modal.hide();
            
            // Limpar campos
            document.getElementById('accessToken').value = '';
            document.getElementById('refreshToken').value = '';
            
            mostrarMensagem('Autenticação realizada com sucesso!', 'success');
            verificarStatusAutenticacao();
        } else {
            mostrarMensagem('Erro na autenticação: ' + data.erro, 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro na autenticação: ' + error.message, 'danger');
    });
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
            verificarStatusAutenticacao();
        } else {
            mostrarMensagem('Erro ao desautenticar: ' + data.erro, 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro ao desautenticar: ' + error.message, 'danger');
    });
}

// Funções de busca
function buscarMLBs() {
    const mlbsText = document.getElementById('mlbs').value.trim();
    const tipoBusca = document.getElementById('tipoBusca').value;
    
    if (tipoBusca === 'mlbs' && !mlbsText) {
        mostrarMensagem('Digite os códigos MLB para buscar', 'warning');
        return;
    }
    
    // Processar MLBs
    let mlbs = [];
    if (tipoBusca === 'mlbs') {
        mlbs = mlbsText.split(/[\n,]+/).map(mlb => mlb.trim()).filter(mlb => mlb);
        
        if (mlbs.length === 0) {
            mostrarMensagem('Nenhum MLB válido encontrado', 'warning');
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
        console.log('Resposta da API:', data); // Para debug
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
    
    // Mostrar estatísticas
    mostrarEstatisticas(data);
    
    // Mostrar resultados
    mostrarResultados(data.resultados);
}

function mostrarEstatisticas(data) {
    const estatisticasDiv = document.getElementById('estatisticas');
    
    let html = `
        <div class="card card-estatisticas">
            <div class="card-body">
                <div class="row text-center">
                    <div class="col-md-3">
                        <div class="stat-number text-primary">${data.total_encontrado || 0}</div>
                        <div class="stat-label">Encontrados</div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-number text-warning">${data.total_nao_encontrado || 0}</div>
                        <div class="stat-label">Não Encontrados</div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-number text-info">${data.resultados ? data.resultados.length : 0}</div>
                        <div class="stat-label">Total Processado</div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-number text-secondary">
                            ${new Date(data.timestamp).toLocaleTimeString()}
                        </div>
                        <div class="stat-label">Horário</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    estatisticasDiv.innerHTML = html;
    estatisticasDiv.style.display = 'block';
}

function mostrarResultados(resultados) {
    const resultadoDiv = document.getElementById('resultadoMLB');
    
    if (!resultados || resultados.length === 0) {
        resultadoDiv.innerHTML = `
            <div class="alert alert-warning mt-4">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Nenhum resultado encontrado
            </div>
        `;
        resultadoDiv.style.display = 'block';
        return;
    }
    
    let html = `
        <div class="card mt-4">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-list me-2"></i>
                    Resultados (${resultados.length} itens)
                </h5>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>MLB</th>
                                <th>Título</th>
                                <th>Preço</th>
                                <th>Status</th>
                                <th>Estoque</th>
                                <th>Envio</th>
                                <th>Manufacturing</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    resultados.forEach(item => {
        const temErro = item.error || item.status === 'error';
        
        html += `
            <tr class="${temErro ? 'table-warning' : ''}">
                <td>
                    <strong>${item.id || 'N/A'}</strong>
                    ${temErro ? '<br><small class="text-danger">' + item.error + '</small>' : ''}
                </td>
                <td>${!temErro ? (item.title ? item.title.substring(0, 50) + (item.title.length > 50 ? '...' : '') : 'N/A') : '-'}</td>
                <td>${!temErro ? ('R$ ' + (item.price || 0).toLocaleString('pt-BR')) : '-'}</td>
                <td>
                    ${!temErro ? `<span class="badge ${getStatusBadgeClass(item.status)}">${item.status || 'N/A'}</span>` : '-'}
                </td>
                <td>${!temErro ? (item.available_quantity || 0) : '-'}</td>
                <td>
                    ${!temErro ? `<span class="badge ${item.shipping_mode === 'me2' ? 'bg-success' : 'bg-secondary'}">${item.shipping_mode || 'N/A'}</span>` : '-'}
                </td>
                <td>
                    ${!temErro ? (item.manufacturing_time && item.manufacturing_time !== 'N/A' ? 
                        `<span class="badge bg-info">${item.manufacturing_time}</span>` : 
                        '<span class="badge bg-warning">Sem</span>') : '-'}
                </td>
                <td>
                    ${!temErro ? `
                        <button class="btn btn-sm btn-outline-primary" onclick="abrirDetalhes('${item.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <a href="${item.permalink || '#'}" target="_blank" class="btn btn-sm btn-outline-secondary">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    ` : '-'}
                </td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    resultadoDiv.innerHTML = html;
    resultadoDiv.style.display = 'block';
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'active': return 'bg-success';
        case 'paused': return 'bg-warning';
        case 'closed': return 'bg-secondary';
        default: return 'bg-light text-dark';
    }
}

function abrirDetalhes(mlbId) {
    // Implementar modal de detalhes se necessário
    alert(`Detalhes do MLB: ${mlbId}\n\nEsta funcionalidade pode ser implementada posteriormente.`);
}

// Funções de análise de envio
function analisarEnvioManufacturing() {
    const mlbsText = document.getElementById('mlbs').value.trim();
    
    if (!mlbsText) {
        mostrarMensagem('Digite os códigos MLB para análise', 'warning');
        return;
    }
    
    const mlbs = mlbsText.split(/[\n,]+/).map(mlb => mlb.trim()).filter(mlb => mlb);
    
    if (mlbs.length === 0) {
        mostrarMensagem('Nenhum MLB válido encontrado', 'warning');
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
    
    const estatisticas = data.estatisticas;
    const estatisticasDiv = document.getElementById('estatisticas');
    
    let html = `
        <div class="card card-estatisticas">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-chart-bar me-2"></i>
                    Análise de Envio e Manufacturing Time
                </h5>
            </div>
            <div class="card-body">
                <div class="row text-center">
                    <div class="col-md-2">
                        <div class="stat-number text-primary">${estatisticas.total_analisado}</div>
                        <div class="stat-label">Total Analisado</div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-number text-success">${estatisticas.me2}</div>
                        <div class="stat-label">ME2</div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-number text-warning">${estatisticas.me1}</div>
                        <div class="stat-label">ME1</div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-number text-info">${estatisticas.com_manufacturing}</div>
                        <div class="stat-label">Com Manufacturing</div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-number text-danger">${estatisticas.sem_manufacturing}</div>
                        <div class="stat-label">Sem Manufacturing</div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-number text-secondary">
                            ${new Date(data.timestamp).toLocaleTimeString()}
                        </div>
                        <div class="stat-label">Horário</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    estatisticasDiv.innerHTML = html;
    estatisticasDiv.style.display = 'block';
    
    // Mostrar resultados também
    mostrarResultados(data.resultados);
}

// Funções auxiliares de UI
function mostrarLoading(mostrar) {
    const loadingDiv = document.getElementById('loadingMLB');
    loadingDiv.style.display = mostrar ? 'block' : 'none';
}

function limparResultados() {
    document.getElementById('estatisticas').style.display = 'none';
    document.getElementById('resultadoMLB').style.display = 'none';
    document.getElementById('mensagemErro').style.display = 'none';
}

function mostrarMensagem(mensagem, tipo) {
    // Usar sistema de alert do Bootstrap
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Adicionar no topo do container
    const container = document.querySelector('.mercado-livre-container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function mostrarErro(mensagem) {
    const erroDiv = document.getElementById('mensagemErro');
    erroDiv.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${mensagem}
        </div>
    `;
    erroDiv.style.display = 'block';
}

function limparCampos() {
    document.getElementById('mlbs').value = '';
    limparResultados();
}

function toggleUploadCard() {
    const tipoBusca = document.getElementById('tipoBusca').value;
    const cardUpload = document.getElementById('cardUpload');
    
    if (tipoBusca === 'arquivo') {
        cardUpload.style.display = 'block';
    } else {
        cardUpload.style.display = 'none';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Configuração
    document.getElementById('btnSalvarConfiguracao').addEventListener('click', function() {
        const clientId = document.getElementById('clientId').value.trim();
        const clientSecret = document.getElementById('clientSecret').value.trim();
        
        if (!clientId || !clientSecret) {
            mostrarMensagem('Preencha ambos os campos', 'warning');
            return;
        }
        
        salvarConfiguracao(clientId, clientSecret);
    });
    
    // Autenticação
    document.getElementById('btnConfirmarAutenticacao').addEventListener('click', function() {
        const accessToken = document.getElementById('accessToken').value.trim();
        const refreshToken = document.getElementById('refreshToken').value.trim();
        
        if (!accessToken || !refreshToken) {
            mostrarMensagem('Preencha ambos os tokens', 'warning');
            return;
        }
        
        autenticarMercadoLivre(accessToken, refreshToken);
    });
    
    // Desautenticação
    document.getElementById('btnDesautenticar').addEventListener('click', function() {
        desautenticarMercadoLivre();
    });
    
    // Busca
    document.getElementById('formBuscarMLB').addEventListener('submit', function(e) {
        e.preventDefault();
        buscarMLBs();
    });
    
    // Análise de envio
    document.getElementById('btnAnalisarEnvio').addEventListener('click', function() {
        analisarEnvioManufacturing();
    });
    
    // Limpar
    document.getElementById('btnLimpar').addEventListener('click', function() {
        limparCampos();
    });
    
    // Tipo de busca
    document.getElementById('tipoBusca').addEventListener('change', function() {
        toggleUploadCard();
    });
    
    // Verificar configuração ao carregar a página
    verificarConfiguracao();
    verificarStatusAutenticacao();
});