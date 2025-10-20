// Controle do Sidebar e Funcionalidades
document.addEventListener('DOMContentLoaded', function() {
    // Elementos
    const sidebar = document.querySelector('.sidebar-wrapper');
    const sidebarToggler = document.querySelector('.sidebar-toggler');
    const overlay = document.querySelector('.sidebar-overlay');
    const darkModeBtn = document.getElementById('btn-dark-mode');

    // Toggle Sidebar Mobile
    sidebarToggler.addEventListener('click', function() {
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('mobile-open');
        document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
    });

    // Fechar sidebar ao clicar no overlay
    overlay.addEventListener('click', function() {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('mobile-open');
        document.body.style.overflow = '';
    });

    // Dark Mode Toggle
    darkModeBtn.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Atualizar ícone
        const icon = this.querySelector('i');
        if (newTheme === 'dark') {
            icon.className = 'fas fa-sun';
            this.querySelector('.menu-text').textContent = 'Modo Claro';
        } else {
            icon.className = 'fas fa-moon';
            this.querySelector('.menu-text').textContent = 'Modo Escuro';
        }
    });

    // Carregar tema salvo
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Atualizar ícone do dark mode conforme tema salvo
    if (savedTheme === 'dark') {
        const icon = darkModeBtn.querySelector('i');
        icon.className = 'fas fa-sun';
        darkModeBtn.querySelector('.menu-text').textContent = 'Modo Claro';
    }

    // Relógio
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        const dateString = now.toLocaleDateString('pt-BR');
        document.getElementById('clock').textContent = `${dateString} ${timeString}`;
    }
    
    setInterval(updateClock, 1000);
    updateClock();

    // Fechar sidebar ao redimensionar para desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 1024) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('mobile-open');
            document.body.style.overflow = '';
        }
    });
});