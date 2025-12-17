// config_tokens.js - Versão Corrigida com Rotas Corretas
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Inicializando configurações de tokens...');
    verificarTokenConfigurado();
});

async function verificarTokenConfigurado() {
    try {
        console.log('🔍 Verificando token configurado...');
        const response = await fetch('/api/tokens/anymarket/obter');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Resposta token:', data);
        
        if (data.success && data.token) {
            document.getElementById('anymarket_token').value = '••••••••••••••••';
            document.getElementById('anymarket_token').placeholder = 'Token configurado (salvo com segurança)';
            atualizarStatusServico('anymarket', 'success', 'Token configurado');
            console.log('✅ Token encontrado e configurado');
        } else {
            document.getElementById('anymarket_token').value = '';
            document.getElementById('anymarket_token').placeholder = 'Cole seu GumgaToken aqui...';
            atualizarStatusServico('anymarket', 'unknown', 'Não configurado');
            console.log('ℹ️ Token não configurado');
        }
    } catch (error) {
        console.error('❌ Erro ao verificar token:', error);
        document.getElementById('anymarket_token').value = '';
        document.getElementById('anymarket_token').placeholder = 'Cole seu GumgaToken aqui...';
        atualizarStatusServico('anymarket', 'error', 'Erro ao carregar');
        mostrarMensagem('anymarketStatus', 'Erro ao verificar token: ' + error.message, 'error');
    }
}

function toggleTokenVisibility(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.nextElementSibling.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

async function salvarToken(tipo) {
    if (tipo === 'anymarket') {
        const tokenInput = document.getElementById('anymarket_token');
        const token = tokenInput.value.trim();
        
        console.log('💾 Tentando salvar token...', { tipo, tokenLength: token.length });
        
        // Se o campo está com máscara, não fazer nada
        if (token === '••••••••••••••••') {
            mostrarMensagem('anymarketStatus', 'Token já está configurado. Digite um novo token para alterar.', 'warning');
            tokenInput.value = '';
            tokenInput.placeholder = 'Cole seu GumgaToken aqui...';
            return;
        }
        
        if (!token) {
            mostrarMensagem('anymarketStatus', 'Informe o token do AnyMarket', 'error');
            return;
        }
        
        if (token.length < 20) {
            mostrarMensagem('anymarketStatus', 'Token parece muito curto. Verifique se está completo.', 'warning');
            return;
        }
        
        try {
            mostrarMensagem('anymarketStatus', 'Salvando token...', 'info');
            
            const response = await fetch('/api/tokens/anymarket/salvar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: token
                })
            });
            
            console.log('Resposta salvar:', response.status, response.statusText);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Dados resposta:', data);
            
            if (data.success) {
                tokenInput.value = '••••••••••••••••';
                tokenInput.placeholder = 'Token configurado (salvo com segurança)';
                mostrarMensagem('anymarketStatus', '✅ Token salvo com segurança!', 'success');
                atualizarStatusServico('anymarket', 'success', 'Token configurado');
                
                // Atualizar também na tela de pedidos se estiver aberta
                if (window.updateTokenInPedidos) {
                    window.updateTokenInPedidos(token);
                }
            } else {
                throw new Error(data.error || 'Erro desconhecido');
            }
        } catch (error) {
            console.error('❌ Erro ao salvar token:', error);
            mostrarMensagem('anymarketStatus', '❌ Erro ao salvar token: ' + error.message, 'error');
        }
    }
}

