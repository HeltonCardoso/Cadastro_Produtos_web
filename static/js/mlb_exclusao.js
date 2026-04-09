let mlbAtual = null;
let mlbsParaExcluir = [];
let emProcessamento = false;
let tempoInicioProcessamento = null;
let tempoRestanteIntervalo = null;

// =========================================
// BARRA DE PROGRESSO (NOVAS FUNÇÕES)
// =========================================

// =========================================
// FUNÇÃO DE INÍCIO DO PROGRESSO (COM TEMPO)
// =========================================

function inicializarEventosExclusao() {
    console.log('🔄 Inicializando eventos de exclusão...');
    
    // Configurar evento para o input de arquivo
    const arquivoExclusao = document.getElementById('arquivoExclusao');
    if (arquivoExclusao) {
        // Remove eventos antigos para evitar duplicação
        const novoArquivo = arquivoExclusao.cloneNode(true);
        arquivoExclusao.parentNode.replaceChild(novoArquivo, arquivoExclusao);
        
        novoArquivo.addEventListener('change', function(e) {
            console.log('📁 Arquivo selecionado');
            processarPlanilhaExclusao(this);
        });
        console.log('✅ Input de arquivo configurado');
    } else {
        console.log('⚠️ Input arquivoExclusao não encontrado');
    }
    
    // Configurar botão de iniciar exclusão
    const btnIniciar = document.getElementById('btnIniciarExclusao');
    if (btnIniciar) {
        // Remove eventos antigos
        const novoBtn = btnIniciar.cloneNode(true);
        btnIniciar.parentNode.replaceChild(novoBtn, btnIniciar);
        
        novoBtn.onclick = function() {
            console.log('🔘 Botão Iniciar Exclusão clicado');
            iniciarExclusaoEmMassa();
        };
        console.log('✅ Botão iniciar exclusão configurado');
    } else {
        console.log('⚠️ Botão btnIniciarExclusao não encontrado');
    }
    
    // Configurar fechamento do modal
    const modalExclusao = document.getElementById('modalExclusaoPlanilha');
    if (modalExclusao) {
        modalExclusao.onclick = function(event) {
            if (event.target === modalExclusao) {
                fecharModalExclusaoPlanilha();
            }
        };
        console.log('✅ Evento de fechar modal configurado');
    }
}

// =========================================
// INICIALIZAÇÃO (ATUALIZADA)
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Sistema de exclusão carregado (com barra de progresso)');
    
    // 🔧 CHAMA A FUNÇÃO DE INICIALIZAÇÃO DOS EVENTOS
    inicializarEventosExclusao();
    
    // Adicionar botões de exclusão nas linhas
    setTimeout(adicionarBotoesExclusao, 1000);
    
    // Observar mudanças na tabela
    const tabela = document.getElementById('ordersTableBody');
    if (tabela) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    setTimeout(adicionarBotoesExclusao, 100);
                }
            });
        });
        
        observer.observe(tabela, { childList: true, subtree: true });
        console.log('✅ Observer configurado para tabela');
    }
    
    // Fechar modal ao clicar fora
    const modalExclusao = document.getElementById('modalExclusaoPlanilha');
    if (modalExclusao) {
        modalExclusao.onclick = function(event) {
            if (event.target === modalExclusao) {
                fecharModalExclusaoPlanilha();
            }
        };
        console.log('✅ Evento de fechar modal configurado');
    }
    
    console.log('✅ Sistema de exclusão totalmente inicializado');
});

