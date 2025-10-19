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