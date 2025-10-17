// Configuração de marketplaces suportados
const MARKETPLACES = {
    'MERCADOLIVRE': 'Mercado Livre',
    'SHOPEE': 'Shopee',
    'AMAZON': 'Amazon',
    'NUVEMSHOP': 'Nuvem Shop',
    'VTEX': 'VTEX',
    'TRAY': 'Tray',
    'B2W_NEW_API': 'B2W',
    'MAGENTO': 'Magento',
    'WOOCOMMERCE': 'WooCommerce'
};

// Funções utilitárias
function getStatusClass(status) {
    const statusMap = {
        'PENDING': 'status-pending',
        'PAID_WAITING_SHIP': 'status-paid',
        'INVOICED': 'status-invoiced',
        'CONCLUDED': 'status-concluded',
        'CANCELED': 'status-cancelled',
        'PAID': 'status-paid',
        'SHIPPED': 'status-shipped'
    };
    return statusMap[status] || 'status-pending';
}

function getStatusText(status) {
    const statusMap = {
        'PENDING': 'Pendente',
        'PAID_WAITING_SHIP': 'Pago Aguardando Envio',
        'INVOICED': 'Faturado',
        'CONCLUDED': 'Concluído',
        'CANCELED': 'Cancelado',
        'PAID': 'Pago',
        'SHIPPED': 'Enviado'
    };
    return statusMap[status] || status;
}

function formatarData(dataString) {
    if (!dataString) return 'N/A';
    try {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR').substring(0, 5);
    } catch {
        return dataString;
    }
}

function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor || 0);
}

// Funções de manipulação do DOM
function mostrarLoading(mostrar) {
    document.getElementById('loading').classList.toggle('hidden', !mostrar);
}

function mostrarErro(mensagem) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.innerHTML = `<strong>❌ Erro:</strong> ${mensagem}`;
    errorDiv.classList.remove('hidden');
}

function mostrarInfo(mensagem) {
    const infoDiv = document.getElementById('infoMessage');
    infoDiv.innerHTML = mensagem;
    infoDiv.classList.remove('hidden');
}

function limparMensagens() {
    document.getElementById('errorMessage').classList.add('hidden');
    document.getElementById('infoMessage').classList.add('hidden');
}

function mostrarInterfacePedidos() {
    document.getElementById('ordersContainer').classList.remove('hidden');
    document.getElementById('emptyState').classList.add('hidden');
}

function mostrarEstadoVazio() {
    document.getElementById('ordersContainer').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');
}

// Nova função para validar período
function validarPeriodo(dataInicio, dataFim) {
    if (!dataInicio || !dataFim) {
        return { valido: false, erro: 'Ambas as datas devem ser preenchidas' };
    }
    
    const inicio = new Date(dataInicio);
    const fim = new Date(dataFim);
    const hoje = new Date();
    
    if (inicio > fim) {
        return { valido: false, erro: 'Data início não pode ser maior que data fim' };
    }
    
    if (fim > hoje) {
        return { valido: false, erro: 'Data fim não pode ser maior que hoje' };
    }
    
    // Limitar a 30 dias para melhor performance
    const diffTime = Math.abs(fim - inicio);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 30) {
        return { 
            valido: false, 
            erro: 'Período máximo é de 30 dias para melhor performance. Se precisar de um período maior, contate o suporte.' 
        };
    }
    
    return { valido: true };
}