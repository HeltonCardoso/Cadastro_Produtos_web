// static/js/mlb_exclusao_simples.js
// SISTEMA SIMPLIFICADO DE EXCLUSÃO - CORRIGIDO PARA MODAIS CUSTOMIZADOS

let mlbAtual = null;
let mlbsParaExcluir = [];

// =========================================
// FUNÇÕES DO MODAL DE EXCLUSÃO
// =========================================

function abrirModalExclusaoPlanilha() {
    console.log('Abrindo modal de exclusão via planilha...');
    
    // Limpa dados anteriores
    mlbsParaExcluir = [];
    document.getElementById('arquivoExclusao').value = '';
    document.getElementById('previewExclusao').innerHTML = '';
    document.getElementById('btnIniciarExclusao').disabled = true;
    
    // Mostra o modal (mesmo padrão dos outros modais)
    document.getElementById('modalExclusaoPlanilha').style.display = 'block';
    
    console.log('✅ Modal de exclusão aberto');
}

function fecharModalExclusaoPlanilha() {
    document.getElementById('modalExclusaoPlanilha').style.display = 'none';
}

// =========================================
// PROCESSAMENTO DO ARQUIVO
// =========================================

function processarPlanilhaExclusao(input) {
    if (!input.files[0]) return;
    
    const file = input.files[0];
    console.log('Arquivo selecionado:', file.name);
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            let mlbs = [];
            const extensao = file.name.split('.').pop().toLowerCase();
            
            console.log('Processando extensão:', extensao);
            
            if (extensao === 'txt' || extensao === 'csv') {
                // Processa texto puro
                const texto = e.target.result;
                console.log('Texto do arquivo (primeiros 200 chars):', texto.substring(0, 200));
                
                mlbs = texto.split(/[\n,;]+/)
                    .map(m => m.trim())
                    .filter(m => m)
                    .map(limparMLB)
                    .filter(m => m);
                    
                console.log('MLBs extraídos do texto:', mlbs.length);
                
            } else if (extensao === 'xlsx' || extensao === 'xls') {
                // Processa Excel
                console.log('Processando Excel...');
                const workbook = XLSX.read(e.target.result, { type: 'array' });
                const sheet = workbook.Sheets[workbook.SheetNames[0]];
                const data = XLSX.utils.sheet_to_json(sheet, { header: 1 });
                
                console.log('Dados brutos do Excel:', data.length, 'linhas');
                
                // Pega todos os valores da planilha e procura MLBs
                mlbs = [];
                data.forEach(linha => {
                    if (Array.isArray(linha)) {
                        linha.forEach(valor => {
                            if (valor && typeof valor === 'string') {
                                const mlbProcessado = limparMLB(valor);
                                if (mlbProcessado) {
                                    mlbs.push(mlbProcessado);
                                }
                            }
                        });
                    }
                });
                
                console.log('MLBs extraídos do Excel:', mlbs.length);
            }
            
            // Remove duplicatas
            mlbsParaExcluir = [...new Set(mlbs)];
            
            console.log('MLBs únicos encontrados:', mlbsParaExcluir.length);
            
            if (mlbsParaExcluir.length === 0) {
                mostrarMensagem('Nenhum MLB válido encontrado no arquivo', 'error');
                return;
            }
            
            // Mostra preview
            mostrarPreviewExclusao(mlbsParaExcluir);
            
        } catch (error) {
            console.error('Erro ao processar arquivo:', error);
            mostrarMensagem('Erro ao processar arquivo: ' + error.message, 'error');
        }
    };
    
    reader.onerror = function(error) {
        console.error('Erro na leitura do arquivo:', error);
        mostrarMensagem('Erro ao ler arquivo', 'error');
    };
    
    if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        reader.readAsArrayBuffer(file);
    } else {
        reader.readAsText(file);
    }
}

