// validar_xml.js - JavaScript para validação de XML

document.addEventListener('DOMContentLoaded', function() {
    initializeXMLForm();
});

function initializeXMLForm() {
    const form = document.getElementById('xmlForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const btn = document.getElementById('btnValidar');
        const container = document.getElementById('resultadoContainer');
        
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Validando...';
        container.innerHTML = '<span class="text-muted">Processando XML...</span>';

        try {
            const formData = new FormData(this);
            const response = await fetch('/validar-xml', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.erro || 'Erro no processamento');

            if (data.sucesso) {
                displayXMLResult(data.dados, container);
            } else {
                container.innerHTML = `<div class="alert alert-danger">Erro: ${data.erro}</div>`;
            }

        } catch (error) {
            container.innerHTML = `<div class="alert alert-danger">Erro: ${error.message}</div>`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'VALIDAR XML';
        }
    });
}

function displayXMLResult(d, container) {
    container.innerHTML = `
        <h6 class="mt-2">📄 Dados da Nota</h6>
        <ul>
            <li><b>Chave:</b> ${d.chave || 'N/A'}</li>
            <li><b>Modelo:</b> ${d.modelo || 'N/A'}</li>
            <li><b>Número:</b> ${d.numero || 'N/A'} - <b>Série:</b> ${d.serie || 'N/A'}</li>
            <li><b>Ambiente:</b> ${d.ambiente || 'N/A'}</li>
            <li><b>Status:</b> ${d.autorizada ? '<span class="text-success">Autorizada ✅</span>' : '<span class="text-danger">Não autorizada ❌</span>'}</li>
            <li><b>QRCode:</b> ${d.qrcode || 'N/A'}</li>
        </ul>

        <h6 class="mt-3">🏢 Emitente</h6>
        <ul>
            <li><b>Nome:</b> ${d.emitente?.nome || 'N/A'}</li>
            <li><b>CNPJ/CPF:</b> ${d.emitente?.cnpj || d.emitente?.cpf || 'N/A'}</li>
        </ul>

        <h6 class="mt-3">🙍‍♂️ Destinatário</h6>
        <ul>
            <li><b>Nome:</b> ${d.destinatario?.nome || 'N/A'}</li>
            <li><b>CNPJ/CPF:</b> ${d.destinatario?.cnpj || d.destinatario?.cpf || 'N/A'}</li>
            <li><b>Endereço:</b> 
                ${d.destinatario?.endereco?.logradouro || ''}, 
                ${d.destinatario?.endereco?.numero || ''} - 
                ${d.destinatario?.endereco?.bairro || ''}, 
                ${d.destinatario?.endereco?.municipio || ''}/${d.destinatario?.endereco?.uf || ''} 
                CEP: ${d.destinatario?.endereco?.cep || ''}
            </li>
        </ul>
    `;
}