function iniciarProgresso(totalMLBs) {
    console.log(`Iniciando progresso para ${totalMLBs} MLBs`);
    
    // Marca o tempo de início
    tempoInicioProcessamento = new Date();
    
    // Inicia o intervalo para atualizar o tempo restante
    if (tempoRestanteIntervalo) {
        clearInterval(tempoRestanteIntervalo);
    }
    
    // Mostra container de progresso
    const container = document.getElementById('progressoContainer');
    if (container) {
        container.style.display = 'block';
    }
    
    // Esconde resumo anterior
    const resumo = document.getElementById('resumoExclusao');
    if (resumo) {
        resumo.style.display = 'none';
    }
    
    // Esconde preview
    const preview = document.getElementById('previewExclusao');
    if (preview) {
        preview.style.display = 'none';
    }
    
    // Reseta a barra
    atualizarProgresso(0, totalMLBs, 'Preparando exclusão...', '');
    
    // Desabilita botões durante processamento
    const btnIniciar = document.getElementById('btnIniciarExclusao');
    const arquivoInput = document.getElementById('arquivoExclusao');
    
    if (btnIniciar) {
        btnIniciar.disabled = true;
        btnIniciar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
    }
    
    if (arquivoInput) {
        arquivoInput.disabled = true;
    }
    
    emProcessamento = true;
}

function atualizarProgresso(processados, total, status, mlbAtual = '') {
    const porcentagem = total > 0 ? Math.round((processados / total) * 100) : 0;
    
    console.log(`Progresso: ${processados}/${total} (${porcentagem}%) - ${status}`);
    
    // Atualiza barra
    const progressoBar = document.getElementById('progressoBar');
    const progressoTexto = document.getElementById('progressoTexto');
    const progressoStatus = document.getElementById('progressoStatus');
    const progressoContador = document.getElementById('progressoContador');
    const mlbProcessandoAtual = document.getElementById('mlbProcessandoAtual');
    const mlbAtualNome = document.getElementById('mlbAtualNome');
    
    if (progressoBar) {
        progressoBar.style.width = `${porcentagem}%`;
    }
    
    if (progressoTexto) {
        progressoTexto.textContent = `${porcentagem}%`;
    }
    
    if (progressoStatus) {
        progressoStatus.textContent = status;
    }
    
    if (progressoContador) {
        progressoContador.textContent = `${processados}/${total} processados`;
    }
    
    // Mostra MLB atual sendo processado
    if (mlbAtual && processados < total) {
        if (mlbProcessandoAtual) mlbProcessandoAtual.style.display = 'block';
        if (mlbAtualNome) mlbAtualNome.textContent = mlbAtual;
    } else if (processados === total) {
        if (mlbProcessandoAtual) mlbProcessandoAtual.style.display = 'none';
    }
    
    // Calcula e atualiza tempo restante
    if (tempoInicioProcessamento && processados > 0 && processados < total) {
        const tempoDecorrido = (new Date() - tempoInicioProcessamento) / 1000; // em segundos
        const mediaPorItem = tempoDecorrido / processados;
        const tempoRestanteSegundos = mediaPorItem * (total - processados);
        
        const minutosRestantes = Math.floor(tempoRestanteSegundos / 60);
        const segundosRestantes = Math.floor(tempoRestanteSegundos % 60);
        
        const tempoRestanteElemento = document.getElementById('tempoRestante');
        if (tempoRestanteElemento) {
            if (minutosRestantes > 0) {
                tempoRestanteElemento.textContent = `${minutosRestantes} min ${segundosRestantes} s`;
            } else {
                tempoRestanteElemento.textContent = `${segundosRestantes} segundos`;
            }
        }
    } else if (processados === total) {
        const tempoRestanteElemento = document.getElementById('tempoRestante');
        if (tempoRestanteElemento) {
            tempoRestanteElemento.textContent = '00:00';
        }
    }
}

