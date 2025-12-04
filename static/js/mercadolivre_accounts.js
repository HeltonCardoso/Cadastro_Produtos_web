// mercadolivre_accounts.js - Gerenciamento de Contas Mercado Livre

let contaSelecionadaParaTokens = null;

// =========================================
// CARREGAMENTO DE CONTAS
// =========================================

function carregarContasMercadoLivre() {
    fetch('/api/mercadolivre/contas')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                atualizarInterfaceContasML(data);
                testarStatusMercadoLivre(data.conta_atual);
            } else {
                mostrarErroML('Erro ao carregar contas: ' + data.erro);
            }
        })
        .catch(error => {
            console.error('Erro ao carregar contas:', error);
            mostrarErroML('Erro de conexão ao carregar contas');
        });
}

function atualizarInterfaceContasML(data) {
    // Atualiza resumo
    atualizarResumoContas(data.contas, data.conta_atual);
    
    // Atualiza lista de contas
    renderizarListaContas(data.contas, data.conta_atual);
    
    // Atualiza informações da conta atual
    atualizarContaAtual(data.contas, data.conta_atual);
}

function atualizarResumoContas(contas, contaAtualId) {
    const total = contas.length;
    const autenticadas = contas.filter(c => c.has_token).length;
    const pendentes = total - autenticadas;
    
    // Atualiza o card "Contas Totais"
    document.getElementById('totalAccountsCount').textContent = `${total} conta${total !== 1 ? 's' : ''}`;
    
    // Atualiza o card "Conta Atual"
    const contaAtual = contas.find(c => c.id === contaAtualId);
    if (contaAtual) {
        document.getElementById('currentAccountName').textContent = contaAtual.name;
        document.getElementById('currentAccountStatus').textContent = contaAtual.has_token ? 'Autenticada' : 'Pendente';
    } else {
        document.getElementById('currentAccountName').textContent = 'Nenhuma';
        document.getElementById('currentAccountStatus').textContent = 'Não selecionada';
    }
    
    // Atualiza status global no sidebar
    const statusElement = document.getElementById('mlGlobalStatus');
    if (contaAtual && contaAtual.has_token) {
        statusElement.textContent = 'Conectado';
        statusElement.style.color = 'var(--success-color)';
    } else if (total > 0) {
        statusElement.textContent = 'Pendente';
        statusElement.style.color = 'var(--warning-color)';
    } else {
        statusElement.textContent = 'Não configurado';
        statusElement.style.color = 'var(--danger-color)';
    }
    
    // Mostra/esconde a seção de contas se tiver contas
    const accountsContainer = document.getElementById('mlAccountsContainer');
    if (total > 0) {
        accountsContainer.style.display = 'block';
    } else {
        accountsContainer.style.display = 'none';
    }
}

