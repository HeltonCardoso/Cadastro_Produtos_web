// consultar_anymarket.js - Versão completa com diagnóstico

document.addEventListener('DOMContentLoaded', function() {
    initializeFormHandlers();
    initializeSortableGallery();
    initializePhotoSelection();
    initializeEventHandlers();
    initializeSelectAll();
});

function initializeFormHandlers() {
    // Botão consultar
    const btnConsultar = document.getElementById('btnConsultar');
    if (btnConsultar) {
        btnConsultar.addEventListener('click', function() {
            const productId = document.getElementById('product_id').value;
            
            if (!productId) {
                showAlert('Por favor, informe o ID do produto', 'error');
                return;
            }
            
            // Preenche os campos ocultos do formulário
            document.getElementById('hiddenProductId').value = productId;
            
            // Mostra loading
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Consultando...';
            
            // Submete o formulário
            document.getElementById('consultarForm').submit();
        });
    }
    
    // Botão excluir lote
    const btnExcluirLote = document.getElementById('btnExcluirLote');
    if (btnExcluirLote) {
        btnExcluirLote.addEventListener('click', function() {
            const planilha = document.getElementById('planilha').files[0];
            
            if (!planilha) {
                showAlert('Por favor, selecione uma planilha', 'error');
                return;
            }
            
            // Prepara o FormData
            const formData = new FormData();
            formData.append('action', 'excluir_lote');
            formData.append('planilha', planilha);
            
            // Mostra loading
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';
            
            // Envia via AJAX
            fetch(window.location.href, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro na resposta do servidor');
                }
                return response.text();
            })
            .then(html => {
                // Recarrega a página para mostrar resultados
                window.location.reload();
            })
            .catch(error => {
                console.error('Erro:', error);
                showAlert('Erro ao processar planilha: ' + error.message, 'error');
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-trash me-2"></i>Excluir Fotos da Planilha';
            });
        });
    }
}

function initializeSortableGallery() {
    const galeria = document.getElementById('galeriaFotos');
    if (galeria && typeof Sortable !== 'undefined') {
        new Sortable(galeria, {
            animation: 150,
            ghostClass: 'dragging',
            chosenClass: 'selecionada',
            onEnd: function(evt) {
                atualizarNumeracao();
            }
        });
    }
}

function initializePhotoSelection() {
    // Seleção ao clicar no card
    document.querySelectorAll('.card-foto').forEach(card => {
        card.addEventListener('click', function(e) {
            // Não ativar se clicou em um botão ou checkbox
            if (e.target.tagName === 'BUTTON' || 
                e.target.closest('button') || 
                e.target.type === 'checkbox' ||
                e.target.classList.contains('foto-checkbox')) {
                return;
            }
            
            const checkbox = this.querySelector('.foto-selecionada');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                this.classList.toggle('selecionada', checkbox.checked);
                atualizarContadorSelecionadas();
            }
        });
    });

    // Evento direto nos checkboxes
    document.querySelectorAll('.foto-selecionada').forEach(checkbox => {
        checkbox.addEventListener('click', function(e) {
            e.stopPropagation(); // Impede que o evento chegue no card
        });
        
        checkbox.addEventListener('change', function() {
            const card = this.closest('.card-foto');
            if (card) {
                card.classList.toggle('selecionada', this.checked);
                atualizarContadorSelecionadas();
            }
        });
    });
}

function initializeSelectAll() {
    const selecionarTodas = document.getElementById('selecionarTodas');
    if (selecionarTodas) {
        selecionarTodas.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.foto-selecionada');
            const cards = document.querySelectorAll('.card-foto');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            
            cards.forEach(card => {
                card.classList.toggle('selecionada', this.checked);
            });
            
            atualizarContadorSelecionadas();
        });
    }
}