function baixarRelatorioExclusao(sucessos, erros, detalhes) {
    console.log('Gerando relatório de exclusão...');
    
    // Prepara dados para o CSV
    const dadosRelatorio = [];
    
    // Adiciona cabeçalho
    dadosRelatorio.push({
        'MLB': 'MLB',
        'STATUS': 'STATUS', 
        'MENSAGEM': 'MENSAGEM',
        'DATA_HORA': 'DATA_HORA'
    });
    
    // Adiciona sucessos
    const sucessosLista = detalhes.filter(d => d.sucesso);
    sucessosLista.forEach(item => {
        dadosRelatorio.push({
            'MLB': item.mlb,
            'STATUS': 'SUCESSO',
            'MENSAGEM': item.mensagem || 'Excluído com sucesso',
            'DATA_HORA': new Date().toLocaleString('pt-BR')
        });
    });
    
    // Adiciona erros
    const errosLista = detalhes.filter(d => !d.sucesso);
    errosLista.forEach(item => {
        dadosRelatorio.push({
            'MLB': item.mlb,
            'STATUS': 'ERRO',
            'MENSAGEM': item.erro || 'Erro desconhecido',
            'DATA_HORA': new Date().toLocaleString('pt-BR')
        });
    });
    
    // Converte para CSV
    const cabecalho = ['MLB', 'STATUS', 'MENSAGEM', 'DATA_HORA'];
    const linhas = dadosRelatorio.slice(1).map(row => 
        cabecalho.map(col => {
            let valor = row[col] || '';
            // Escape de aspas e vírgulas
            if (typeof valor === 'string' && (valor.includes(',') || valor.includes('"'))) {
                valor = `"${valor.replace(/"/g, '""')}"`;
            }
            return valor;
        }).join(',')
    );
    
    const csvContent = [cabecalho.join(','), ...linhas].join('\n');
    
    // Adiciona BOM para UTF-8 com acentos
    const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // Cria link para download
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    
    // Nome do arquivo com data/hora
    const dataHora = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    link.setAttribute('download', `relatorio_exclusao_${dataHora}.csv`);
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    mostrarMensagem(`📥 Relatório baixado: ${dadosRelatorio.length - 1} registros (${sucessosLista.length} sucessos, ${errosLista.length} erros)`, 'success');
    
    console.log(`Relatório gerado: ${sucessosLista.length} sucessos, ${errosLista.length} erros`);
}

// =========================================
// FINALIZAR PROGRESSO (COM DOWNLOAD)
// =========================================

function finalizarProgresso(sucessos, erros, total, detalhes) {
    console.log(`Finalizando: ${sucessos} sucessos, ${erros} erros de ${total} total`);
    
    // Para o intervalo de tempo
    if (tempoRestanteIntervalo) {
        clearInterval(tempoRestanteIntervalo);
        tempoRestanteIntervalo = null;
    }
    
    // Remove animação da barra
    const progressoBar = document.getElementById('progressoBar');
    if (progressoBar) {
        progressoBar.classList.remove('progress-bar-animated');
        
        if (erros === 0) {
            progressoBar.classList.remove('bg-danger', 'bg-warning');
            progressoBar.classList.add('bg-success');
        } else if (sucessos > 0) {
            progressoBar.classList.remove('bg-danger', 'bg-success');
            progressoBar.classList.add('bg-warning');
        }
    }
    
    // Atualiza status final
    const progressoStatus = document.getElementById('progressoStatus');
    if (progressoStatus) {
        if (erros === 0) {
            progressoStatus.innerHTML = '<span class="text-success"><i class="fas fa-check-circle"></i> Concluído com sucesso!</span>';
        } else if (sucessos === 0) {
            progressoStatus.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle"></i> Falha completa</span>';
        } else {
            progressoStatus.innerHTML = `<span class="text-warning"><i class="fas fa-exclamation-circle"></i> Concluído com ${erros} erro(s)</span>`;
        }
    }
    
    // Atualiza contador final
    const progressoContador = document.getElementById('progressoContador');
    if (progressoContador) {
        progressoContador.textContent = `Total: ${total} | Sucessos: ${sucessos} | Erros: ${erros}`;
    }
    
    // Mostra resumo
    const resumoExclusao = document.getElementById('resumoExclusao');
    if (resumoExclusao) {
        resumoExclusao.style.display = 'block';
    }
    
    // Atualiza números do resumo
    const totalSucesso = document.getElementById('totalSucesso');
    const totalErrosSpan = document.getElementById('totalErros');
    
    if (totalSucesso) totalSucesso.textContent = sucessos;
    if (totalErrosSpan) totalErrosSpan.textContent = erros;
    
    // LISTA DE ERROS (apenas se houver erros)
    const resumoDetalhes = document.getElementById('resumoDetalhes');
    if (resumoDetalhes) {
        const errosLista = detalhes.filter(d => !d.sucesso);
        
        if (errosLista.length > 0) {
            let html = '<div class="mt-3"><strong><i class="fas fa-exclamation-triangle text-danger"></i> MLBs com erro:</strong></div>';
            html += '<div class="table-responsive" style="max-height: 200px; overflow-y: auto;">';
            html += '<table class="table table-sm table-striped mt-2">';
            html += '<thead><tr><th>MLB</th><th>Erro</th></tr></thead><tbody>';
            
            errosLista.forEach(erro => {
                const mensagemErro = erro.erro || 'Erro desconhecido';
                const erroLimitado = mensagemErro.length > 60 ? mensagemErro.substring(0, 60) + '...' : mensagemErro;
                html += `<tr>
                            <td><code>${erro.mlb}</code></td>
                            <td class="text-danger"><small>${erroLimitado}</small></td>
                         </tr>`;
            });
            
            html += '</tbody></table></div>';
            resumoDetalhes.innerHTML = html;
        } else {
            resumoDetalhes.innerHTML = '<div class="alert alert-success mt-3 mb-0"><i class="fas fa-check-circle"></i> Nenhum erro encontrado. Todos os MLBs foram excluídos com sucesso!</div>';
        }
    }
    
    // Mostra botão de download
    const btnDownloadContainer = document.getElementById('btnDownloadContainer');
    if (btnDownloadContainer && detalhes.length > 0) {
        btnDownloadContainer.style.display = 'block';
        
        const btnDownload = document.getElementById('btnDownloadRelatorioFinal');
        if (btnDownload) {
            btnDownload.onclick = () => baixarRelatorioExclusao(sucessos, erros, detalhes);
        }
    }
    
    // Mostra botão fechar
    mostrarBotaoFechar();
    
    // Limpa estado
    emProcessamento = false;
    tempoInicioProcessamento = null;
    
    // Atualiza título
    document.title = 'MLB Manager - Exclusão Concluída';
    
    console.log(`✅ Finalizado: ${sucessos} sucessos, ${erros} erros`);
}

