// Controle do Sidebar e Funcionalidades
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Inicializando sidebar...');
    
    // Elementos
    const sidebar = document.querySelector('#sidebarWrapper');
    const sidebarToggler = document.querySelector('#sidebarToggler');
    const toggleSidebarBtn = document.querySelector('#toggleSidebar');
    const mobileToggle = document.querySelector('#mobileToggle');
    const overlay = document.querySelector('.sidebar-overlay');
    const darkModeBtn = document.querySelector('#darkModeToggle');
    const logoutBtn = document.querySelector('#logoutBtn');
    const moduleToggles = document.querySelectorAll('.module-toggle');
    const menuGroups = document.querySelectorAll('.menu-group');

    // Estado inicial
    let isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    let expandedModules = JSON.parse(localStorage.getItem('expandedModules') || '["configuracoes"]');

    // Inicializar estado do sidebar
    function initSidebarState() {
        console.log('📊 Estado inicial:', { isSidebarCollapsed, expandedModules });
        
        if (isSidebarCollapsed) {
            sidebar.classList.add('collapsed');
            console.log('📱 Sidebar iniciado como RECOLHIDO → (seta para direita)');
            // Quando recolhido, força mostrar todos os subitens
            showAllSubitems();
        } else {
            sidebar.classList.remove('collapsed');
            console.log('💻 Sidebar iniciado como EXPANDIDO ← (seta para esquerda)');
            // Quando expandido, restaura estado dos módulos
            restoreModulesState();
        }
        updateToggleIcon();
        addTooltips();
        forceIconsVisibility();
    }

    // Função para mostrar todos os subitens quando sidebar recolhido
    function showAllSubitems() {
        if (!sidebar.classList.contains('collapsed')) return;
        
        console.log('📂 Mostrando todos os subitens (sidebar recolhido)');
        menuGroups.forEach(group => {
            const subitems = group.querySelector('.menu-subitems');
            if (subitems) {
                subitems.style.display = 'block';
                subitems.style.opacity = '1';
                subitems.style.visibility = 'visible';
                subitems.style.height = 'auto';
            }
            
            // Também mostra todos os itens
            const menuItems = group.querySelectorAll('.menu-item');
            menuItems.forEach(item => {
                item.style.display = 'flex';
                item.style.opacity = '1';
                item.style.visibility = 'visible';
                item.style.height = 'auto';
            });
        });
    }

    // Função para restaurar estado dos módulos quando sidebar expandido
    function restoreModulesState() {
        if (sidebar.classList.contains('collapsed')) return;
        
        console.log('📂 Restaurando estado dos módulos (sidebar expandido)');
        
        // Primeiro fecha todos
        menuGroups.forEach(group => {
            const moduleName = group.dataset.module;
            const subitems = group.querySelector('.menu-subitems');
            const toggle = group.querySelector('.module-toggle');
            
            if (subitems) {
                subitems.style.display = 'none';
                subitems.style.opacity = '0';
            }
            if (toggle) {
                toggle.style.transform = 'rotate(-90deg)';
                toggle.style.opacity = '0.5';
            }
            group.classList.remove('expanded');
        });
        
        // Depois expande apenas os salvos
        expandedModules.forEach(moduleName => {
            const module = document.querySelector(`[data-module="${moduleName}"]`);
            if (module) {
                module.classList.add('expanded');
                const subitems = module.querySelector('.menu-subitems');
                const toggle = module.querySelector('.module-toggle');
                if (subitems) {
                    subitems.style.display = 'block';
                    subitems.style.opacity = '1';
                    subitems.style.animation = 'none';
                    setTimeout(() => {
                        subitems.style.animation = '';
                    }, 10);
                }
                if (toggle) {
                    toggle.style.transform = 'rotate(0deg)';
                    toggle.style.opacity = '1';
                }
                console.log(`📂 Módulo "${moduleName}" expandido`);
            }
        });
    }

    // Garantir que ícones sejam visíveis
    function forceIconsVisibility() {
        const menuIcons = document.querySelectorAll('.menu-icon');
        menuIcons.forEach(icon => {
            icon.style.display = 'flex';
            icon.style.visibility = 'visible';
            icon.style.opacity = '1';
        });
    }

    // Inicializar
    initSidebarState();

    // Toggle Sidebar Desktop (colapsar/expandir)
    toggleSidebarBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        isSidebarCollapsed = !isSidebarCollapsed;
        console.log(`🔄 Toggle sidebar: ${isSidebarCollapsed ? 'RECOLHENDO' : 'EXPANDINDO'}`);
        
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', isSidebarCollapsed);
        
        // Se estiver recolhendo, mostra todos os subitens
        if (isSidebarCollapsed) {
            showAllSubitems();
        } else {
            // Se estiver expandindo, restaura estado dos módulos
            restoreModulesState();
        }
        
        updateToggleIcon();
        addTooltips();
        forceIconsVisibility();
    });

    // Toggle Sidebar Mobile
    sidebarToggler.addEventListener('click', function() {
        console.log('📱 Toggle mobile clicado');
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('mobile-open');
        document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
        
        // Em mobile, se abrir o menu, força expandir sidebar
        if (sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('collapsed');
            restoreModulesState();
            updateToggleIcon();
            addTooltips();
        }
    });

    // Mobile toggle
    mobileToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        console.log('📱 Mobile toggle clicado');
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('mobile-open');
        document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
    });

    // Fechar sidebar ao clicar no overlay
    overlay.addEventListener('click', function() {
        console.log('❌ Overlay clicado, fechando sidebar');
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('mobile-open');
        document.body.style.overflow = '';
    });

    // Dark Mode Toggle
    darkModeBtn.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        console.log(`🌙 Alternando tema: ${currentTheme} -> ${newTheme}`);
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Atualizar ícone
        const icon = this.querySelector('i');
        const text = this.querySelector('.menu-text');
        if (newTheme === 'dark') {
            icon.className = 'fas fa-sun';
            text.textContent = 'Modo Claro';
        } else {
            icon.className = 'fas fa-moon';
            text.textContent = 'Modo Escuro';
        }
    });

    // Logout button
    logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (confirm('Tem certeza que deseja sair?')) {
            console.log('🚪 Usuário solicitou logout');
            // Implementar logout aqui
            // window.location.href = '/logout';
        }
    });

    // Module toggle functionality - APENAS quando sidebar expandido
    moduleToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Só funciona se sidebar estiver expandido
            if (sidebar.classList.contains('collapsed')) {
                console.log('⚠️ Sidebar recolhido, não é possível expandir/recolher módulos');
                return;
            }
            
            const menuGroup = this.closest('.menu-group');
            const moduleName = menuGroup.dataset.module;
            const subitems = menuGroup.querySelector('.menu-subitems');
            
            console.log(`📂 Toggle módulo: ${moduleName} (sidebar expandido)`);
            
            if (menuGroup.classList.contains('expanded')) {
                // Collapse
                menuGroup.classList.remove('expanded');
                if (subitems) {
                    subitems.style.display = 'none';
                    subitems.style.opacity = '0';
                }
                this.style.transform = 'rotate(-90deg)';
                this.style.opacity = '0.5';
                
                // Remove do localStorage
                expandedModules = expandedModules.filter(m => m !== moduleName);
                console.log(`📂 Módulo "${moduleName}" recolhido`);
            } else {
                // Fecha todos os outros módulos primeiro
                menuGroups.forEach(group => {
                    const otherModuleName = group.dataset.module;
                    if (otherModuleName !== moduleName) {
                        group.classList.remove('expanded');
                        const otherSubitems = group.querySelector('.menu-subitems');
                        const otherToggle = group.querySelector('.module-toggle');
                        if (otherSubitems) {
                            otherSubitems.style.display = 'none';
                            otherSubitems.style.opacity = '0';
                        }
                        if (otherToggle) {
                            otherToggle.style.transform = 'rotate(-90deg)';
                            otherToggle.style.opacity = '0.5';
                        }
                        
                        // Remove do array de módulos expandidos
                        expandedModules = expandedModules.filter(m => m !== otherModuleName);
                    }
                });
                
                // Expand este módulo
                menuGroup.classList.add('expanded');
                if (subitems) {
                    subitems.style.display = 'block';
                    subitems.style.opacity = '1';
                }
                this.style.transform = 'rotate(0deg)';
                this.style.opacity = '1';
                
                // Adicionar ao localStorage (será o único)
                expandedModules = [moduleName];
                console.log(`📂 Módulo "${moduleName}" expandido (únicos)`);
            }
            
            localStorage.setItem('expandedModules', JSON.stringify(expandedModules));
        });
    });

    // Toggle modules on title click (apenas quando expandido)
    document.querySelectorAll('.menu-title').forEach(title => {
        title.addEventListener('click', function(e) {
            // Só permite toggle se não estiver em modo colapsado
            if (!sidebar.classList.contains('collapsed')) {
                const toggle = this.querySelector('.module-toggle');
                if (toggle) {
                    console.log('📂 Clicou no título do módulo');
                    toggle.click();
                }
            }
        });
    });

    // Carregar tema salvo
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        console.log(`🎨 Carregando tema: ${savedTheme}`);
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Atualizar ícone do dark mode conforme tema salvo
        if (darkModeBtn) {
            const icon = darkModeBtn.querySelector('i');
            const text = darkModeBtn.querySelector('.menu-text');
            if (savedTheme === 'dark') {
                icon.className = 'fas fa-sun';
                text.textContent = 'Modo Claro';
            } else {
                icon.className = 'fas fa-moon';
                text.textContent = 'Modo Escuro';
            }
        }
    }

    initTheme();

    // Relógio
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        const dateString = now.toLocaleDateString('pt-BR');
        const clockElement = document.getElementById('clock');
        if (clockElement) {
            clockElement.textContent = `${dateString} ${timeString}`;
        }
    }
    
    setInterval(updateClock, 1000);
    updateClock();

    // Fechar sidebar ao redimensionar para desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 1024) {
            if (sidebar.classList.contains('mobile-open')) {
                console.log('📱 Redimensionou para desktop, fechando menu mobile');
                sidebar.classList.remove('mobile-open');
                overlay.classList.remove('mobile-open');
                document.body.style.overflow = '';
                
                // Restaura estado do sidebar
                if (isSidebarCollapsed) {
                    sidebar.classList.add('collapsed');
                    showAllSubitems();
                } else {
                    sidebar.classList.remove('collapsed');
                    restoreModulesState();
                }
                updateToggleIcon();
                addTooltips();
                forceIconsVisibility();
            }
        }
    });

    // Helper functions
    function updateToggleIcon() {
        const icon = toggleSidebarBtn.querySelector('i');
        if (icon) {
            if (isSidebarCollapsed) {
                // Sidebar RECOLHIDO: seta para DIREITA →
                icon.className = 'fas fa-chevron-right';
                toggleSidebarBtn.title = 'Expandir menu';
                toggleSidebarBtn.style.fontSize = '1.4rem';
                console.log('➡️ Seta definida para DIREITA (sidebar recolhido)');
            } else {
                // Sidebar EXPANDIDO: seta para ESQUERDA ←
                icon.className = 'fas fa-chevron-left';
                toggleSidebarBtn.title = 'Recolher menu';
                toggleSidebarBtn.style.fontSize = '1.2rem';
                console.log('⬅️ Seta definida para ESQUERDA (sidebar expandido)');
            }
        }
    }

    function addTooltips() {
        // Remove tooltips antigos
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            el.removeAttribute('data-tooltip');
        });

        // Adiciona tooltips se sidebar estiver colapsado E não estiver em mobile
        if (sidebar.classList.contains('collapsed') && window.innerWidth > 1024) {
            console.log('🛠️ Adicionando tooltips para sidebar colapsado');
            
            // Tooltips para itens de menu
            document.querySelectorAll('.menu-item').forEach(item => {
                const textElement = item.querySelector('.menu-text');
                if (textElement) {
                    const text = textElement.textContent;
                    item.setAttribute('data-tooltip', text);
                }
            });
            
            // Tooltips para títulos de módulos
            document.querySelectorAll('.menu-title').forEach(title => {
                const textElement = title.querySelector('.menu-title-text');
                if (textElement) {
                    const text = textElement.textContent;
                    title.setAttribute('data-tooltip', text);
                }
            });
            
            // Tooltip para logo
            const logoContainer = document.querySelector('.logo-container');
            if (logoContainer) {
                logoContainer.setAttribute('data-tooltip', 'MPOZENATO Sistema');
            }
            
            // Tooltip para botão de toggle
            toggleSidebarBtn.setAttribute('data-tooltip', isSidebarCollapsed ? 'Expandir menu' : 'Recolher menu');
        }
    }

    // Fechar sidebar ao clicar fora (apenas mobile)
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 1024 && 
            sidebar.classList.contains('mobile-open') && 
            !sidebar.contains(e.target) && 
            !sidebarToggler.contains(e.target)) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('mobile-open');
            document.body.style.overflow = '';
        }
    });

    console.log('✅ Sidebar inicializado com sucesso');
});