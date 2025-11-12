// Funções de configuração
function verificarConfiguracao() {
    fetch('/api/mercadolivre/configuracao')
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                const statusElement = document.getElementById('statusConfiguracao');
                if (data.configurado) {
                    statusElement.innerHTML = '<span class="text-success">Configurado</span>';
                } else {
                    statusElement.innerHTML = '<span class="text-warning">Não configurado</span>';
                }
            }
        })
        .catch(error => {
            console.error('Erro ao verificar configuração:', error);
        });
}

function salvarConfiguracao(clientId, clientSecret) {
    fetch('/api/mercadolivre/configurar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            client_id: clientId,
            client_secret: clientSecret
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfiguracao'));
            modal.hide();
            
            // Limpar campos
            document.getElementById('clientId').value = '';
            document.getElementById('clientSecret').value = '';
            
            mostrarMensagem('Configuração salva com sucesso!', 'success');
            verificarConfiguracao();
        } else {
            mostrarMensagem('Erro na configuração: ' + data.erro, 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro ao salvar configuração: ' + error.message, 'danger');
    });
}

// Adicione estes event listeners:
document.addEventListener('DOMContentLoaded', function() {
    // ... outros event listeners ...
    
    // Configuração
    document.getElementById('btnSalvarConfiguracao').addEventListener('click', function() {
        const clientId = document.getElementById('clientId').value.trim();
        const clientSecret = document.getElementById('clientSecret').value.trim();
        
        if (!clientId || !clientSecret) {
            mostrarMensagem('Preencha ambos os campos', 'warning');
            return;
        }
        
        salvarConfiguracao(clientId, clientSecret);
    });
    
    // Verificar configuração ao carregar a página
    verificarConfiguracao();
    verificarStatusAutenticacao();
});