// =========================================
// FUNÇÕES DO MODAL DE EXCLUSÃO
// =========================================

function abrirModalExclusaoPlanilha() {
    console.log('Abrindo modal de exclusão via planilha...');
    
    // 🔴 RESET COMPLETO DE TODOS OS ESTADOS
    
    // 1. Limpa dados
    mlbsParaExcluir = [];
    emProcessamento = false;
    mlbAtual = null;
    
    // 2. Reseta campos do formulário
    document.getElementById('arquivoExclusao').value = '';
    document.getElementById('previewExclusao').innerHTML = '';
    
    // 3. Esconde barra de progresso
    const progressoContainer = document.getElementById('progressoContainer');
    if (progressoContainer) {
        progressoContainer.style.display = 'none';
    }
    
    // 4. Esconde resumo
    const resumoExclusao = document.getElementById('resumoExclusao');
    if (resumoExclusao) {
        resumoExclusao.style.display = 'none';
    }
    
    // 5. Reseta completamente a barra de progresso
    const progressoBar = document.getElementById('progressoBar');
    if (progressoBar) {
        progressoBar.style.width = '0%';
        progressoBar.classList.remove('bg-success', 'bg-warning', 'progress-bar-animated');
        progressoBar.classList.add('bg-danger', 'progress-bar-animated');
    }
    
    // 6. Reseta textos da barra
    const progressoTexto = document.getElementById('progressoTexto');
    if (progressoTexto) {
        progressoTexto.textContent = '0%';
    }
    
    const progressoStatus = document.getElementById('progressoStatus');
    if (progressoStatus) {
        progressoStatus.textContent = 'Aguardando início...';
    }
    
    const progressoContador = document.getElementById('progressoContador');
    if (progressoContador) {
        progressoContador.textContent = '0/0 processados';
    }
    
    // 7. Reseta detalhes do progresso
    const progressoDetalhes = document.getElementById('progressoDetalhes');
    if (progressoDetalhes) {
        progressoDetalhes.innerHTML = '';
    }
    
    // 8. Reseta resumo detalhado
    const resumoDetalhes = document.getElementById('resumoDetalhes');
    if (resumoDetalhes) {
        resumoDetalhes.innerHTML = '';
    }
    
    // 9. Reseta números do resumo
    const totalSucesso = document.getElementById('totalSucesso');
    const totalErros = document.getElementById('totalErros');
    if (totalSucesso) totalSucesso.textContent = '0';
    if (totalErros) totalErros.textContent = '0';
    
    // 🔴 10. RESETA OS BOTÕES IMPORTANTE!
    restaurarBotoesOriginais();
    
    // 11. Habilita input de arquivo
    const arquivoInput = document.getElementById('arquivoExclusao');
    if (arquivoInput) {
        arquivoInput.disabled = false;
    }
    
    // 12. Reseta botão iniciar exclusão
    const btnIniciar = document.getElementById('btnIniciarExclusao');
    if (btnIniciar) {
        btnIniciar.disabled = true; // Começa desabilitado
        btnIniciar.innerHTML = '<i class="fas fa-play"></i> Iniciar Exclusão';
    }
    
    // 13. Mostra o modal
    document.getElementById('modalExclusaoPlanilha').style.display = 'block';
    
    console.log('✅ Modal de exclusão aberto com reset completo');
}