function mostrarPreviewExclusao(mlbs) {
    const preview = document.getElementById('previewExclusao');
    
    let html = `<div class="alert alert-info">
        <i class="fas fa-info-circle"></i>
        <strong>${mlbs.length} MLBs encontrados para exclusão</strong>
        <br><small>Serão excluídos permanentemente</small>
    </div>
    <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
        <table class="table table-sm table-striped">
            <thead>
                <tr><th>MLB</th><th>Status</th></tr>
            </thead>
            <tbody>`;
    
    mlbs.slice(0, 20).forEach(mlb => {
        html += `<tr>
            <td><code>${mlb}</code></td>
            <td><span class="badge bg-warning">Aguardando exclusão</span></td>
        </tr>`;
    });
    
    if (mlbs.length > 20) {
        html += `<tr>
            <td colspan="2" class="text-muted text-center">
                <i class="fas fa-ellipsis-h"></i>
                ... e mais ${mlbs.length - 20} MLBs
            </td>
        </tr>`;
    }
    
    html += `</tbody></table></div>`;
    
    preview.innerHTML = html;
    document.getElementById('btnIniciarExclusao').disabled = false;
    
    console.log('Preview gerado para', mlbs.length, 'MLBs');
}

// =========================================
// EXCLUSÃO EM MASSA
// =========================================

