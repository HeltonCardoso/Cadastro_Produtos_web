// Base.js - JavaScript principal da aplicação

document.addEventListener('DOMContentLoaded', function() {
    initializeDarkMode();
    initializeMenu();
    initializeAutoCloseAlerts();
    initializeClock();
});

// Modo Escuro
function initializeDarkMode() {
    const btnDarkMode = document.getElementById('btn-dark-mode');
    const icon = btnDarkMode?.querySelector('i');
    
    if (!btnDarkMode || !icon) return;

    // Verifica preferência salva
    if (localStorage.getItem('darkMode') === 'enabled') {
        enableDarkMode();
    }

    btnDarkMode.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });

    function enableDarkMode() {
        document.body.classList.add('dark-mode');
        icon.classList.replace('fa-moon', 'fa-sun');
        localStorage.setItem('darkMode', 'enabled');
    }

    function disableDarkMode() {
        document.body.classList.remove('dark-mode');
        icon.classList.replace('fa-sun', 'fa-moon');
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Menu Navigation
function initializeMenu() {
    // Toggle de clique
    document.querySelectorAll('.menu-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('open');
            const submenu = btn.nextElementSibling;
            if (submenu && submenu.classList.contains('submenu')) {
                submenu.classList.toggle('show');
            }
        });
    });

    // Abre módulo ativo automaticamente
    const openModule = document.querySelector('.menu-toggle.open');
    if (openModule) {
        const submenu = openModule.nextElementSibling;
        if (submenu && submenu.classList.contains('submenu')) {
            submenu.classList.add('show');
        }
    }
}

// Auto-close alerts
function initializeAutoCloseAlerts() {
    setTimeout(() => {
        const alertas = document.querySelectorAll('.alert');
        alertas.forEach(alerta => {
            alerta.classList.remove('show');
            alerta.classList.add('fade');
            setTimeout(() => alerta.remove(), 500);
        });
    }, 90000);
}

// Clock
function initializeClock() {
    function updateClock() {
        const now = new Date();
        const time = now.toLocaleTimeString('pt-BR');
        const date = now.toLocaleDateString('pt-BR');
        const clockElement = document.getElementById('clock');
        if (clockElement) {
            clockElement.innerHTML = `${date} ${time}`;
        }
    }
    setInterval(updateClock, 1000);
    updateClock();
}

// Utils
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