function fecharModalExclusaoPlanilha() {
    console.log('Fechando modal...');
    
    // Verifica se está em processamento
    if (emProcessamento) {
        if (!confirm('A exclusão ainda está em andamento. Deseja realmente cancelar?')) {
            return;
        }
        emProcessamento = false;
    }
    
    // Fecha o modal
    document.getElementById('modalExclusaoPlanilha').style.display = 'none';
    
    // 🔴 RESETA O MODAL APÓS FECHAR (após um pequeno delay)
    setTimeout(resetarModalCompletamente, 300);
    
    console.log('✅ Modal fechado e resetado');
}

// =========================================
// PROCESSAMENTO DO ARQUIVO
// =========================================

function processarPlanilhaExclusao(input) {
    if (!input.files[0]) return;
    
    const file = input.files[0];
    console.log('Arquivo selecionado:', file.name);
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            let mlbs = [];
            const extensao = file.name.split('.').pop().toLowerCase();
            
            console.log('Processando extensão:', extensao);
            
            if (extensao === 'txt' || extensao === 'csv') {
                // Processa texto puro
                const texto = e.target.result;
                
                mlbs = texto.split(/[\n,;]+/)
                    .map(m => m.trim())
                    .filter(m => m)
                    .map(limparMLB)
                    .filter(m => m);
                    
                console.log('MLBs extraídos do texto:', mlbs.length);
                
            } else if (extensao === 'xlsx' || extensao === 'xls') {
                // Processa Excel
                const workbook = XLSX.read(e.target.result, { type: 'array' });
                const sheet = workbook.Sheets[workbook.SheetNames[0]];
                const data = XLSX.utils.sheet_to_json(sheet, { header: 1 });
                
                // Pega todos os valores da planilha e procura MLBs
                mlbs = [];
                data.forEach(linha => {
                    if (Array.isArray(linha)) {
                        linha.forEach(valor => {
                            if (valor && typeof valor === 'string') {
                                const mlbProcessado = limparMLB(valor);
                                if (mlbProcessado) {
                                    mlbs.push(mlbProcessado);
                                }
                            }
                        });
                    }
                });
                
                console.log('MLBs extraídos do Excel:', mlbs.length);
            }
            
            // Remove duplicatas
            mlbsParaExcluir = [...new Set(mlbs)];
            
            console.log('MLBs únicos encontrados:', mlbsParaExcluir.length);
            
            if (mlbsParaExcluir.length === 0) {
                mostrarMensagem('Nenhum MLB válido encontrado no arquivo', 'error');
                return;
            }
            
            // Mostra preview
            mostrarPreviewExclusao(mlbsParaExcluir);
            
        } catch (error) {
            console.error('Erro ao processar arquivo:', error);
            mostrarMensagem('Erro ao processar arquivo: ' + error.message, 'error');
        }
    };
    
    reader.onerror = function(error) {
        console.error('Erro na leitura do arquivo:', error);
        mostrarMensagem('Erro ao ler arquivo', 'error');
    };
    
    if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        reader.readAsArrayBuffer(file);
    } else {
        reader.readAsText(file);
    }
}

