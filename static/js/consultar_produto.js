// static/js/consultar_produto.js
let produtoAtual = null;

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('formBuscarProduto').addEventListener('submit', function(e) {
        e.preventDefault();
        buscarProduto();
    });
});

function buscarProduto() {
    const sku = document.getElementById('sku').value.trim();
    
    if (!sku) {
        mostrarErro('Por favor, digite um SKU ou EAN para buscar');
        return;
    }

    mostrarLoading(true);
    esconderResultados();
    esconderErro();

    fetch('/api/anymarket/produtos/buscar-sku', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sku: sku })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            produtoAtual = data;
            setTimeout(() => exibirProduto(), 100); // Pequeno delay para animação
        } else {
            mostrarErro(data.erro || 'Produto não encontrado');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarErro('Erro ao buscar produto: ' + error.message);
    })
    .finally(() => {
        mostrarLoading(false);
    });
}

function exibirProduto() {
    if (!produtoAtual) return;

    const container = document.getElementById('resultadoProduto');
    const produto = produtoAtual.produto;
    const skuEncontrado = produtoAtual.sku_encontrado;

    container.innerHTML = `
        <div class="card card-produto fade-in">
            <div class="card-header">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4 class="mb-1">
                            <i class="fas fa-box me-2"></i>${produto.title || 'Sem título'}
                        </h4>
                        <p class="mb-0 opacity-75">${produto.description ? produto.description.substring(0, 100) + '...' : 'Sem descrição'}</p>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-light text-dark fs-6">ID: ${produto.id}</span>
                        <div class="mt-2">
                            <span class="badge ${produto.isProductActive ? 'bg-success' : 'bg-danger'}">
                                <i class="fas fa-circle me-1"></i>${produto.isProductActive ? 'Ativo' : 'Inativo'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card-body">
                <!-- Estatísticas Rápidas -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="estatistica-card">
                            <h3>${formatarMoeda(skuEncontrado.price || 0)}</h3>
                            <p><i class="fas fa-tag me-1"></i>Preço</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="estatistica-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                            <h3>${skuEncontrado.amount || 0}</h3>
                            <p><i class="fas fa-warehouse me-1"></i>Estoque</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="estatistica-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                            <h3>${produto.skus ? produto.skus.length : 0}</h3>
                            <p><i class="fas fa-barcode me-1"></i>SKUs</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="estatistica-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                            <h3>${produto.images ? produto.images.length : 0}</h3>
                            <p><i class="fas fa-image me-1"></i>Imagens</p>
                        </div>
                    </div>
                </div>

                <!-- Informações Básicas -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header bg-light">
                                <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Informações do Produto</h5>
                            </div>
                            <div class="card-body">
                                <table class="table table-borderless">
                                    <tr><td><strong>SKU:</strong></td><td><span class="badge bg-primary">${skuEncontrado.partnerId || 'N/A'}</span></td></tr>
                                    <tr><td><strong>EAN:</strong></td><td>${skuEncontrado.ean || 'N/A'}</td></tr>
                                    <tr><td><strong>Categoria:</strong></td><td>${produto.category?.name || 'N/A'}</td></tr>
                                    <tr><td><strong>Marca:</strong></td><td>${produto.brand?.name || 'N/A'}</td></tr>
                                    <tr><td><strong>Modelo:</strong></td><td>${produto.model || 'N/A'}</td></tr>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header bg-light">
                                <h5 class="mb-0"><i class="fas fa-ruler me-2"></i>Dimensões</h5>
                            </div>
                            <div class="card-body">
                                <table class="table table-borderless">
                                    <tr><td><strong>Altura:</strong></td><td>${produto.height || 0} cm</td></tr>
                                    <tr><td><strong>Largura:</strong></td><td>${produto.width || 0} cm</td></tr>
                                    <tr><td><strong>Comprimento:</strong></td><td>${produto.length || 0} cm</td></tr>
                                    <tr><td><strong>Peso:</strong></td><td>${produto.weight || 0} kg</td></tr>
                                    <tr><td><strong>Gênero:</strong></td><td>${formatarGenero(produto.gender)}</td></tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Abas Detalhadas -->
                <ul class="nav nav-tabs" id="produtoTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="skus-tab" data-bs-toggle="tab" data-bs-target="#skus" type="button">
                            <i class="fas fa-barcode me-2"></i>Todos os SKUs (${produto.skus ? produto.skus.length : 0})
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="imagens-tab" data-bs-toggle="tab" data-bs-target="#imagens" type="button">
                            <i class="fas fa-images me-2"></i>Galeria (${produto.images ? produto.images.length : 0})
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="detalhes-tab" data-bs-toggle="tab" data-bs-target="#detalhes" type="button">
                            <i class="fas fa-list-alt me-2"></i>Detalhes Completos
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="json-tab" data-bs-toggle="tab" data-bs-target="#json" type="button">
                            <i class="fas fa-code me-2"></i>JSON
                        </button>
                    </li>
                </ul>

                <div class="tab-content">
                    <!-- Tab SKUs -->
                    <div class="tab-pane fade show active" id="skus" role="tabpanel">
                        <div class="table-responsive mt-3">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>SKU</th>
                                        <th>EAN</th>
                                        <th>Título</th>
                                        <th>Preço</th>
                                        <th>Estoque</th>
                                        <th>Preço Venda</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${produto.skus ? produto.skus.map(sku => `
                                        <tr class="${sku.partnerId === skuEncontrado.partnerId ? 'table-success' : ''}">
                                            <td><strong>${sku.partnerId || 'N/A'}</strong></td>
                                            <td>${sku.ean || 'N/A'}</td>
                                            <td>${sku.title || 'N/A'}</td>
                                            <td class="fw-bold text-success">${formatarMoeda(sku.price || 0)}</td>
                                            <td>
                                                <span class="badge ${sku.amount > 0 ? 'bg-success' : 'bg-danger'}">
                                                    ${sku.amount || 0}
                                                </span>
                                            </td>
                                            <td>${formatarMoeda(sku.sellPrice || 0)}</td>
                                            <td>
                                                <span class="badge bg-secondary">
                                                    ${sku.additionalTime ? sku.additionalTime + ' dias' : 'Imediato'}
                                                </span>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="7" class="text-center py-4">Nenhum SKU encontrado</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Tab Imagens -->
                    <div class="tab-pane fade" id="imagens" role="tabpanel">
                        <div class="galeria-imagens mt-3">
                            ${produto.images ? produto.images.map((imagem, index) => `
                                <div class="card-imagem ${imagem.main ? 'principal' : ''}" onclick="ampliarImagem('${imagem.url || imagem.standardUrl}')">
                                    <img src="${imagem.url || imagem.standardUrl || 'https://via.placeholder.com/200'}" 
                                         class="imagem-produto"
                                         alt="Imagem ${index + 1}"
                                         onerror="this.src='https://via.placeholder.com/200x200/cccccc/969696?text=Imagem+Não+Carregada'">
                                    <div class="card-body text-center p-2">
                                        <small class="text-muted">
                                            ${imagem.main ? '<i class="fas fa-star text-warning me-1"></i><strong>Principal</strong>' : 'Secundária'}
                                        </small>
                                        ${imagem.standardWidth ? `<br><small>${imagem.standardWidth}x${imagem.standardHeight}px</small>` : ''}
                                    </div>
                                </div>
                            `).join('') : '<div class="col-12 text-center py-5"><p class="text-muted">Nenhuma imagem disponível</p></div>'}
                        </div>
                    </div>

                    <!-- Tab Detalhes Completos -->
                    <div class="tab-pane fade" id="detalhes" role="tabpanel">
                        <div class="row mt-3">
                            <div class="col-md-6">
                                <h5><i class="fas fa-tags me-2"></i>Classificações</h5>
                                <div class="card">
                                    <div class="card-body">
                                        <p><strong>Categoria:</strong> ${produto.category?.name || 'N/A'}</p>
                                        <p><strong>Path:</strong> ${produto.category?.path || 'N/A'}</p>
                                        <p><strong>Marca:</strong> ${produto.brand?.name || 'N/A'}</p>
                                        <p><strong>NBM:</strong> ${produto.nbm?.id || 'N/A'} - ${produto.nbm?.description || 'N/A'}</p>
                                        <p><strong>Origem:</strong> ${produto.origin?.description || 'N/A'}</p>
                                    </div>
                                </div>

                                <h5 class="mt-4"><i class="fas fa-shield-alt me-2"></i>Garantia</h5>
                                <div class="card">
                                    <div class="card-body">
                                        <p><strong>Tempo:</strong> ${produto.warrantyTime || 0} meses</p>
                                        <p><strong>Texto:</strong> ${produto.warrantyText || 'Não informado'}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h5><i class="fas fa-cogs me-2"></i>Configurações</h5>
                                <div class="card">
                                    <div class="card-body">
                                        <p><strong>ID Externo:</strong> ${produto.externalIdProduct || 'N/A'}</p>
                                        <p><strong>URL Vídeo:</strong> ${produto.videoUrl ? `<a href="${produto.videoUrl}" target="_blank">Ver vídeo</a>` : 'N/A'}</p>
                                        <p><strong>Fator Preço:</strong> ${produto.priceFactor || 0}</p>
                                        <p><strong>Preço Calculado:</strong> ${produto.calculatedPrice ? 'Sim' : 'Não'}</p>
                                        <p><strong>Tem Variações:</strong> ${produto.hasVariations ? 'Sim' : 'Não'}</p>
                                    </div>
                                </div>

                                ${produto.characteristics && produto.characteristics.length > 0 ? `
                                <h5 class="mt-4"><i class="fas fa-list me-2"></i>Características (${produto.characteristics.length})</h5>
                                <div class="card">
                                    <div class="card-body">
                                        ${produto.characteristics.map(carac => `
                                            <p class="mb-2"><strong>${carac.name || 'N/A'}:</strong> ${carac.value || 'N/A'}</p>
                                        `).join('')}
                                    </div>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>

                    <!-- Tab JSON -->
                    <div class="tab-pane fade" id="json" role="tabpanel">
                        <div class="d-flex justify-content-between align-items-center mt-3 mb-3">
                            <h5>Dados Completos da API</h5>
                            <button class="btn btn-outline-primary btn-sm" onclick="copiarJSON()">
                                <i class="fas fa-copy me-1"></i>Copiar JSON
                            </button>
                        </div>
                        <pre class="bg-dark text-light p-3 rounded" style="max-height: 500px; overflow-y: auto; font-size: 0.8rem;">
                            <code id="jsonCompleto">${JSON.stringify(produtoAtual, null, 2)}</code>
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    `;

    container.style.display = 'block';
    
    // Inicializa as tabs do Bootstrap
    var triggerTabList = [].slice.call(document.querySelectorAll('#produtoTabs button'))
    triggerTabList.forEach(function (triggerEl) {
        var tabTrigger = new bootstrap.Tab(triggerEl)
        triggerEl.addEventListener('click', function (event) {
            event.preventDefault()
            tabTrigger.show()
        })
    });
}

// Novas funções utilitárias
function formatarGenero(genero) {
    const generos = {
        'MALE': 'Masculino',
        'FEMALE': 'Feminino',
        'UNISEX': 'Unissex'
    };
    return generos[genero] || genero || 'N/A';
}

// Mantenha as outras funções (formatarMoeda, mostrarLoading, etc.) iguais
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function mostrarLoading(mostrar) {
    document.getElementById('loadingProduto').style.display = mostrar ? 'block' : 'none';
}

function esconderResultados() {
    document.getElementById('resultadoProduto').style.display = 'none';
}

function esconderErro() {
    document.getElementById('mensagemErro').style.display = 'none';
}

function mostrarErro(mensagem) {
    const erroDiv = document.getElementById('mensagemErro');
    erroDiv.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    erroDiv.style.display = 'block';
}

function ampliarImagem(url) {
    if (url && url !== 'https://via.placeholder.com/200') {
        window.open(url, '_blank');
    }
}

function copiarJSON() {
    const jsonText = document.getElementById('jsonCompleto').textContent;
    navigator.clipboard.writeText(jsonText).then(() => {
        // Toast de sucesso
        const toast = document.createElement('div');
        toast.className = 'alert alert-success alert-dismissible fade show';
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <i class="fas fa-check me-2"></i>JSON copiado para a área de transferência!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    });
}