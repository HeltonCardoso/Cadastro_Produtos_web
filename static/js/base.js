// Controle do Sidebar e Funcionalidades - UM MÓDULO POR VEZ
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Inicializando sidebar...');
    
    // Elementos
    const sidebar = document.querySelector('#sidebarWrapper');
    const sidebarToggler = document.querySelector('#sidebarToggler');
    const toggleSidebarBtn = document.querySelector('#toggleSidebar');
    const mobileToggle = document.querySelector('#mobileToggle');
    const overlay = document.querySelector('.sidebar-overlay');
    const darkModeBtn = document.querySelector('#darkModeToggle');
    const moduleToggles = document.querySelectorAll('.module-toggle');
    const menuGroups = document.querySelectorAll('.menu-group');

    // Botão de logout
    const logoutBtn = document.querySelector('.logout-item, #logoutBtn');
    
    // Estado inicial
    let isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    // ============================================
    // 🎯 DESTACAR LINK ATIVO (APENAS COR, SEM EXPANDIR)
    // ============================================
    
    const currentPath = window.location.pathname;
    console.log(`📍 URL atual: ${currentPath}`);
    
    // Função apenas para destacar o link ativo (sem expandir módulo)
    function highlightActiveLinkOnly() {
        let activeFound = false;
        
        document.querySelectorAll('.sidebar .menu-item').forEach(link => {
            const href = link.getAttribute('href');
            if (!href || href === '#' || href.startsWith('javascript:')) return;
            
            // Remove classe active de todos
            link.classList.remove('active');
            
            // Verifica se é o link atual
            let isActive = false;
            
            if (href.startsWith('/')) {
                // Comparação exata
                if (currentPath === href) {
                    isActive = true;
                }
                // Home especial
                else if (href === '/home' && (currentPath === '/' || currentPath === '/home')) {
                    isActive = true;
                }
                // Para rotas com prefixo (ex: /dashboard/master)
                else if (href !== '/' && currentPath.startsWith(href + '/')) {
                    isActive = true;
                }
                // Para a rota raiz
                else if (href === '/' && currentPath === '/') {
                    isActive = true;
                }
            }
            
            if (isActive) {
                link.classList.add('active');
                activeFound = true;
                console.log(`✅ Link ativo destacado: ${href}`);
            }
        });
        
        return activeFound;
    }
    
    // ============================================
    // FUNÇÕES PARA EXPANSÃO DE MÓDULOS
    // ============================================
    
    // Fecha TODOS os módulos
    function closeAllModules() {
        menuGroups.forEach(group => {
            group.classList.remove('expanded');
            const subitems = group.querySelector('.menu-subitems');
            const toggle = group.querySelector('.module-toggle');
            
            if (subitems) {
                subitems.style.display = 'none';
            }
            if (toggle) {
                toggle.classList.remove('fa-caret-down');
                toggle.classList.add('fa-caret-right');
            }
        });
        console.log('📂 Todos os módulos fechados');
    }
    
    // Expande um módulo específico e fecha os outros
    function expandModuleAndCloseOthers(moduleGroup) {
        if (!moduleGroup) return;
        
        // Fecha todos os módulos primeiro
        closeAllModules();
        
        // Expande apenas o módulo selecionado
        const subitems = moduleGroup.querySelector('.menu-subitems');
        const toggle = moduleGroup.querySelector('.module-toggle');
        
        moduleGroup.classList.add('expanded');
        if (subitems) {
            subitems.style.display = 'block';
        }
        if (toggle) {
            toggle.classList.remove('fa-caret-right');
            toggle.classList.add('fa-caret-down');
        }
        
        const moduleName = moduleGroup.getAttribute('data-module');
        console.log(`📂 Módulo expandido: ${moduleName} (outros fechados)`);
        
        // Salva apenas este módulo no localStorage
        localStorage.setItem('expandedModules', JSON.stringify([moduleName]));
    }
    
    // Restaura estado dos módulos do localStorage (apenas um módulo)
    function restoreModulesFromStorage() {
        if (sidebar.classList.contains('collapsed')) return;
        
        // Carrega módulo salvo
        let savedModules = [];
        try {
            const saved = localStorage.getItem('expandedModules');
            if (saved) {
                savedModules = JSON.parse(saved);
            }
        } catch(e) {}
        
        // Fecha todos primeiro
        closeAllModules();
        
        // Expande apenas o primeiro módulo salvo (se houver)
        if (savedModules.length > 0) {
            const moduleName = savedModules[0];
            const module = document.querySelector(`.menu-group[data-module="${moduleName}"]`);
            if (module) {
                expandModuleAndCloseOthers(module);
            }
        }
    }
    
    // Mostrar todos os subitens quando sidebar recolhido
    function showAllSubitems() {
        if (!sidebar.classList.contains('collapsed')) return;
        
        menuGroups.forEach(group => {
            const subitems = group.querySelector('.menu-subitems');
            if (subitems) {
                subitems.style.display = 'block';
            }
        });
    }

    // ============================================
    // INICIALIZAÇÃO
    // ============================================
    
    function initSidebar() {
        // Aplica estado de colapso
        if (isSidebarCollapsed) {
            sidebar.classList.add('collapsed');
            console.log('📱 Sidebar iniciado como RECOLHIDO');
            showAllSubitems();
        } else {
            sidebar.classList.remove('collapsed');
            console.log('💻 Sidebar iniciado como EXPANDIDO');
            // Restaura módulo expandido (se houver)
            restoreModulesFromStorage();
        }
        
        // Destaca o link ativo (apenas cor, sem expandir)
        highlightActiveLinkOnly();
        
        // Atualiza ícone do toggle
        updateToggleIcon();
        
        // Adiciona tooltips se necessário
        addTooltips();
    }
    
    function updateToggleIcon() {
        const icon = toggleSidebarBtn?.querySelector('i');
        if (icon) {
            if (sidebar.classList.contains('collapsed')) {
                icon.className = 'fas fa-chevron-right';
                toggleSidebarBtn.title = 'Expandir menu';
            } else {
                icon.className = 'fas fa-chevron-left';
                toggleSidebarBtn.title = 'Recolher menu';
            }
        }
    }
    
    function addTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            el.removeAttribute('data-tooltip');
        });
        
        if (sidebar.classList.contains('collapsed') && window.innerWidth > 768) {
            document.querySelectorAll('.menu-item').forEach(item => {
                const textElement = item.querySelector('.menu-text');
                if (textElement && textElement.textContent.trim()) {
                    item.setAttribute('data-tooltip', textElement.textContent.trim());
                }
            });
        }
    }
    
    // ============================================
    // EVENTOS
    // ============================================
    
    // Toggle Sidebar Desktop
    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            isSidebarCollapsed = !sidebar.classList.contains('collapsed');
            
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', isSidebarCollapsed);
            
            if (isSidebarCollapsed) {
                showAllSubitems();
            } else {
                restoreModulesFromStorage();
            }
            
            updateToggleIcon();
            addTooltips();
        });
    }
    
    // Toggle Sidebar Mobile
    if (sidebarToggler) {
        sidebarToggler.addEventListener('click', function() {
            sidebar.classList.toggle('mobile-open');
            if (overlay) overlay.classList.toggle('active');
            document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
            
            if (sidebar.classList.contains('mobile-open')) {
                sidebar.classList.remove('collapsed');
                restoreModulesFromStorage();
                updateToggleIcon();
            }
        });
    }
    
    // Mobile toggle button
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('mobile-open');
            if (overlay) overlay.classList.toggle('active');
            document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
        });
    }
    
    // Fechar sidebar ao clicar no overlay
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Dark Mode Toggle
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', function() {
            const isDark = document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', isDark);
            
            const icon = this.querySelector('i');
            const text = this.querySelector('.menu-text');
            if (isDark) {
                icon.className = 'fas fa-sun';
                if (text) text.textContent = 'MODO CLARO';
            } else {
                icon.className = 'fas fa-moon';
                if (text) text.textContent = 'MODO ESCURO';
            }
        });
    }
    
    // Logout button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Tem certeza que deseja sair?')) {
                window.location.href = '/logout';
            }
        });
    }
    
    // ============================================
    // CLIQUE NOS MÓDULOS (EXPANDIR UM, FECHAR OUTROS)
    // ============================================
    
    moduleToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Só funciona se sidebar estiver expandido
            if (sidebar.classList.contains('collapsed')) {
                console.log('⚠️ Sidebar recolhido, não é possível expandir/recolher módulos');
                return;
            }
            
            const menuGroup = this.closest('.menu-group');
            const moduleName = menuGroup.getAttribute('data-module');
            const isExpanded = menuGroup.classList.contains('expanded');
            
            if (isExpanded) {
                // Se já está expandido, RECOLHE (fecha este módulo)
                closeAllModules();
                // Salva lista vazia (nenhum módulo expandido)
                localStorage.setItem('expandedModules', JSON.stringify([]));
                console.log(`📂 Módulo "${moduleName}" recolhido - nenhum módulo expandido`);
            } else {
                // Expande este módulo e fecha os outros
                expandModuleAndCloseOthers(menuGroup);
            }
        });
    });
    
    // Clique no título do módulo também expande/recolhe
    document.querySelectorAll('.menu-title').forEach(title => {
        title.addEventListener('click', function(e) {
            if (!sidebar.classList.contains('collapsed')) {
                const toggle = this.querySelector('.module-toggle');
                if (toggle) {
                    e.preventDefault();
                    toggle.click();
                }
            }
        });
    });
    
    // ============================================
    // TEMA E RELÓGIO
    // ============================================
    
    function initTheme() {
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            if (darkModeBtn) {
                const icon = darkModeBtn.querySelector('i');
                const text = darkModeBtn.querySelector('.menu-text');
                if (icon) icon.className = 'fas fa-sun';
                if (text) text.textContent = 'MODO CLARO';
            }
        }
    }
    initTheme();
    
    function updateClock() {
        const clockElement = document.getElementById('clock');
        if (clockElement) {
            const now = new Date();
            clockElement.textContent = now.toLocaleTimeString('pt-BR');
        }
    }
    setInterval(updateClock, 1000);
    updateClock();
    
    // ============================================
    // RESPONSIVIDADE
    // ============================================
    
    window.addEventListener('resize', function() {
        if (window.innerWidth > 992) {
            if (sidebar.classList.contains('mobile-open')) {
                sidebar.classList.remove('mobile-open');
                if (overlay) overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    });
    
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 992 && 
            sidebar.classList.contains('mobile-open') && 
            !sidebar.contains(e.target) && 
            sidebarToggler && !sidebarToggler.contains(e.target) &&
            mobileToggle && !mobileToggle.contains(e.target)) {
            sidebar.classList.remove('mobile-open');
            if (overlay) overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
    
    // INICIALIZA
    initSidebar();
    
    console.log('✅ Sidebar inicializada - Um módulo por vez');
});

// Função global para o modal Sobre
window.mostrarSobre = function() {
    alert('Sistema MPOZENATO - Versão 2.0\nDesenvolvido por Helton Cardoso');
};