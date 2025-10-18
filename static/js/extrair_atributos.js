// extrair_atributos.js - JavaScript para extração de atributos

document.addEventListener('DOMContentLoaded', function() {
    initializeGoogleSheetsForm();
    initializeTableFunctions();
    initializeTabBehavior();
});

function initializeGoogleSheetsForm() {
    const btnBuscarAbas = document.getElementById('btnBuscarAbas');
    const btnVisualizar = document.getElementById('btnVisualizar');
    const btnExtrair = document.getElementById('btnExtrair');
    const form = document.getElementById('googleForm');
    const actionType = document.getElementById('action_type');

    if (btnBuscarAbas) {
        btnBuscarAbas.addEventListener('click', function() {
            const sheetId = document.getElementById('sheet_id').value.trim();
            if (!sheetId) {
                alert('Informe o ID da planilha primeiro');
                return;
            }
            
            // Mostrar loading
            const originalText = btnBuscarAbas.innerHTML;
            btnBuscarAbas.disabled = true;
            btnBuscarAbas.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Buscando...';
            
            actionType.value = 'listar_abas';
            form.submit();
        });
    }

    if (btnVisualizar) {
        btnVisualizar.addEventListener('click', function() {
            if (!validarSelecaoAba()) return;
            
            // Mostrar loading
            const originalText = btnVisualizar.innerHTML;
            btnVisualizar.disabled = true;
            btnVisualizar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Carregando...';
            
            actionType.value = 'preview_aba';
            form.submit();
        });
    }

    if (btnExtrair) {
        btnExtrair.addEventListener('click', function() {
            if (!validarSelecaoAba()) return;
            
            // Mostrar loading
            btnExtrair.disabled = true;
            btnExtrair.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Extraindo...';
            
            actionType.value = 'conectar_google';
            form.submit();
        });
    }

    // Buscar abas automaticamente
    document.getElementById('sheet_id')?.addEventListener('blur', function() {
        const sheetId = this.value.trim();
        if (sheetId) {
            buscarAbasViaAPI(sheetId);
        }
    });
}

function validarSelecaoAba() {
    const sheetId = document.getElementById('sheet_id').value.trim();
    const aba = document.getElementById('aba_nome')?.value;
    
    if (!sheetId) {
        alert('Informe o ID da planilha primeiro');
        return false;
    }
    
    if (!aba) {
        alert('Selecione uma aba primeiro');
        return false;
    }
    
    return true;
}

function buscarAbasViaAPI(sheetId) {
    fetch(`/api/abas-google-sheets-visiveis?sheet_id=${encodeURIComponent(sheetId)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('aba_nome');
                select.innerHTML = '<option value="">Selecione uma aba...</option>';
                
                data.abas.forEach(aba => {
                    const option = document.createElement('option');
                    option.value = aba.title;
                    option.textContent = `${aba.title} (${aba.row_count} linhas)`;
                    select.appendChild(option);
                });
                
                showToast(`${data.abas.length} abas visíveis encontradas`, 'success');
            } else {
                showToast('Erro: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showToast('Erro ao buscar abas', 'error');
        });
}

function initializeTableFunctions() {
    // Estas funções serão disponíveis globalmente para o template
    window.scrollTableHorizontal = function(distance) {
        const tableBody = document.querySelector('.table-body-scroll');
        if (tableBody) {
            tableBody.scrollBy({ left: distance, behavior: 'smooth' });
            
            const tableHeader = document.querySelector('.table-header-fixed');
            if (tableHeader) {
                tableHeader.scrollLeft = tableBody.scrollLeft;
            }
        }
    };

    window.toggleFullscreen = function() {
        const container = document.getElementById('tableContainer');
        const button = document.querySelector('[onclick="toggleFullscreen()"]');
        if (!container || !button) return;
        
        const icon = button.querySelector('i');
        
        if (container.classList.contains('fullscreen')) {
            container.classList.remove('fullscreen');
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
            button.innerHTML = '<i class="fas fa-expand"></i>';
        } else {
            container.classList.add('fullscreen');
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
            button.innerHTML = '<i class="fas fa-compress"></i>';
        }
    };

    // Sincroniza scroll horizontal
    const tableBody = document.querySelector('.table-body-scroll');
    if (tableBody) {
        tableBody.addEventListener('scroll', function() {
            const tableHeader = document.querySelector('.table-header-fixed');
            if (tableHeader) {
                tableHeader.scrollLeft = this.scrollLeft;
            }
        });
    }

    // Navegação com teclado
    document.addEventListener('keydown', function(e) {
        const tableBody = document.querySelector('.table-body-scroll');
        if (tableBody && document.activeElement.closest('.table-container-fixed')) {
            if (e.key === 'ArrowLeft') {
                scrollTableHorizontal(-100);
                e.preventDefault();
            } else if (e.key === 'ArrowRight') {
                scrollTableHorizontal(100);
                e.preventDefault();
            } else if (e.key === 'Escape') {
                const container = document.getElementById('tableContainer');
                if (container && container.classList.contains('fullscreen')) {
                    toggleFullscreen();
                }
            }
        }
    });

    // Tooltips
    const cells = document.querySelectorAll('.cell-content');
    cells.forEach(cell => {
        if (cell.scrollWidth > cell.offsetWidth) {
            cell.setAttribute('data-bs-toggle', 'tooltip');
        }
    });
    
    // Inicializa tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Ajuste automático de largura
    setTimeout(adjustColumnWidths, 100);
}

function adjustColumnWidths() {
    const headerCells = document.querySelectorAll('.table-header-fixed th');
    const bodyCells = document.querySelectorAll('.table-body-scroll td');
    
    headerCells.forEach((headerCell, index) => {
        const bodyCell = bodyCells[index];
        if (bodyCell) {
            const maxWidth = Math.max(headerCell.scrollWidth, bodyCell.scrollWidth);
            headerCell.style.minWidth = maxWidth + 'px';
            bodyCell.style.minWidth = maxWidth + 'px';
        }
    });
}

function initializeTabBehavior() {
    // Mantém a aba ativa após recarregar a página
    const urlParams = new URLSearchParams(window.location.search);
    const abaParam = urlParams.get('aba');
    
    if (abaParam === 'google') {
        const googleTab = new bootstrap.Tab(document.getElementById('google-tab'));
        googleTab.show();
    }

    // Adiciona parâmetro na URL ao interagir
    document.getElementById('google-tab')?.addEventListener('click', function() {
        window.history.replaceState({}, '', '?aba=google');
    });

    document.getElementById('upload-tab')?.addEventListener('click', function() {
        window.history.replaceState({}, '', '?aba=upload');
    });
}

// Função global para mostrar processamento no upload
function mostrarProcessando() {
    const botao = document.getElementById("btnProcessar");
    if (botao) {
        botao.disabled = true;
        botao.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Processando...`;
    }
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