function initializeEventHandlers() {
    // Exclusão individual
    document.querySelectorAll('.btn-excluir-individual').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const productId = this.getAttribute('data-product-id');
            const photoId = this.getAttribute('data-photo-id');
            
            if (productId && photoId) {
                if (confirm(`Tem certeza que deseja excluir a foto ${photoId} do produto ${productId}?`)) {
                    excluirFotoIndividual(productId, photoId, this);
                }
            } else {
                console.error('IDs do produto ou foto não encontrados');
            }
        });
    });

    // Definir como principal
    document.querySelectorAll('.btn-definir-principal').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const productId = this.getAttribute('data-product-id');
            const photoId = this.getAttribute('data-photo-id');
            
            if (productId && photoId) {
                if (confirm(`Tem certeza que deseja definir esta foto como principal?`)) {
                    definirFotoPrincipal(productId, photoId, this);
                }
            }
        });
    });

    // Exclusão em lote
    const btnExcluirSelecionadas = document.getElementById('btnExcluirSelecionadas');
    if (btnExcluirSelecionadas) {
        btnExcluirSelecionadas.addEventListener('click', function(e) {
            e.preventDefault();
            
            const selecionadas = document.querySelectorAll('.foto-selecionada:checked');
            
            if (selecionadas.length === 0) {
                showAlert('Selecione pelo menos uma foto para excluir.', 'error');
                return;
            }

            if (confirm(`Tem certeza que deseja excluir ${selecionadas.length} foto(s) selecionada(s)?`)) {
                excluirFotosEmLote(selecionadas);
            }
        });
    }

    // Salvar ordem
    const btnSalvarOrdem = document.getElementById('btnSalvarOrdem');
    if (btnSalvarOrdem) {
        btnSalvarOrdem.addEventListener('click', function(e) {
            e.preventDefault();
            salvarOrdemFotos();
        });
    }
    
    // Diagnóstico em lote
    const btnDiagnosticar = document.getElementById('btnDiagnosticar');
    if (btnDiagnosticar) {
        btnDiagnosticar.addEventListener('click', function() {
            diagnosticarMultiplosProdutos();
        });
    }
    
    // Exportar diagnóstico
    const btnExportarDiagnostico = document.getElementById('btnExportarDiagnostico');
    if (btnExportarDiagnostico) {
        btnExportarDiagnostico.addEventListener('click', function() {
            exportarDiagnosticoExcel();
        });
    }
}

function atualizarContadorSelecionadas() {
    const selecionadas = document.querySelectorAll('.foto-selecionada:checked');
    const quantidadeSelecionadas = document.getElementById('quantidadeSelecionadas');
    const acoesLote = document.getElementById('acoesLote');
    
    if (quantidadeSelecionadas) {
        quantidadeSelecionadas.textContent = selecionadas.length;
    }
    
    if (acoesLote) {
        acoesLote.style.display = selecionadas.length > 0 ? 'block' : 'none';
    }
    
    // Atualiza o checkbox "Selecionar todas"
    const selecionarTodas = document.getElementById('selecionarTodas');
    if (selecionarTodas) {
        const totalFotos = document.querySelectorAll('.foto-selecionada').length;
        selecionarTodas.checked = selecionadas.length === totalFotos && totalFotos > 0;
        selecionarTodas.indeterminate = selecionadas.length > 0 && selecionadas.length < totalFotos;
    }
}

function atualizarNumeracao() {
    document.querySelectorAll('.card-foto').forEach((card, index) => {
        const posicaoElement = card.querySelector('.posicao-atual');
        if (posicaoElement) {
            posicaoElement.textContent = index + 1;
        }
        
        // Atualiza também o índice visual
        const indiceElement = card.querySelector('.foto-indice');
        if (indiceElement) {
            indiceElement.textContent = index + 1;
        }
    });
}

function excluirFotoIndividual(productId, photoId, button) {
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Excluindo...';

    fetch('/excluir-foto-anymarket', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            photo_id: photoId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na resposta do servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.sucesso) {
            showToast('Foto excluída com sucesso!', 'success');
            // Remove o card da foto
            const card = button.closest('.card-foto');
            if (card) {
                card.style.opacity = '0.5';
                card.style.pointerEvents = 'none';
                button.innerHTML = '<i class="fas fa-check me-1"></i>Excluída';
                
                // Atualiza contador
                setTimeout(() => {
                    atualizarContadorSelecionadas();
                }, 100);
            }
        } else {
            throw new Error(data.erro || 'Erro desconhecido');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('Erro ao excluir foto: ' + error.message, 'error');
        button.disabled = false;
        button.innerHTML = originalHTML;
    });
}

