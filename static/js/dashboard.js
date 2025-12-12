// static/js/dashboard.js
class DashboardManager {
    constructor() {
        this.refreshInterval = 60000; // 1 minuto
        this.init();
    }

    init() {
        // Atualiza métricas ao carregar
        this.updateMetrics();
        
        // Configura atualização automática
        setInterval(() => this.updateMetrics(), this.refreshInterval);
        
        // Adiciona listeners para widgets
        this.addWidgetInteractions();
    }

    async updateMetrics() {
        try {
            const response = await fetch('/api/dashboard/metricas-gerais');
            const data = await response.json();
            
            if (data.sucesso) {
                this.updateUI(data);
                this.showNotification('Dashboard atualizado', 'success');
            }
        } catch (error) {
            console.error('Erro ao atualizar métricas:', error);
        }
    }

    updateUI(data) {
        // Atualiza contadores do sistema
        this.updateCounter('processamentos-hoje', data.sistema.processamentos_hoje);
        this.updateCounter('sucessos-hoje', data.sistema.sucessos_hoje);
        this.updateCounter('erros-hoje', data.sistema.erros_hoje);
        
        // Atualiza status do Mercado Livre
        this.updateMLStatus(data.mercadolivre);
        
        // Atualiza status do AnyMarket
        this.updateAnyMarketStatus(data.anymarket);
        
        // Atualiza timestamp
        this.updateTimestamp();
    }

    updateCounter(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            this.animateCounter(element, value);
        }
    }

    animateCounter(element, target) {
        const current = parseInt(element.textContent) || 0;
        const increment = target > current ? 1 : -1;
        let currentValue = current;

        const animate = () => {
            if ((increment > 0 && currentValue >= target) || 
                (increment < 0 && currentValue <= target)) {
                element.textContent = target;
                return;
            }

            currentValue += increment;
            element.textContent = currentValue;
            
            requestAnimationFrame(animate);
        };

        requestAnimationFrame(animate);
    }

    updateMLStatus(mlData) {
        const mlWidget = document.querySelector('.mercadolivre-widget');
        if (!mlWidget) return;

        if (mlData.autenticado && mlData.metricas) {
            mlWidget.classList.remove('offline');
            mlWidget.classList.add('online');
            
            // Atualiza métricas específicas
            this.updateMetric(mlWidget, 'total-anuncios', mlData.metricas.anuncios_ativos);
            this.updateMetric(mlWidget, 'vendas-30d', mlData.metricas.total_vendas_30_dias);
            this.updateMetric(mlWidget, 'ticket-medio', 
                mlData.metricas.ticket_medio ? 
                `R$ ${mlData.metricas.ticket_medio.toFixed(2)}` : 'R$ 0,00');
        } else {
            mlWidget.classList.remove('online');
            mlWidget.classList.add('offline');
        }
    }

    updateAnyMarketStatus(anymarketData) {
        const anymarketWidget = document.querySelector('.anymarket-widget');
        if (!anymarketWidget) return;

        if (anymarketData.token_configurado) {
            anymarketWidget.classList.remove('offline');
            anymarketWidget.classList.add('online');
        } else {
            anymarketWidget.classList.remove('online');
            anymarketWidget.classList.add('offline');
        }
    }

    updateTimestamp() {
        const now = new Date();
        const timeElement = document.getElementById('last-update-time');
        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString('pt-BR');
        }
    }

    addWidgetInteractions() {
        // Adiciona tooltips
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => {
            new bootstrap.Tooltip(el);
        });

        // Adiciona click handlers para widgets
        document.querySelectorAll('.dashboard-widget').forEach(widget => {
            widget.addEventListener('click', (e) => {
                if (!e.target.closest('a, button')) {
                    widget.classList.add('clicked');
                    setTimeout(() => widget.classList.remove('clicked'), 300);
                }
            });
        });
    }

    showNotification(message, type = 'info') {
        // Implemente notificações toast se desejar
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Inicializa quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});