// =========================================
// FUNÇÃO DE PREVIEW SIMPLIFICADA
// =========================================

function mostrarPreviewExclusao(mlbs) {
    const preview = document.getElementById('previewExclusao');
    
    // Mostra apenas informações resumidas, sem listagem
    let html = `<div class="alert alert-info">
        <i class="fas fa-info-circle"></i>
        <strong>${mlbs.length} MLBs encontrados para exclusão</strong>
        <br><small>Serão excluídos permanentemente</small>
    </div>`;
    
    // Adiciona aviso sobre o tempo
    const tempoEstimadoMinutos = Math.ceil(mlbs.length / 120);
    html += `<div class="alert alert-secondary mt-2 small">
        <i class="fas fa-clock"></i> 
        <strong>Tempo estimado:</strong> Aproximadamente ${tempoEstimadoMinutos} minuto(s) 
        (processando ~2 MLBs por segundo)
    </div>`;
    
    preview.innerHTML = html;
    document.getElementById('btnIniciarExclusao').disabled = false;
    
    console.log('Preview gerado para', mlbs.length, 'MLBs');
}

// =========================================
// EXCLUSÃO EM MASSA (ATUALIZADA COM PROGRESSO)
// =========================================

async function iniciarExclusaoEmMassa() {
    console.log('Iniciando exclusão em massa...', mlbsParaExcluir.length, 'MLBs');
    
    if (mlbsParaExcluir.length === 0) {
        mostrarMensagem('Nenhum MLB para excluir', 'error');
        return;
    }
    
    if (!confirm(`EXCLUIR ${mlbsParaExcluir.length} ANÚNCIOS?\n\nEsta ação é irreversível!`)) {
        console.log('Exclusão cancelada pelo usuário');
        return;
    }
    
    const total = mlbsParaExcluir.length;
    let sucessos = 0;
    let erros = 0;
    const detalhes = [];
    
    // Inicia barra de progresso
    iniciarProgresso(total);
    
    // Processa cada MLB individualmente
    for (let i = 0; i < total; i++) {
        const mlb = mlbsParaExcluir[i];
        
        // Atualiza progresso
        atualizarProgresso(
            i + 1,  // CORREÇÃO: i+1 para mostrar o atual como processado
            total, 
            `Excluindo MLB ${i + 1} de ${total}`,
            mlb
        );
        
        try {
            // Faz a requisição para excluir
            const response = await fetch('/api/mercadolivre/excluir-definitivo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mlb: mlb })
            });
            
            const resultado = await response.json();
            
            // Registra resultado
            if (resultado.sucesso) {
                sucessos++;
                detalhes.push({
                    mlb: mlb,
                    sucesso: true,
                    mensagem: resultado.mensagem || 'Excluído com sucesso'
                });
                
                // Remove da visualização se estiver na tabela
                removerDaTabela(mlb);
                
            } else {
                erros++;
                detalhes.push({
                    mlb: mlb,
                    sucesso: false,
                    erro: resultado.erro || 'Erro desconhecido'
                });
            }
            
        } catch (error) {
            erros++;
            detalhes.push({
                mlb: mlb,
                sucesso: false,
                erro: 'Erro de conexão: ' + error.message
            });
        }
        
        // Pequeno delay para não sobrecarregar a API (300ms)
        if (i < total - 1) {
            await new Promise(resolve => setTimeout(resolve, 150));
        }
    }
    
    // CORREÇÃO: Garantir que o último item foi atualizado
    atualizarProgresso(
        total, 
        total, 
        'Processamento concluído',
        ''
    );
    
    // CORREÇÃO: Pequeno delay antes de finalizar
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Finaliza progresso
    finalizarProgresso(sucessos, erros, total, detalhes);
    
    // Mostra mensagem de conclusão
    if (erros === 0) {
        mostrarMensagem(`✅ Exclusão concluída com sucesso! Todos os ${total} anúncios foram excluídos.`, 'success');
    } else if (sucessos === 0) {
        mostrarMensagem(`❌ Falha completa! Nenhum anúncio foi excluído.`, 'error');
    } else {
        mostrarMensagem(`⚠️ Exclusão parcialmente concluída! Sucesso: ${sucessos}, Erros: ${erros}`, 'warning');
    }
    
    console.log('Processo de exclusão finalizado');
}

