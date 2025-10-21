// consultar_anymarket.js - Versão corrigida

document.addEventListener('DOMContentLoaded', function() {
    initializeFormHandlers();
    initializeSortableGallery();
    initializePhotoSelection();
    initializeEventHandlers();
    initializeSelectAll();
});

function initializeFormHandlers() {
    // Botão consultar - CORREÇÃO: usa type="button" e submit programático
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
    
    // Botão excluir lote - CORREÇÃO: usa type="button"
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

    // ✅ CORREÇÃO: Verifica se há fotos para salvar
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
        // ✅ CORREÇÃO: Verifica se a resposta é JSON válido
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

// Sistema de Alertas
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type}`;
    alertDiv.style.marginBottom = '20px';
    alertDiv.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
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
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    // Remove automaticamente após 4 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 4000);
}