function iniciarExclusaoEmMassa() {
    console.log('Iniciando exclusão em massa...', mlbsParaExcluir.length, 'MLBs');
    
    if (mlbsParaExcluir.length === 0) {
        mostrarMensagem('Nenhum MLB para excluir', 'error');
        return;
    }
    
    if (!confirm(`EXCLUIR ${mlbsParaExcluir.length} ANÚNCIOS?\n\nEsta ação é irreversível!`)) {
        console.log('Exclusão cancelada pelo usuário');
        return;
    }
    
    const btn = document.getElementById('btnIniciarExclusao');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Excluindo...';
    btn.disabled = true;
    
    console.log('Enviando para API...');
    
    fetch('/api/mercadolivre/excluir-definitivo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mlbs: mlbsParaExcluir })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Resposta da API:', data);
        
        if (data.sucesso) {
            mostrarMensagem(`✅ Exclusão concluída! Sucesso: ${data.sucessos || data.total_excluidos || 0}, Erros: ${data.erros || 0}`, 'success');
            fecharModalExclusaoPlanilha();
            
            // Atualiza a página se estiver mostrando resultados
            if (window.ultimosResultados && window.ultimosResultados.length > 0) {
                buscarMLBs();
            }
        } else {
            mostrarMensagem(`❌ Erro: ${data.erro || 'Erro desconhecido'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Erro na exclusão:', error);
        mostrarMensagem('Erro de conexão com o servidor', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        console.log('Processo de exclusão finalizado');
    });
}

// =========================================
// EXCLUSÃO INDIVIDUAL
// =========================================

function excluirMLB(mlb) {
    mlbAtual = limparMLB(mlb);
    
    if (!mlbAtual) {
        mostrarMensagem('MLB inválido', 'error');
        return;
    }
    
    if (!confirm(`EXCLUIR ANÚNCIO?\n\nMLB: ${mlbAtual}\n\nEsta ação é irreversível!`)) {
        return;
    }
    
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;
    
    console.log(`Excluindo MLB: ${mlbAtual}`);
    
    fetch('/api/mercadolivre/excluir-definitivo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mlb: mlbAtual })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem(`✅ MLB ${mlbAtual} excluído com sucesso!`, 'success');
            
            // Remove da tabela
            removerDaTabela(mlbAtual);
            
        } else {
            mostrarMensagem(`❌ Erro: ${data.erro || 'Erro desconhecido'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro de conexão', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

// =========================================
// FUNÇÕES AUXILIARES
// =========================================

function limparMLB(mlb) {
    if (!mlb) return null;
    
    let mlbStr = mlb.toString().trim().toUpperCase();
    
    // Remove todos os caracteres não alfanuméricos
    mlbStr = mlbStr.replace(/[^A-Z0-9]/g, '');
    
    if (mlbStr.startsWith('MLB')) {
        return mlbStr;
    } else if (/^\d+$/.test(mlbStr)) {
        return 'MLB' + mlbStr;
    } else if (mlbStr.length > 3) {
        // Tenta encontrar MLB dentro do texto
        const match = mlbStr.match(/MLB\d+/);
        if (match) return match[0];
    }
    
    return null;
}

function removerDaTabela(mlb) {
    const linhas = document.querySelectorAll('#ordersTableBody tr');
    let encontrado = false;
    
    linhas.forEach(linha => {
        const mlbCell = linha.querySelector('td:nth-child(2) strong');
        if (mlbCell && mlbCell.textContent === mlb) {
            linha.style.transition = 'opacity 0.5s';
            linha.style.opacity = '0.3';
            linha.style.textDecoration = 'line-through';
            
            setTimeout(() => {
                linha.remove();
                if (document.querySelectorAll('#ordersTableBody tr').length === 0) {
                    document.getElementById('ordersContainer').classList.add('hidden');
                    document.getElementById('emptyState').classList.remove('hidden');
                }
            }, 1000);
            
            encontrado = true;
        }
    });
    
    if (!encontrado) {
        console.log('MLB não encontrado na tabela:', mlb);
    }
}

function mostrarMensagem(mensagem, tipo) {
    // Cria alerta temporário
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'info'}`;
    alertDiv.innerHTML = `
        <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle'}"></i>
        ${mensagem}
    `;
    
    // Adiciona no container
    const container = document.querySelector('.mercado-livre-container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove após 3 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// =========================================
// INTEGRAÇÃO COM A TABELA
// =========================================

function adicionarBotoesExclusao() {
    document.querySelectorAll('#ordersTableBody tr').forEach(linha => {
        const mlbCell = linha.querySelector('td:nth-child(2) strong');
        const botoesCell = linha.querySelector('td:last-child');
        
        if (mlbCell && botoesCell && !botoesCell.querySelector('.btn-excluir-simples')) {
            const mlb = mlbCell.textContent;
            
            // Cria botão de exclusão
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-outline-danger btn-excluir-simples ms-1';
            btn.innerHTML = '<i class="fas fa-trash-alt"></i>';
            btn.title = 'Excluir anúncio';
            
            // Adiciona evento
            btn.onclick = function(e) {
                e.stopPropagation();
                e.preventDefault();
                excluirMLB(mlb);
            };
            
            botoesCell.appendChild(btn);
        }
    });
}

// =========================================
// INICIALIZAÇÃO
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Sistema de exclusão carregado');
    
    // Configurar evento para o input de arquivo
    const arquivoExclusao = document.getElementById('arquivoExclusao');
    if (arquivoExclusao) {
        arquivoExclusao.addEventListener('change', function(e) {
            processarPlanilhaExclusao(this);
        });
        console.log('✅ Input de arquivo configurado');
    }
    
    // Configurar botão de iniciar exclusão
    const btnIniciarExclusao = document.getElementById('btnIniciarExclusao');
    if (btnIniciarExclusao) {
        btnIniciarExclusao.onclick = iniciarExclusaoEmMassa;
        console.log('✅ Botão iniciar exclusão configurado');
    }
    
    // Adicionar botões de exclusão nas linhas
    setTimeout(adicionarBotoesExclusao, 1000);
    
    // Observar mudanças na tabela
    const tabela = document.getElementById('ordersTableBody');
    if (tabela) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    setTimeout(adicionarBotoesExclusao, 100);
                }
            });
        });
        
        observer.observe(tabela, { childList: true, subtree: true });
        console.log('✅ Observer configurado para tabela');
    }
    
    // Fechar modal ao clicar fora
    const modalExclusao = document.getElementById('modalExclusaoPlanilha');
    if (modalExclusao) {
        modalExclusao.onclick = function(event) {
            if (event.target === modalExclusao) {
                fecharModalExclusaoPlanilha();
            }
        };
        console.log('✅ Evento de fechar modal configurado');
    }
    
    console.log('✅ Sistema de exclusão totalmente inicializado');
});