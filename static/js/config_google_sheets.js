// config_google_sheets.js - JavaScript para configuração do Google Sheets

document.addEventListener('DOMContentLoaded', function() {
    initializeSheetIdListener();
});

function initializeSheetIdListener() {
    const sheetIdInput = document.getElementById('sheet_id');
    if (!sheetIdInput) return;

    sheetIdInput.addEventListener('change', function() {
        const sheetId = this.value;
        if (sheetId) {
            fetchAbas(sheetId);
        }
    });
}

function fetchAbas(sheetId) {
    fetch(`/api/abas-google-sheets?sheet_id=${encodeURIComponent(sheetId)}`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('aba_nome');
            if (!select) return;
            
            select.innerHTML = '<option value="">Selecione uma aba</option>';
            
            if (data.abas) {
                data.abas.forEach(aba => {
                    const option = document.createElement('option');
                    option.value = aba.title;
                    option.textContent = `${aba.title} (${aba.row_count}x${aba.col_count})`;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Erro:', error));
}