// =========================================
// EXCLUSÃO INDIVIDUAL (MANTIDA)
// =========================================

function excluirMLB(mlb) {
    mlbAtual = limparMLB(mlb);
    
    if (!mlbAtual) {
        mostrarMensagem('MLB inválido', 'error');
        return;
    }
    
    if (!confirm(`EXCLUIR ANÚNCIO?\n\nMLB: ${mlbAtual}\n\nEsta ação é irreversível!`)) {
        return;
    }
    
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;
    
    console.log(`Excluindo MLB: ${mlbAtual}`);
    
    fetch('/api/mercadolivre/excluir-definitivo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mlb: mlbAtual })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarMensagem(`✅ MLB ${mlbAtual} excluído com sucesso!`, 'success');
            
            // Remove da tabela
            removerDaTabela(mlbAtual);
            
        } else {
            mostrarMensagem(`❌ Erro: ${data.erro || 'Erro desconhecido'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarMensagem('Erro de conexão', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

// =========================================
// FUNÇÕES AUXILIARES (MANTIDAS)
// =========================================

function limparMLB(mlb) {
    if (!mlb) return null;
    
    let mlbStr = mlb.toString().trim().toUpperCase();
    
    // Remove todos os caracteres não alfanuméricos
    mlbStr = mlbStr.replace(/[^A-Z0-9]/g, '');
    
    if (mlbStr.startsWith('MLB')) {
        return mlbStr;
    } else if (/^\d+$/.test(mlbStr)) {
        return 'MLB' + mlbStr;
    } else if (mlbStr.length > 3) {
        // Tenta encontrar MLB dentro do texto
        const match = mlbStr.match(/MLB\d+/);
        if (match) return match[0];
    }
    
    return null;
}

function removerDaTabela(mlb) {
    const linhas = document.querySelectorAll('#ordersTableBody tr');
    let encontrado = false;
    
    linhas.forEach(linha => {
        const mlbCell = linha.querySelector('td:nth-child(2) strong');
        if (mlbCell && mlbCell.textContent === mlb) {
            linha.style.transition = 'opacity 0.5s';
            linha.style.opacity = '0.3';
            linha.style.textDecoration = 'line-through';
            
            setTimeout(() => {
                linha.remove();
                if (document.querySelectorAll('#ordersTableBody tr').length === 0) {
                    document.getElementById('ordersContainer').classList.add('hidden');
                    document.getElementById('emptyState').classList.remove('hidden');
                }
            }, 1000);
            
            encontrado = true;
        }
    });
    
    if (!encontrado) {
        console.log('MLB não encontrado na tabela:', mlb);
    }
}

function mostrarMensagem(mensagem, tipo) {
    // Cria alerta temporário
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'info'}`;
    alertDiv.innerHTML = `
        <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle'}"></i>
        ${mensagem}
    `;
    
    // Adiciona no container
    const container = document.querySelector('.mercado-livre-container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove após 3 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// =========================================
// INTEGRAÇÃO COM A TABELA (MANTIDA)
// =========================================

function adicionarBotoesExclusao() {
    document.querySelectorAll('#ordersTableBody tr').forEach(linha => {
        const mlbCell = linha.querySelector('td:nth-child(2) strong');
        const botoesCell = linha.querySelector('td:last-child');
        
        if (mlbCell && botoesCell && !botoesCell.querySelector('.btn-excluir-simples')) {
            const mlb = mlbCell.textContent;
            
            // Cria botão de exclusão
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-outline-danger btn-excluir-simples ms-1';
            btn.innerHTML = '<i class="fas fa-trash-alt"></i>';
            btn.title = 'Excluir anúncio';
            
            // Adiciona evento
            btn.onclick = function(e) {
                e.stopPropagation();
                e.preventDefault();
                excluirMLB(mlb);
            };
            
            botoesCell.appendChild(btn);
        }
    });
}

// =========================================
// FUNÇÕES PARA CONTROLE DOS BOTÕES
// =========================================

function mostrarBotoesPreProcessamento(mostrar = true) {
    const botoesPre = document.getElementById('botoesPreProcessamento');
    const botoesPos = document.getElementById('botaoPosProcessamento');
    
    if (botoesPre) {
        botoesPre.style.display = mostrar ? 'block' : 'none';
    }
    
    if (botoesPos) {
        botoesPos.style.display = mostrar ? 'none' : 'block';
    }
}

function resetarModalCompletamente() {
    console.log('🔄 Resetando modal completamente...');
    
    // Chama a mesma lógica da abertura, mas sem mostrar o modal
    mlbsParaExcluir = [];
    emProcessamento = false;
    
    const progressoBar = document.getElementById('progressoBar');
    if (progressoBar) {
        progressoBar.style.width = '0%';
        progressoBar.classList.remove('bg-success', 'bg-warning');
        progressoBar.classList.add('bg-danger');
        progressoBar.classList.add('progress-bar-animated');
    }
    
    const progressoTexto = document.getElementById('progressoTexto');
    if (progressoTexto) {
        progressoTexto.textContent = '0%';
    }
    
    const progressoStatus = document.getElementById('progressoStatus');
    if (progressoStatus) {
        progressoStatus.textContent = 'Aguardando início...';
    }
    
    restaurarBotoesOriginais();
    
    console.log('✅ Modal resetado completamente');
}

function mostrarBotaoFechar() {
    const botoesPre = document.getElementById('botoesPreProcessamento');
    const botoesPos = document.getElementById('botaoPosProcessamento');
    
    if (botoesPre) {
        botoesPre.style.display = 'none';
    }
    
    if (botoesPos) {
        botoesPos.style.display = 'block';
    }
    
    console.log('✅ Botão "Fechar" ativado');
}

function restaurarBotoesOriginais() {
    const botoesPre = document.getElementById('botoesPreProcessamento');
    const botoesPos = document.getElementById('botaoPosProcessamento');
    
    if (botoesPre) {
        botoesPre.style.display = 'flex'; // ou 'block'
        botoesPre.style.gap = '10px'; // para espaçamento
    }
    
    if (botoesPos) {
        botoesPos.style.display = 'none';
    }
    
    console.log('🔁 Botões restaurados ao estado original');
}


// =========================================
// INICIALIZAÇÃO (ATUALIZADA)
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Sistema de exclusão carregado (com barra de progresso)');
    
    // Configurar evento para o input de arquivo
    const arquivoExclusao = document.getElementById('arquivoExclusao');
    if (arquivoExclusao) {
        arquivoExclusao.addEventListener('change', function(e) {
            processarPlanilhaExclusao(this);
        });
        console.log('✅ Input de arquivo configurado');
    }
    
    // Configurar botão de iniciar exclusão
    const btnIniciarExclusao = document.getElementById('btnIniciarExclusao');
    if (btnIniciarExclusao) {
        btnIniciarExclusao.onclick = iniciarExclusaoEmMassa;
        console.log('✅ Botão iniciar exclusão configurado');
    }
    
    // Adicionar botões de exclusão nas linhas
    setTimeout(adicionarBotoesExclusao, 1000);
    
    // Observar mudanças na tabela
    const tabela = document.getElementById('ordersTableBody');
    if (tabela) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    setTimeout(adicionarBotoesExclusao, 100);
                }
            });
        });
        
        observer.observe(tabela, { childList: true, subtree: true });
        console.log('✅ Observer configurado para tabela');
    }
    
    // Fechar modal ao clicar fora
    const modalExclusao = document.getElementById('modalExclusaoPlanilha');
    if (modalExclusao) {
        modalExclusao.onclick = function(event) {
            if (event.target === modalExclusao) {
                fecharModalExclusaoPlanilha();
            }
        };
        console.log('✅ Evento de fechar modal configurado');
    }
    
    console.log('✅ Sistema de exclusão totalmente inicializado');
});