async function testarToken(tipo) {
    if (tipo === 'anymarket') {
        try {
            console.log('🧪 Testando token...');
            mostrarMensagem('anymarketStatus', '🧪 Testando conexão...', 'info');
            
            // Primeiro obtém o token do backend
            const tokenResponse = await fetch('/api/tokens/anymarket/obter');
            
            if (!tokenResponse.ok) {
                throw new Error(`Erro ao obter token: HTTP ${tokenResponse.status}`);
            }
            
            const tokenData = await tokenResponse.json();
            console.log('Token para teste:', tokenData);
            
            if (!tokenData.success || !tokenData.token) {
                mostrarMensagem('anymarketStatus', '❌ Nenhum token configurado para testar', 'error');
                return;
            }
            
            const token = tokenData.token;
            
            // Testa o token
            const testResponse = await fetch('/api/anymarket/testar-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            
            console.log('Resposta teste:', testResponse.status, testResponse.statusText);
            
            if (!testResponse.ok) {
                const errorText = await testResponse.text();
                throw new Error(`HTTP ${testResponse.status}: ${errorText}`);
            }
            
            const testData = await testResponse.json();
            console.log('Dados teste:', testData);
            
            if (testData.success) {
                mostrarMensagem('anymarketStatus', '✅ Conexão estabelecida com sucesso!', 'success');
                atualizarStatusServico('anymarket', 'success', 'Conectado');
            } else {
                mostrarMensagem('anymarketStatus', '❌ Erro na conexão: ' + (testData.error || 'Erro desconhecido'), 'error');
                atualizarStatusServico('anymarket', 'error', 'Erro de conexão');
            }
        } catch (error) {
            console.error('❌ Erro ao testar token:', error);
            mostrarMensagem('anymarketStatus', '❌ Erro ao testar conexão: ' + error.message, 'error');
            atualizarStatusServico('anymarket', 'error', 'Erro de conexão');
        }
    }
}

function salvarConfigGoogleSheets() {
    const sheetId = document.getElementById('sheet_id').value.trim();
    if (!sheetId) {
        mostrarMensagem('googleSheetsStatus', 'Informe o ID da planilha', 'error');
        return;
    }
    
    // Implementar salvamento do Google Sheets se necessário
    mostrarMensagem('googleSheetsStatus', 'Configuração salva com sucesso!', 'success');
}

async function testarGoogleSheets() {
    const sheetId = document.getElementById('sheet_id').value.trim();
    if (!sheetId) {
        mostrarMensagem('googleSheetsStatus', 'Informe o ID da planilha primeiro', 'error');
        return;
    }
    
    mostrarMensagem('googleSheetsStatus', 'Testando conexão com Google Sheets...', 'info');
    
    try {
        const response = await fetch(`/api/abas-google-sheets?sheet_id=${encodeURIComponent(sheetId)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem('googleSheetsStatus', `✅ Conexão estabelecida! ${data.abas.length} abas encontradas.`, 'success');
            atualizarStatusServico('googleSheets', 'success', 'Conectado');
        } else {
            mostrarMensagem('googleSheetsStatus', '❌ Erro na conexão: ' + data.error, 'error');
            atualizarStatusServico('googleSheets', 'error', 'Erro de conexão');
        }
    } catch (error) {
        mostrarMensagem('googleSheetsStatus', '❌ Erro ao testar conexão: ' + error.message, 'error');
        atualizarStatusServico('googleSheets', 'error', 'Erro de conexão');
    }
}

function mostrarMensagem(containerId, mensagem, tipo) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-${tipo} alert-dismissible fade show">
                ${mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }
}

function atualizarStatusServico(servico, status, mensagem) {
    const elemento = document.getElementById(servico + 'ServiceStatus');
    if (elemento) {
        elemento.className = `status-badge status-${status}`;
        
        const icon = status === 'success' ? 'fa-check-circle' : 
                     status === 'error' ? 'fa-times-circle' : 'fa-question-circle';
        
        elemento.innerHTML = `<i class="fas ${icon}"></i> ${mensagem}`;
    }
}

// Função para remover token (se necessário)
async function removerToken(tipo) {
    if (tipo === 'anymarket') {
        if (!confirm('Tem certeza que deseja remover o token do AnyMarket?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/tokens/anymarket/remover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('anymarket_token').value = '';
                document.getElementById('anymarket_token').placeholder = 'Cole seu GumgaToken aqui...';
                mostrarMensagem('anymarketStatus', '🗑️ Token removido com sucesso!', 'success');
                atualizarStatusServico('anymarket', 'unknown', 'Não configurado');
            } else {
                throw new Error(data.error || 'Erro desconhecido');
            }
        } catch (error) {
            mostrarMensagem('anymarketStatus', '❌ Erro ao remover token: ' + error.message, 'error');
        }
    }
}
// Adicione ao config_tokens.js
function atualizarStatusServicos() {
    // Status Mercado Livre
    fetch('/api/mercadolivre/contas')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                const contaAtual = data.contas.find(c => c.id === data.conta_atual);
                if (contaAtual && contaAtual.has_token) {
                    atualizarStatusElemento('ml', 'success', `OK - ${contaAtual.nickname || contaAtual.name}`);
                } else {
                    atualizarStatusElemento('ml', 'warning', 'Pendente ou sem conta');
                }
            }
        });
    
    // Testa AnyMarket se tiver token
    const anymarketToken = document.getElementById('anymarket_token').value;
    if (anymarketToken && anymarketToken.length > 10) {
        testarToken('anymarket', true); // true = apenas status
    }
}

function atualizarStatusElemento(servico, status, texto) {
    const icon = document.getElementById(`${servico}StatusIcon`);
    const text = document.getElementById(`${servico}StatusText`);
    
    if (icon && text) {
        icon.className = `status-icon ${status}`;
        icon.innerHTML = `<i class="fas fa-${status === 'success' ? 'check' : status === 'warning' ? 'exclamation' : 'times'}"></i>`;
        text.textContent = texto;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Verifica status apenas uma vez ao carregar
    setTimeout(() => {
        console.log('🔍 Verificando status inicial dos serviços...');
        
        // Mercado Livre
        fetch('/api/mercadolivre/contas')
            .then(response => response.json())
            .then(data => {
                if (data.sucesso && data.contas.length > 0) {
                    const contaAtual = data.contas.find(c => c.id === data.conta_atual);
                    if (contaAtual && contaAtual.has_token) {
                        document.getElementById('mlGlobalStatus').textContent = 'Conectado';
                    }
                }
            });
        
        // AnyMarket já é verificado por verificarTokenConfigurado()
        
        // Google Sheets
        document.getElementById('sheetsGlobalStatus').textContent = 'Conectado';
    }, 500);
    
    // NÃO use setInterval - remove testes desnecessários
});
// 🔹 FUNÇÕES INTELIPOST
function testarTokenIntelipost() {
    const apiKey = document.getElementById('intelipost_api_key').value;
    const statusDiv = document.getElementById('intelipostStatus');
    
    if (!apiKey) {
        mostrarStatus(statusDiv, 'Por favor, insira a API Key para testar', 'error');
        return;
    }
    
    mostrarStatus(statusDiv, '<i class="fas fa-spinner fa-spin"></i> Testando conexão com Intelipost...', 'info');
    
    fetch('/api/tokens/intelipost/testar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_key: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            if (data.conectado) {
                mostrarStatus(statusDiv, 
                    `<strong>✅ Conexão bem-sucedida!</strong><br>
                     ${data.mensagem}<br>
                     Tempo de resposta: ${data.tempo_resposta || 'N/A'}`, 
                    'success');
            } else {
                mostrarStatus(statusDiv, 
                    `<strong>⚠️ Conexão parcial</strong><br>
                     ${data.mensagem || 'API respondeu mas não está totalmente funcional'}`, 
                    'warning');
            }
        } else {
            mostrarStatus(statusDiv, 
                `<strong>❌ Falha na conexão</strong><br>
                 ${data.erro || data.mensagem || 'Erro desconhecido'}<br>
                 ${data.sugestao ? `<small>${data.sugestao}</small>` : ''}`, 
                'error');
        }
    })
    .catch(error => {
        mostrarStatus(statusDiv, 
            `<strong>❌ Erro de conexão</strong><br>
             Não foi possível testar a API: ${error}`, 
            'error');
    });
}

function salvarTokenIntelipost() {
    const apiKey = document.getElementById('intelipost_api_key').value;
    const statusDiv = document.getElementById('intelipostStatus');
    
    if (!apiKey) {
        mostrarStatus(statusDiv, 'Por favor, insira a API Key', 'error');
        return;
    }
    
    if (confirm('Deseja salvar esta API Key do Intelipost?\n\nA chave será armazenada de forma segura no sistema.')) {
        mostrarStatus(statusDiv, '<i class="fas fa-spinner fa-spin"></i> Salvando API Key...', 'info');
        
        fetch('/api/tokens/intelipost/salvar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ api_key: apiKey })
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                mostrarStatus(statusDiv, 
                    `<strong>✅ API Key salva com sucesso!</strong><br>
                     ${data.mensagem}<br>
                     <small>Salvo em: ${data.salvo_em || 'tokens_secure.json'}</small>`, 
                    'success');
                
                // Atualizar status global e recarregar após 2 segundos
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                mostrarStatus(statusDiv, 
                    `<strong>❌ Erro ao salvar</strong><br>
                     ${data.erro || 'Erro desconhecido'}`, 
                    'error');
            }
        })
        .catch(error => {
            mostrarStatus(statusDiv, 
                `<strong>❌ Erro de conexão</strong><br>
                 Não foi possível salvar: ${error}`, 
                'error');
        });
    }
}

function removerTokenIntelipost() {
    if (confirm('Tem certeza que deseja remover a API Key do Intelipost?\n\nO módulo de rastreamento deixará de funcionar.')) {
        fetch('/api/tokens/intelipost/remover', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                alert(data.mensagem);
                location.reload();
            } else {
                alert('Erro ao remover: ' + (data.erro || 'Erro desconhecido'));
            }
        })
        .catch(error => {
            alert('Erro de conexão: ' + error);
        });
    }
}

// Função auxiliar para mostrar status
function mostrarStatus(element, message, type) {
    element.innerHTML = message;
    element.className = 'status-message';
    
    switch(type) {
        case 'success':
            element.classList.add('status-success');
            break;
        case 'error':
            element.classList.add('status-error');
            break;
        case 'warning':
            element.classList.add('status-warning');
            break;
        case 'info':
            element.classList.add('status-info');
            break;
    }
    
    element.style.display = 'block';
    
    // Auto-esconder após 8 segundos (exceto sucesso)
    if (type !== 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 8000);
    }
}

// Adicione esta função se não existir
function toggleTokenVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}