// Aplicação principal e inicialização
let debugMode = false;

function toggleDebug() {
    debugMode = !debugMode;
    document.getElementById('debugInfo').classList.toggle('hidden', !debugMode);
    if (debugMode) {
        mostrarDebug('Modo debug ativado.');
    }
}

function mostrarDebug(mensagem) {
    if (!debugMode) return;
    const debugDiv = document.getElementById('debugInfo');
    const timestamp = new Date().toLocaleTimeString();
    debugDiv.innerHTML += `[${timestamp}] ${mensagem}\n`;
    debugDiv.scrollTop = debugDiv.scrollHeight;
}

function limparDebug() {
    document.getElementById('debugInfo').innerHTML = '';
}

// Inicialização da aplicação
function inicializarApp() {
    // Preencher data padrão (últimos 7 dias)
    const hoje = new Date();
    const seteDiasAtras = new Date();
    seteDiasAtras.setDate(hoje.getDate() - 7);
    
    document.getElementById('dataInicio').value = seteDiasAtras.toISOString().split('T')[0];
    document.getElementById('dataFim').value = hoje.toISOString().split('T')[0];

    // Event listeners para melhor UX
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') fecharModal();
    });

    document.getElementById('orderModal').addEventListener('click', function(e) {
        if (e.target === this) fecharModal();
    });

    // Configurar submit do formulário de filtros
    document.querySelector('.controls').addEventListener('submit', function(e) {
        e.preventDefault();
        carregarPedidos(true);
    });

    // Inicializar dados
    window.pedidosData = [];
    paginaAtual = 0;
    carregandoPagina = false;
    temMaisPedidos = true;
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', inicializarApp);