function renderizarListaContas(contas, contaAtualId) {
    const container = document.getElementById('mlAccountsList');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (contas.length === 0) {
        container.innerHTML = `
            <div class="info-box">
                <i class="fas fa-info-circle"></i>
                <div>
                    <p>Nenhuma conta configurada. Clique em "Adicionar Nova Conta" para começar.</p>
                </div>
            </div>
        `;
        return;
    }
    
    contas.forEach(conta => {
        const isAtual = conta.id === contaAtualId;
        const card = document.createElement('div');
        card.className = `account-card ${isAtual ? 'current' : ''}`;
        
        card.innerHTML = `
            <div class="account-header">
                <h5>${conta.name}</h5>
                <div>
                    ${isAtual ? 
                        '<span class="badge badge-primary-modern"><i class="fas fa-check"></i> Em uso</span>' : 
                        ''}
                    ${conta.has_token ? 
                        '<span class="badge badge-success"><i class="fas fa-key"></i> Autenticada</span>' : 
                        '<span class="badge badge-warning"><i class="fas fa-clock"></i> Pendente</span>'}
                </div>
            </div>
            
            <div class="account-details">
                <div><i class="fas fa-id-card"></i> App ID: ${conta.app_id}</div>
                ${conta.nickname ? 
                    `<div><i class="fas fa-user"></i> ${conta.nickname}</div>` : 
                    `<div><i class="fas fa-exclamation-triangle"></i> Não autenticada</div>`}
                <div><i class="fas fa-calendar"></i> Criada em: ${formatarData(conta.created_at)}</div>
            </div>
            
            <div class="account-actions">
                ${!isAtual && conta.has_token ? `
                    <button class="btn-secondary btn-sm" onclick="selecionarContaML('${conta.id}')">
                        <i class="fas fa-play-circle"></i> Usar
                    </button>
                ` : ''}
                
                ${!conta.has_token ? `
                    <button class="btn-secondary btn-sm" onclick="completarAutenticacaoML('${conta.id}', '${conta.name}')">
                        <i class="fas fa-key"></i> Completar
                    </button>
                ` : `
                    <button class="btn-secondary btn-sm" onclick="testarContaML('${conta.id}')">
                        <i class="fas fa-vial"></i> Testar
                    </button>
                `}
                
                ${!isAtual ? `
                    <button class="btn-danger btn-sm" onclick="removerContaML('${conta.id}', '${conta.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                ` : ''}
            </div>
        `;
        
        container.appendChild(card);
    });
}

function testarTodasContas() {
    const container = document.getElementById('mlAccountsList');
    const cards = container.querySelectorAll('.account-card');
    
    cards.forEach(card => {
        const testBtn = card.querySelector('button[onclick*="testarContaML"]');
        if (testBtn) {
            testBtn.click();
        }
    });
}

function atualizarContaAtual(contas, contaAtualId) {
    const container = document.getElementById('currentAccountInfo');
    if (!container) return;
    
    const contaAtual = contas.find(c => c.id === contaAtualId);
    
    if (!contaAtual) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                Nenhuma conta selecionada para uso.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <strong>${contaAtual.name}</strong><br>
                ${contaAtual.nickname ? `<small>Usuário: ${contaAtual.nickname}</small><br>` : ''}
                <small class="text-muted">App ID: ${contaAtual.app_id}</small>
            </div>
            <div>
                ${contaAtual.has_token ? 
                    '<span class="badge bg-success"><i class="fas fa-check"></i> Autenticada</span>' : 
                    '<span class="badge bg-warning"><i class="fas fa-clock"></i> Pendente</span>'}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// =========================================
// FUNÇÕES PRINCIPAIS
// =========================================

function abrirModalNovaConta() {
    const modalOverlay = document.getElementById('modalNovaConta');
    const modalContainer = modalOverlay.querySelector('.modal-container');
    
    if (modalOverlay) {
        // Mostra o overlay
        modalOverlay.style.display = 'flex';
        // Mostra o container (se necessário)
        if (modalContainer) {
            modalContainer.style.display = 'block';
        }
    }
}

function fecharModalNovaConta() {
    console.log('Fechando modal nova conta...');
    
    const modal = document.getElementById('modalNovaConta');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        console.log('✅ Modal fechado com sucesso');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado - inicializando modais Mercado Livre');
    
    // 1. Configura botões de fechar modal
    const closeButtons = document.querySelectorAll('.close-modal-modern');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal-overlay');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // 2. Fechar modal ao clicar fora
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(modal => {
        modal.addEventListener('click', function(event) {
            if (event.target === this) {
                this.style.display = 'none';
            }
        });
    });
    
    // 3. Prevenir fechamento ao clicar dentro do modal container
    const modalContainers = document.querySelectorAll('.modal-container');
    modalContainers.forEach(container => {
        container.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    });
    
    // 4. Carrega contas ao iniciar
    carregarContasMercadoLivre();
    
    // 5. Testa atalho de teclado (ESC para fechar)
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modalAberto = document.querySelector('.modal-overlay[style*="display: block"]');
            if (modalAberto) {
                modalAberto.style.display = 'none';
            }
        }
    });
    
    console.log('✅ Modais Mercado Livre inicializados');
});

function adicionarNovaContaML() {
    const nome = document.getElementById('novaContaNome').value.trim();
    const appId = document.getElementById('novaContaAppId').value.trim();
    const secretKey = document.getElementById('novaContaSecretKey').value.trim();
    
    if (!nome || !appId || !secretKey) {
        mostrarResultadoML('Preencha todos os campos', 'error');
        return;
    }
    
    mostrarResultadoML('Adicionando conta e tentando autenticar automaticamente...', 'info');
    
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
                mostrarResultadoML('🎉 Conta adicionada e autenticada automaticamente!', 'success');
                setTimeout(() => {
                    fecharModalNovaConta();
                    carregarContasMercadoLivre();
                }, 1500);
            } else {
                // Autenticação automática falhou
                mostrarResultadoML('Conta criada! Mas precisamos completar a autenticação manualmente.', 'warning');
                contaSelecionadaParaTokens = data.account_id;
                
                // Abre modal para tokens manuais
                setTimeout(() => {
                    fecharModalNovaConta();
                    abrirModalTokensManual(data.account_id, nome);
                }, 1000);
            }
        } else {
            mostrarResultadoML('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarResultadoML('Erro: ' + error.message, 'error');
    });
}

function abrirModalTokensManual(accountId, accountName) {
    contaSelecionadaParaTokens = accountId;
    
    document.getElementById('modalTokensInfo').innerHTML = `
        <div class="alert alert-warning">
            <h6><i class="fas fa-exclamation-triangle"></i> Completar Autenticação: ${accountName}</h6>
            <p><strong>Siga estes passos para obter os tokens:</strong></p>
            <ol style="margin-left: 20px; padding-left: 0;">
                <li>Acesse: <a href="https://developers.mercadolibre.com.br/devcenter" target="_blank">Mercado Livre DevCenter</a></li>
                <li>Clique em "Minhas aplicações"</li>
                <li>Selecione sua aplicação</li>
                <li>Vá na aba "Test"</li>
                <li>Clique em "Obtenha seu token de teste"</li>
                <li>Copie o <strong>Access Token</strong> e <strong>Refresh Token</strong></li>
            </ol>
        </div>
    `;
    
    // Limpa campos
    document.getElementById('manualAccessToken').value = '';
    document.getElementById('manualRefreshToken').value = '';
    document.getElementById('modalTokensResultado').innerHTML = '';
    
    document.getElementById('modalAdicionarTokens').style.display = 'block';
}

function fecharModalTokens() {
    document.getElementById('modalAdicionarTokens').style.display = 'none';
    contaSelecionadaParaTokens = null;
}

function salvarTokensManualmente() {
    if (!contaSelecionadaParaTokens) return;
    
    const accessToken = document.getElementById('manualAccessToken').value.trim();
    const refreshToken = document.getElementById('manualRefreshToken').value.trim();
    
    if (!accessToken || !refreshToken) {
        mostrarResultadoModal('Preencha ambos os tokens', 'error');
        return;
    }
    
    fetch(`/api/mercadolivre/contas/${contaSelecionadaParaTokens}/adicionar-tokens-manual`, {
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
            mostrarResultadoModal('✅ Tokens salvos com sucesso! Conta pronta para uso.', 'success');
            
            setTimeout(() => {
                fecharModalTokens();
                carregarContasMercadoLivre();
            }, 1500);
        } else {
            mostrarResultadoModal('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarResultadoModal('Erro: ' + error.message, 'error');
    });
}

function completarAutenticacaoML(accountId, accountName) {
    contaSelecionadaParaTokens = accountId;
    abrirModalTokensManual(accountId, accountName);
}

function selecionarContaML(accountId) {
    fetch(`/api/mercadolivre/contas/${accountId}/selecionar`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagemRapida('Conta selecionada!', 'success');
            carregarContasMercadoLivre();
        } else {
            mostrarMensagemRapida('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarMensagemRapida('Erro: ' + error.message, 'error');
    });
}

function testarContaML(accountId) {
    fetch(`/api/mercadolivre/contas/${accountId}/testar`)
        .then(response => response.json())
        .then(data => {
            if (data.sucesso && data.autenticada) {
                mostrarMensagemRapida(`✅ Conta funcionando! Usuário: ${data.nickname}`, 'success');
            } else {
                mostrarMensagemRapida(`❌ Problema na conta: ${data.erro}`, 'error');
            }
        })
        .catch(error => {
            mostrarMensagemRapida('Erro: ' + error.message, 'error');
        });
}

function removerContaML(accountId, accountName) {
    if (!confirm(`Tem certeza que deseja remover a conta "${accountName}"?`)) return;
    
    fetch(`/api/mercadolivre/contas/${accountId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagemRapida('Conta removida!', 'success');
            carregarContasMercadoLivre();
        } else {
            mostrarMensagemRapida('Erro: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        mostrarMensagemRapida('Erro: ' + error.message, 'error');
    });
}

// =========================================
// TESTE DE STATUS
// =========================================

function testarStatusMercadoLivre(contaAtualId) {
    if (!contaAtualId) {
        atualizarStatusML('unknown', 'Nenhuma conta selecionada');
        return;
    }
    
    fetch(`/api/mercadolivre/contas/${contaAtualId}/testar`)
        .then(response => response.json())
        .then(data => {
            if (data.sucesso && data.autenticada) {
                atualizarStatusML('success', `OK - ${data.nickname}`);
            } else {
                atualizarStatusML('error', data.erro || 'Não autenticada');
            }
        })
        .catch(error => {
            atualizarStatusML('error', 'Erro de conexão');
        });
}

function atualizarStatusML(status, mensagem) {
    const elemento = document.getElementById('mlServiceStatus');
    if (!elemento) return;
    
    elemento.className = `status-badge status-${status}`;
    
    const icones = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'unknown': 'fa-question-circle'
    };
    
    elemento.innerHTML = `<i class="fas ${icones[status]}"></i> ${mensagem}`;
}

// =========================================
// FUNÇÕES AUXILIARES
// =========================================

function mostrarToast(mensagem, tipo) {
    const toast = document.createElement('div');
    toast.className = `toast-modern ${tipo}`;
    
    const icones = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icones[tipo]}"></i>
        <span>${mensagem}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function mostrarResultadoML(mensagem, tipo) {
    const container = document.getElementById('novaContaResultado');
    mostrarResultadoNoContainer(container, mensagem, tipo);
}

function mostrarResultadoModal(mensagem, tipo) {
    const container = document.getElementById('modalTokensResultado');
    mostrarResultadoNoContainer(container, mensagem, tipo);
}

function mostrarResultadoNoContainer(container, mensagem, tipo) {
    const classes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    container.innerHTML = `
        <div class="alert ${classes[tipo]} alert-dismissible fade show">
            ${mensagem}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        </div>
    `;
}

function mostrarMensagemRapida(mensagem, tipo) {
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${tipo}`;
    toast.innerHTML = `
        <i class="fas fa-${tipo === 'success' ? 'check' : 'times'}"></i>
        ${mensagem}
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function mostrarErroML(mensagem) {
    mostrarMensagemRapida(mensagem, 'error');
}

function formatarData(dataString) {
    if (!dataString) return 'N/A';
    try {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR');
    } catch {
        return dataString;
    }
}

// =========================================
// INICIALIZAÇÃO
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    // Carrega contas ao abrir a página
    carregarContasMercadoLivre();
    
    // Atualiza a cada 30 segundos
    setInterval(carregarContasMercadoLivre, 30000);
    
    // Fechar modais ao clicar fora
    window.addEventListener('click', function(event) {
        const modalNova = document.getElementById('modalNovaConta');
        const modalTokens = document.getElementById('modalAdicionarTokens');
        
        if (event.target === modalNova) {
            fecharModalNovaConta();
        }
        if (event.target === modalTokens) {
            fecharModalTokens();
        }
    });
});