function definirFotoPrincipal(productId, photoId, button) {
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Alterando...';

    // Implementar chamada API para definir como principal
    fetch('/definir-foto-principal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            photo_id: photoId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            showToast('Foto definida como principal!', 'success');
            // Atualiza a interface
            location.reload(); // Ou atualize apenas os elementos necessários
        } else {
            throw new Error(data.erro || 'Erro ao definir foto principal');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('Erro: ' + error.message, 'error');
        button.disabled = false;
        button.innerHTML = originalHTML;
    });
}

function salvarOrdemFotos() {
    const fotos = Array.from(document.querySelectorAll('.card-foto')).map((card, index) => ({
        product_id: card.getAttribute('data-product-id'),
        photo_id: card.getAttribute('data-foto-id'),
        new_index: index
    }));

    const btnSalvarOrdem = document.getElementById('btnSalvarOrdem');
    const originalHTML = btnSalvarOrdem.innerHTML;
    btnSalvarOrdem.disabled = true;
    btnSalvarOrdem.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Salvando...';

    if (fotos.length === 0) {
        showToast('Nenhuma foto para salvar ordem', 'warning');
        btnSalvarOrdem.disabled = false;
        btnSalvarOrdem.innerHTML = originalHTML;
        return;
    }

    fetch('/salvar-ordem-fotos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fotos: fotos })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.sucesso) {
            showToast('Ordem das fotos salva com sucesso!', 'success');
        } else {
            throw new Error(data.erro || 'Erro ao salvar ordem');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('Erro ao salvar ordem: ' + error.message, 'error');
    })
    .finally(() => {
        btnSalvarOrdem.disabled = false;
        btnSalvarOrdem.innerHTML = originalHTML;
    });
}

function excluirFotosEmLote(selecionadas) {
    const btn = document.getElementById('btnExcluirSelecionadas');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Excluindo...';

    const exclusoes = Array.from(selecionadas).map(checkbox => ({
        product_id: checkbox.getAttribute('data-product-id'),
        photo_id: checkbox.getAttribute('data-photo-id')
    }));

    fetch('/excluir-fotos-lote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fotos: exclusoes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            showToast(`${data.total_sucesso} foto(s) excluída(s) com sucesso!`, 'success');
            // Recarrega a página após 2 segundos
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            throw new Error(data.erro || 'Erro ao excluir fotos');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('Erro ao excluir fotos: ' + error.message, 'error');
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    });
}

// ============================================
// FUNÇÕES DE DIAGNÓSTICO EM LOTE
// ============================================

