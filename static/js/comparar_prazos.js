// comparar_prazos.js

document.addEventListener('DOMContentLoaded', function() {
    initializeFormSubmission();
    initializeFileDropAreas();
});

function initializeFormSubmission() {
    const form = document.getElementById('compararForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const btn = document.getElementById('btnProcessar');
        const popup = document.getElementById('processingPopup');
        const timer = document.getElementById('processingTimer');
        const popupText = document.getElementById('popupText');
        const logContainer = document.getElementById('logContainer');
        const downloadContainer = document.getElementById('downloadContainer');
        
        // Resetar estado
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';
        popup.style.display = 'flex';
        popupText.textContent = 'Processando...';
        timer.textContent = '00:00';
        downloadContainer.innerHTML = '';
        logContainer.innerHTML = '<span class="text-muted">Processando arquivos...</span>';

        // Cronômetro
        let seconds = 0;
        const interval = setInterval(() => {
            seconds++;
            const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
            const secs = (seconds % 60).toString().padStart(2, '0');
            timer.textContent = `${mins}:${secs}`;
        }, 1000);

        try {
            const formData = new FormData(this);
            const response = await fetch('/comparar-prazos', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) throw new Error(data.erro || 'Erro no processamento');

            // Atualizar interface
            if (data.sucesso) {
                downloadContainer.innerHTML = `
                    <a href="/uploads/${data.arquivo}" 
                       class="btn btn-success">
                       <i class="fas fa-download"></i> BAIXAR RESULTADO
                    </a>
                `;

                logContainer.innerHTML = `
                    <div class="d-flex align-items-center mb-3">
                        <img src="${data.marketplace.imagem}" width="120" class="me-3">
                        <h4 class="m-0">${data.marketplace.nome}</h4>
                    </div>
                    ${data.log || ''}
                `;
            }

            // Feedback visual de conclusão
            clearInterval(interval);
            popup.style.background = '#28a745';
            popupText.textContent = 'Concluído!';
            
            // Fade out após 3 segundos
            setTimeout(() => {
                popup.style.opacity = '0';
                setTimeout(() => {
                    popup.style.display = 'none';
                    btn.disabled = false;
                    btn.innerHTML = 'COMPARAR PRAZOS';
                }, 1000);
            }, 3000);

        } catch (error) {
            clearInterval(interval);
            popup.style.background = '#dc3545';
            popupText.textContent = 'Erro!';
            
            logContainer.innerHTML = `
                <div class="alert alert-danger">
                    Erro: ${error.message}
                </div>
            `;

            setTimeout(() => {
                popup.style.opacity = '0';
                setTimeout(() => {
                    popup.style.display = 'none';
                    btn.disabled = false;
                    btn.innerHTML = 'COMPARAR PRAZOS';
                }, 1000);
            }, 5000);
        }
    });
}

function initializeFileDropAreas() {
    document.querySelectorAll('.file-drop-area').forEach(dropArea => {
        const input = dropArea.querySelector('.file-input');
        const msg = dropArea.querySelector('.file-msg');
        const info = dropArea.querySelector('.file-info');
        
        input.addEventListener('change', function() {
            if (this.files.length) {
                info.textContent = this.files[0].name;
                dropArea.classList.add('active');
            }
        });

        ['dragenter', 'dragover'].forEach(event => {
            dropArea.addEventListener(event, () => dropArea.classList.add('highlight'));
        });

        ['dragleave', 'drop'].forEach(event => {
            dropArea.addEventListener(event, () => dropArea.classList.remove('highlight'));
        });

        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            input.files = e.dataTransfer.files;
            input.dispatchEvent(new Event('change'));
        });
    });
}