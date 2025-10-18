// consultar_anymarket.js - Versão corrigida

document.addEventListener('DOMContentLoaded', function() {
    initializeSortableGallery();
    initializePhotoSelection();
    initializeEventHandlers();
    initializeSelectAll();
});

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
    // Seleção ao clicar no card - CORRIGIDO
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

    // Evento direto nos checkboxes - CORRIGIDO
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
    // Exclusão individual - CORRIGIDO
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

    // Definir como principal - CORRIGIDO
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

    // Exclusão em lote - CORRIGIDO
    const btnExcluirSelecionadas = document.getElementById('btnExcluirSelecionadas');
    if (btnExcluirSelecionadas) {
        btnExcluirSelecionadas.addEventListener('click', function(e) {
            e.preventDefault();
            
            const selecionadas = document.querySelectorAll('.foto-selecionada:checked');
            
            if (selecionadas.length === 0) {
                alert('Selecione pelo menos uma foto para excluir.');
                return;
            }

            if (confirm(`Tem certeza que deseja excluir ${selecionadas.length} foto(s) selecionada(s)?`)) {
                excluirFotosEmLote(selecionadas);
            }
        });
    }

    // Salvar ordem - CORRIGIDO
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

    fetch('/salvar-ordem-fotos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fotos: fotos })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            showToast('Ordem das fotos salva com sucesso!', 'success');
        } else {
            throw new Error(data.erro || 'Erro ao salvar ordem');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('Erro: ' + error.message, 'error');
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

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}