function diagnosticarMultiplosProdutos() {
    const input = document.getElementById('multi_product_ids');
    const idsTexto = input.value.trim();
    
    if (!idsTexto) {
        showAlert('Digite pelo menos um ID de produto', 'error');
        return;
    }
    
    // Parse dos IDs
    const ids = idsTexto
        .split(/[,\n]/)
        .map(id => id.trim())
        .filter(id => id.length > 0 && !isNaN(id))
        .slice(0, 1000); // Limitar a 20 produtos
    
    if (ids.length === 0) {
        showAlert('Nenhum ID válido encontrado. Digite números válidos.', 'error');
        return;
    }
    
    // Mostrar loading
    const btn = document.getElementById('btnDiagnosticar');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analisando...';
    
    // Limpar resultados anteriores
    document.getElementById('resultadosDiagnostico').style.display = 'none';
    document.getElementById('btnExportarDiagnostico').style.display = 'none';
    document.getElementById('listaProdutosErro').style.display = 'none';
    
    const inicio = Date.now();
    const resultados = [];
    let processados = 0;
    let totalErros = 0;
    let totalOk = 0;
    
    // Função para processar um produto
    async function processarProduto(productId, index) {
        try {
            // Usar a nova API de diagnóstico
            const response = await fetch('/api/anymarket/diagnosticar-produto', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ product_id: productId })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const resultado = await response.json();
            resultados.push({
                productId: productId,
                resultado: resultado
            });
            
            // Atualizar contadores
            if (resultado.imagens_com_erro && resultado.imagens_com_erro.length > 0) {
                totalErros += resultado.imagens_com_erro.length;
            }
            if (resultado.imagens_ok && resultado.imagens_ok.length > 0) {
                totalOk += resultado.imagens_ok.length;
            }
            
        } catch (error) {
            console.error(`Erro ao processar ${productId}:`, error);
            resultados.push({
                productId: productId,
                resultado: {
                    sucesso: false,
                    erro: error.message,
                    imagens_com_erro: [],
                    imagens_ok: []
                }
            });
        } finally {
            processados++;
            
            // Atualizar progresso
            const progresso = Math.round((processados / ids.length) * 100);
            btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Analisando... ${progresso}%`;
        }
    }
    
    // Processar todos os produtos sequencialmente com delay
    async function processarTodos() {
        for (let i = 0; i < ids.length; i++) {
            await processarProduto(ids[i], i);
            // Delay de 500ms entre requisições para não sobrecarregar a API
            if (i < ids.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        
        // Finalizar processamento
        const tempoTotal = ((Date.now() - inicio) / 1000).toFixed(1);
        
        // Atualizar interface
        atualizarResultadosDiagnostico(resultados, {
            totalProdutos: ids.length,
            totalErros: totalErros,
            totalOk: totalOk,
            tempoExecucao: tempoTotal
        });
        
        // Resetar botão
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
    
    processarTodos();
}

function atualizarResultadosDiagnostico(resultados, estatisticas) {
    // Atualizar estatísticas
    document.getElementById('totalProdutos').textContent = estatisticas.totalProdutos;
    document.getElementById('totalErros').textContent = estatisticas.totalErros;
    document.getElementById('totalOk').textContent = estatisticas.totalOk;
    document.getElementById('tempoExecucao').textContent = `${estatisticas.tempoExecucao}s`;
    
    // Preencher tabela
    const tbody = document.getElementById('corpoTabelaDiagnostico');
    tbody.innerHTML = '';
    
    // Coletar todos os produtos com erros
    const produtosComErro = [];
    let dadosExportacao = [];
    
    resultados.forEach(resultado => {
        if (resultado.resultado.imagens_com_erro && resultado.resultado.imagens_com_erro.length > 0) {
            produtosComErro.push(resultado.productId);
            
            resultado.resultado.imagens_com_erro.forEach(erro => {
                const row = document.createElement('tr');
                row.className = 'table-warning';
                
                // Cor diferente para tipos de erro
                let badgeClass = 'bg-danger';
                if (erro.tipo_erro === 'STATUS_PROBLEMATICO') badgeClass = 'bg-warning';
                if (erro.tipo_erro === 'ESTRUTURA_INCOMPLETA') badgeClass = 'bg-info';
                
                // URL curta para exibição
                let urlCurta = erro.url || 'N/A';
                if (urlCurta.length > 40) {
                    urlCurta = urlCurta.substring(0, 37) + '...';
                }
                
                // Mensagem de erro resumida
                let erroDescricao = erro.erro || erro.tipo_erro || 'Erro desconhecido';
                if (erroDescricao.length > 60) {
                    erroDescricao = erroDescricao.substring(0, 57) + '...';
                }
                
                row.innerHTML = `
                    <td><strong>${resultado.productId}</strong></td>
                    <td><code>${erro.id || 'N/A'}</code></td>
                    <td><span class="badge bg-secondary">${erro.index || 'N/A'}</span></td>
                    <td><span class="badge ${badgeClass}">${erro.tipo_erro || 'ERRO'}</span></td>
                    <td><small title="${erro.erro || ''}">${erroDescricao}</small></td>
                    <td><small class="text-truncate d-block" style="max-width: 120px;" title="${erro.url || ''}">${urlCurta}</small></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="irParaProduto('${resultado.productId}')" title="Ir para este produto">
                            <i class="fas fa-external-link-alt"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger mt-1" onclick="excluirImagemErro('${resultado.productId}', '${erro.id}')" title="Excluir esta imagem">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
                
                // Adicionar para exportação
                dadosExportacao.push({
                    'ID_PRODUTO': resultado.productId,
                    'ID_IMG': erro.id || '',
                    'POSICAO': erro.index || '',
                    'TIPO_ERRO': erro.tipo_erro || '',
                    'ERRO_DESCRICAO': erro.erro || '',
                    'URL': erro.url || ''
                });
            });
        }
    });
    
    // Mostrar mensagem se não houver erros
    if (produtosComErro.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="7" class="text-center text-muted py-4">
                <i class="fas fa-check-circle fa-2x text-success mb-2"></i><br>
                <strong>Nenhuma imagem com erro encontrada!</strong><br>
                <small>${estatisticas.totalProdutos} produtos analisados, todas as imagens estão OK.</small>
            </td>
        `;
        tbody.appendChild(row);
    }
    
    // Mostrar/ocultar lista de produtos
    const listaProdutosErro = document.getElementById('listaProdutosErro');
    const listaProdutos = document.getElementById('listaProdutos');
    
    if (produtosComErro.length > 0) {
        listaProdutosErro.style.display = 'block';
        listaProdutos.innerHTML = '';
        
        produtosComErro.forEach(productId => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-warning me-1 mb-1';
            badge.style.cursor = 'pointer';
            badge.innerHTML = `<i class="fas fa-external-link-alt me-1"></i>${productId}`;
            badge.onclick = () => irParaProduto(productId);
            listaProdutos.appendChild(badge);
        });
    } else {
        listaProdutosErro.style.display = 'none';
    }
    
    // Armazenar dados para exportação
    window.dadosExportacaoDiagnostico = dadosExportacao;
    
    // Mostrar resultados
    document.getElementById('resultadosDiagnostico').style.display = 'block';
    if (dadosExportacao.length > 0) {
        document.getElementById('btnExportarDiagnostico').style.display = 'inline-block';
    }
}

// Nova função para excluir imagem com erro diretamente da tabela
function excluirImagemErro(productId, photoId) {
    if (confirm(`Excluir imagem ${photoId} do produto ${productId}?`)) {
        fetch('/excluir-foto-anymarket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                photo_id: photoId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                showToast('Imagem excluída! Atualizando diagnóstico...', 'success');
                // Recarregar diagnóstico após 1 segundo
                setTimeout(() => {
                    diagnosticarMultiplosProdutos();
                }, 1000);
            } else {
                showToast(`Erro: ${data.erro}`, 'error');
            }
        })
        .catch(error => {
            showToast(`Erro: ${error.message}`, 'error');
        });
    }
}

function irParaProduto(productId) {
    // Muda para a aba de consulta e preenche o ID
    document.getElementById('consultar-tab').click();
    document.getElementById('product_id').value = productId;
    
    // Rolagem suave para o formulário
    document.getElementById('product_id').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('product_id').focus();
}

function exportarDiagnosticoExcel() {
    if (!window.dadosExportacaoDiagnostico || window.dadosExportacaoDiagnostico.length === 0) {
        showAlert('Nenhum dado para exportar', 'warning');
        return;
    }
    
    // Criar CSV no formato que você precisa (ID_PRODUTO|ID_IMG)
    let csvContent = 'ID_PRODUTO|ID_IMG\n';
    
    window.dadosExportacaoDiagnostico.forEach(item => {
        csvContent += `${item.ID_PRODUTO}|${item.ID_IMG}\n`;
    });
    
    // Criar blob e download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.href = url;
    link.download = `diagnostico_imagens_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
    
    URL.revokeObjectURL(url);
    
    showToast('Exportação concluída!', 'success');
}

// ============================================
// FUNÇÕES UTILITÁRIAS
// ============================================

// Sistema de Alertas
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.style.marginBottom = '20px';
    alertDiv.style.marginTop = '10px';
    alertDiv.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insere após o header
    const content = document.querySelector('.pedidos-content');
    if (content) {
        content.insertBefore(alertDiv, content.firstChild);
    } else {
        document.body.insertBefore(alertDiv, document.body.firstChild);
    }
    
    // Remove após 5 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Toast notification
function showToast(message, type = 'info') {
    // Remove toasts antigos
    document.querySelectorAll('.toast-notification').forEach(toast => {
        toast.remove();
    });
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show toast-notification`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.style.maxWidth = '400px';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.borderRadius = '8px';
    toast.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" style="font-size: 0.7rem;"></button>
    `;
    document.body.appendChild(toast);
    
    // Remove automaticamente após 4 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 4000);
}