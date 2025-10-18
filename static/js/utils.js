// utils.js - Funções utilitárias compartilhadas

// Função para mostrar toast notifications
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

// Função para mostrar popup de processamento
function showProcessingPopup() {
    const popup = document.getElementById('processingPopup');
    if (popup) {
        popup.style.display = 'flex';
        
        // Iniciar cronômetro
        let seconds = 0;
        const timer = document.getElementById('processingTimer');
        if (timer) {
            const interval = setInterval(() => {
                seconds++;
                const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
                const secs = (seconds % 60).toString().padStart(2, '0');
                timer.textContent = `${mins}:${secs}`;
            }, 1000);
            
            return interval;
        }
    }
    return null;
}

// Função para esconder popup de processamento
function hideProcessingPopup(interval, success = true) {
    if (interval) clearInterval(interval);
    
    const popup = document.getElementById('processingPopup');
    if (popup) {
        popup.style.background = success ? '#28a745' : '#dc3545';
        const popupText = document.getElementById('popupText');
        if (popupText) {
            popupText.textContent = success ? 'Concluído!' : 'Erro!';
        }
        
        setTimeout(() => {
            popup.style.opacity = '0';
            setTimeout(() => {
                popup.style.display = 'none';
                popup.style.opacity = '1';
                popup.style.background = '#0d6efd';
                if (popupText) {
                    popupText.textContent = 'Processando...';
                }
            }, 1000);
        }, 3000);
    }
}

// Função para desabilitar botão durante processamento
function disableButton(button, text = 'Processando...') {
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm"></span> ${text}`;
}

// Função para habilitar botão após processamento
function enableButton(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

// Validação de formulários
function validateFileInput(input, allowedExtensions = []) {
    if (!input.files.length) {
        return { isValid: false, message: 'Selecione um arquivo' };
    }
    
    const file = input.files[0];
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (allowedExtensions.length && !allowedExtensions.includes(extension)) {
        return { 
            isValid: false, 
            message: `Extensão não permitida. Use: ${allowedExtensions.join(', ')}` 
        };
    }
    
    return { isValid: true, file: file };
}

// Formatação de dados
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Manipulação de datas
function formatDate(date, format = 'pt-BR') {
    const d = new Date(date);
    return d.toLocaleDateString(format);
}

function formatDateTime(date, format = 'pt-BR') {
    const d = new Date(date);
    return d.toLocaleString(format);
}