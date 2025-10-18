// preencher_planilha.js - JavaScript para preenchimento de planilha

document.addEventListener('DOMContentLoaded', function() {
    initializeGoogleSheetsForm();
    initializeTabBehavior();
});

function initializeGoogleSheetsForm() {
    const form = document.getElementById('googleForm');
    const actionType = document.getElementById('action_type');

    const btnBuscarAbas = document.getElementById('btnBuscarAbas');
    const btnVisualizar = document.getElementById('btnVisualizar');
    const btnExtrair = document.getElementById('btnExtrair');

    if (btnBuscarAbas) {
        btnBuscarAbas.addEventListener('click', function() {
            actionType.value = 'listar_abas';
            form.submit();
        });
    }

    if (btnVisualizar) {
        btnVisualizar.addEventListener('click', function() {
            actionType.value = 'preview_aba';
            form.submit();
        });
    }

    if (btnExtrair) {
        btnExtrair.addEventListener('click', function() {
            btnExtrair.disabled = true;
            btnExtrair.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';
            actionType.value = 'conectar_google';
            form.submit();
        });
    }
}

function initializeTabBehavior() {
    // Mantém a aba ativa após recarregar a página
    const urlParams = new URLSearchParams(window.location.search);
    const abaParam = urlParams.get('aba');
    
    if (abaParam === 'google') {
        const googleTab = new bootstrap.Tab(document.getElementById('google-tab'));
        googleTab.show();
    }

    // Adiciona parâmetro na URL ao interagir com a aba Google
    document.getElementById('google-tab')?.addEventListener('click', function() {
        window.history.replaceState({}, '', '?aba=google');
    });

    document.getElementById('upload-tab')?.addEventListener('click', function() {
        window.history.replaceState({}, '', '?aba=upload');
    });
}

// Função global para mostrar processamento
function mostrarProcessando() {
    const botao = document.getElementById("btnProcessar");
    if (botao) {
        botao.disabled = true;
        botao.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Processando...`;
    }
}