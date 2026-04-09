// ============================================
// GOOGLE SHEETS OAuth 2.0
// ============================================

async function conectarGoogleSheets() {
    const statusDiv = document.getElementById('googleSheetsStatus');
    statusDiv.innerHTML = '<div class="loading">🔐 Redirecionando para Google...</div>';
    
    // Redireciona para o fluxo OAuth
    window.location.href = '/google/auth';
}

async function verificarStatusGoogle() {
    try {
        const response = await fetch('/api/google/status');
        const data = await response.json();
        
        const badge = document.getElementById('googleSheetsBadge');
        const btnConectar = document.getElementById('btnConectarGoogle');
        const btnDesconectar = document.getElementById('btnDesconectarGoogle');
        const btnSelecionarPlanilha = document.getElementById('btnSelecionarPlanilha');
        const accountInfo = document.getElementById('googleAccountInfo');
        
        if (data.connected) {
            badge.innerHTML = '<span class="badge badge-success"><i class="fab fa-google"></i> Conectado</span>';
            btnConectar.style.display = 'none';
            btnDesconectar.style.display = 'inline-block';
            btnSelecionarPlanilha.style.display = 'inline-block';
            
            accountInfo.innerHTML = `
                <div class="info-success">
                    <i class="fab fa-google"></i>
                    <strong>✅ Conectado ao Google Sheets</strong>
                    ${data.expires_at ? `<br><small>Expira em: ${new Date(data.expires_at).toLocaleString()}</small>` : ''}
                </div>
            `;
            
            // Carrega planilhas recentes
            carregarPlanilhasRecentes();
        } else {
            badge.innerHTML = '<span class="badge badge-warning"><i class="fab fa-google"></i> Desconectado</span>';
            btnConectar.style.display = 'inline-block';
            btnDesconectar.style.display = 'none';
            btnSelecionarPlanilha.style.display = 'none';
            
            accountInfo.innerHTML = `
                <div class="info-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Não conectado</strong>
                    <br><small>Clique em "Conectar com Google" para começar</small>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao verificar status:', error);
    }
}

async function desconectarGoogleSheets() {
    if (!confirm('Tem certeza que deseja desconectar sua conta do Google?')) {
        return;
    }
    
    try {
        const response = await fetch('/google/revoke');
        const data = await response.json();
        
        if (data.success) {
            verificarStatusGoogle();
            mostrarMensagem('success', 'Conta Google desconectada com sucesso!');
        } else {
            mostrarMensagem('error', data.error);
        }
    } catch (error) {
        mostrarMensagem('error', error.message);
    }
}

async function carregarPlanilhasRecentes() {
    try {
        const response = await fetch('/api/google/sheets/list');
        const data = await response.json();
        
        if (data.success && data.sheets && data.sheets.length > 0) {
            const recentSheets = document.getElementById('recentSheets');
            const sheetsList = document.getElementById('sheetsList');
            
            sheetsList.innerHTML = data.sheets.map(sheet => `
                <div class="sheet-item" onclick="selecionarPlanilhaDaLista('${sheet.id}', '${sheet.name.replace(/'/g, "\\'")}')">
                    <i class="fas fa-table"></i>
                    <div class="sheet-info">
                        <strong>${escapeHtml(sheet.name)}</strong>
                        <small>ID: ${sheet.id}</small>
                    </div>
                    <button class="btn-sm" onclick="event.stopPropagation(); copiarIdPlanilha('${sheet.id}')">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
            `).join('');
            
            recentSheets.style.display = 'block';
        }
    } catch (error) {
        console.error('Erro ao carregar planilhas:', error);
    }
}

function selecionarPlanilhaDaLista(id, nome) {
    document.getElementById('sheet_id').value = id;
    mostrarMensagem('success', `Planilha "${nome}" selecionada!`);
}

function copiarIdPlanilha(id) {
    navigator.clipboard.writeText(id);
    mostrarMensagem('success', 'ID da planilha copiado!');
}

async function selecionarPlanilhaGoogle() {
    try {
        const response = await fetch('/api/google/sheets/list');
        const data = await response.json();
        
        if (data.success && data.sheets) {
            // Abre modal com lista de planilhas
            abrirModalPlanilhas(data.sheets);
        } else {
            mostrarMensagem('error', 'Não foi possível carregar suas planilhas');
        }
    } catch (error) {
        mostrarMensagem('error', error.message);
    }
}

function abrirModalPlanilhas(sheets) {
    // Cria modal dinâmico
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-container" style="max-width: 600px;">
            <div class="modal-header">
                <h3><i class="fab fa-google"></i> Suas Planilhas</h3>
                <button class="close-modal" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <input type="text" id="searchSheet" placeholder="🔍 Buscar planilha..." class="form-control" style="margin-bottom: 15px;">
                <div id="modalSheetsList" class="sheets-list-modal">
                    ${sheets.map(sheet => `
                        <div class="sheet-item" onclick="selecionarPlanilhaDaLista('${sheet.id}', '${sheet.name.replace(/'/g, "\\'")}'); document.querySelector('.modal-overlay').remove()">
                            <i class="fas fa-table"></i>
                            <div>
                                <strong>${escapeHtml(sheet.name)}</strong>
                                <br><small>${sheet.id}</small>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Adiciona busca
    const searchInput = modal.querySelector('#searchSheet');
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const items = modal.querySelectorAll('.sheet-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(term) ? 'flex' : 'none';
        });
    });
}

async function testarGoogleSheets() {
    const sheet_id = document.getElementById('sheet_id').value;
    
    if (!sheet_id) {
        mostrarMensagem('warning', 'Informe o ID da planilha primeiro');
        return;
    }
    
    mostrarMensagem('loading', 'Testando conexão...');
    
    try {
        const response = await fetch('/api/google/sheets/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sheet_id })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem('success', `✅ ${data.message}`);
            
            // Mostra preview se disponível
            if (data.preview) {
                mostrarPreviewPlanilha(data.preview);
            }
        } else {
            mostrarMensagem('error', data.error);
        }
    } catch (error) {
        mostrarMensagem('error', error.message);
    }
}

function mostrarPreviewPlanilha(preview) {
    const statusDiv = document.getElementById('googleSheetsStatus');
    statusDiv.innerHTML += `
        <div class="preview-info">
            <h4>📊 Informações da Planilha</h4>
            <ul>
                <li><strong>Total de linhas:</strong> ${preview.total_linhas}</li>
                <li><strong>Total de colunas:</strong> ${preview.total_colunas}</li>
                <li><strong>Abas disponíveis:</strong> ${preview.abas.join(', ')}</li>
            </ul>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function mostrarMensagem(tipo, mensagem) {
    const statusDiv = document.getElementById('googleSheetsStatus');
    const className = tipo === 'success' ? 'success' : (tipo === 'error' ? 'error' : 'loading');
    statusDiv.innerHTML = `<div class="${className}">${mensagem}</div>`;
    
    setTimeout(() => {
        if (statusDiv.innerHTML === `<div class="${className}">${mensagem}</div>`) {
            statusDiv.innerHTML = '';
        }
    }, 5000);
}

// Inicializa
document.addEventListener('DOMContentLoaded', () => {
    verificarStatusGoogle();
    carregarConfigGoogleSheets();
});