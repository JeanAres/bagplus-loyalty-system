const API_URL = 'http://localhost:8000';

// Buscar sacola
async function buscarSacola() {
    const input = document.getElementById('sacolaInput');
    const sacolaId = input.value.trim();
    
    if (!sacolaId) {
        mostrarErro('Por favor, digite o código da sacola');
        return;
    }
    
    esconderErro();
    esconderSucesso();
    esconderInformacoes();
    
    try {
        const response = await fetch(`${API_URL}/api/sacolas/${sacolaId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Sacola não encontrada');
            }
            throw new Error('Erro ao buscar sacola');
        }
        
        const data = await response.json();
        mostrarInformacoes(data);
        
    } catch (error) {
        mostrarErro(error.message);
    }
}

// Mostrar informações da sacola
function mostrarInformacoes(data) {
    // Preencher dados do cliente
    document.getElementById('clienteNome').textContent = data.cliente.nome;
    document.getElementById('clienteCpf').textContent = data.cliente.cpf;
    
    // Preencher dados da sacola
    document.getElementById('sacolaId').textContent = data.sacola.id;
    
    const statusBadge = document.getElementById('sacolaStatus');
    statusBadge.textContent = data.sacola.status.toUpperCase();
    statusBadge.className = `status-badge ${data.sacola.status}`;
    
    // Estatísticas
    const utilizacoes = data.sacola.utilizacoes;
    const diasUso = data.sacola.dias_de_uso;
    
    document.getElementById('utilizacoes').textContent = `${utilizacoes} / 40`;
    document.getElementById('diasUso').textContent = `${diasUso} / 90 dias`;
    
    // Barra de progresso de utilizações
    const progressBar = document.getElementById('progressBar');
    const percentUsos = (utilizacoes / 40) * 100;
    progressBar.style.width = `${percentUsos}%`;
    
    if (utilizacoes <= 15) {
        progressBar.className = 'progress-fill';
    } else if (utilizacoes <= 25) {
        progressBar.className = 'progress-fill warning';
    } else {
        progressBar.className = 'progress-fill danger';
    }
    
    // Barra de progresso de dias
    const progressBarDias = document.getElementById('progressBarDias');
    const percentDias = (diasUso / 90) * 100;
    progressBarDias.style.width = `${percentDias}%`;
    
    if (diasUso <= 60) {
        progressBarDias.className = 'progress-fill';
    } else if (diasUso <= 80) {
        progressBarDias.className = 'progress-fill warning';
    } else {
        progressBarDias.className = 'progress-fill danger';
    }
    
    // Última utilização
    if (data.sacola.ultima_utilizacao) {
        const data_uso = new Date(data.sacola.ultima_utilizacao);
        document.getElementById('ultimaUtilizacao').textContent = 
            data_uso.toLocaleDateString('pt-BR') + ' às ' + 
            data_uso.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    } else {
        document.getElementById('ultimaUtilizacao').textContent = 'Nunca utilizada';
    }
    
    // Mostrar desconto por fidelidade
    mostrarDescontoFidelidade(data.fidelidade, utilizacoes);
    
    // Mostrar desconto por devolução
    mostrarDescontoDevolucao(data.desconto_devolucao, utilizacoes, diasUso);
    
    // Mostrar seção
    document.getElementById('sacolaInfo').classList.remove('hidden');
}

// Mostrar desconto por fidelidade
function mostrarDescontoFidelidade(fidelidade, utilizacoes) {
    const descontoAtual = fidelidade.desconto_atual;
    const proximoMarco = fidelidade.proximo_marco;
    const proximoDesconto = fidelidade.proximo_desconto;
    const usosParaProximo = fidelidade.usos_para_proximo;
    
    // Mostrar desconto atual
    document.getElementById('descontoFidelidadeAtual').textContent = 
        'R$ ' + descontoAtual.toFixed(2).replace('.', ',');
    
    const progressoDiv = document.getElementById('progressoMarco');
    
    if (proximoMarco) {
        // Ainda tem marcos para atingir
        const percentProgresso = ((utilizacoes % 10) / 10) * 100;
        
        progressoDiv.innerHTML = `
            <p><strong>Próximo marco:</strong> ${proximoMarco} utilizações</p>
            <p>Faltam <strong>${usosParaProximo} ${usosParaProximo === 1 ? 'uso' : 'usos'}</strong> para ganhar <strong>R$ ${proximoDesconto.toFixed(2).replace('.', ',')}</strong></p>
            <div class="progress-bar-marco">
                <div class="progress-fill-marco" style="width: ${percentProgresso}%">
                    ${Math.round(percentProgresso)}%
                </div>
            </div>
        `;
    } else {
        // Atingiu o último marco
        progressoDiv.innerHTML = `
            <div class="marco-atingido">
                🎉 Desconto máximo atingido!
            </div>
            <p style="text-align: center; margin-top: 10px; color: #666; font-size: 0.9rem;">
                Cliente atingiu o maior desconto por fidelidade.
            </p>
        `;
    }
}

// Mostrar desconto por devolução
// Mostrar desconto por devolução
function mostrarDescontoDevolucao(descontoDevolucao, utilizacoes, diasUso) {
    document.getElementById('descontoDevolucaoAtual').textContent = 
        'R$ ' + descontoDevolucao.toFixed(2).replace('.', ',');
    
    const incentivoDiv = document.getElementById('incentivoDevolucao');
    let mensagem = '';
    let classe = '';
    
    // Determinar estado e mensagem
    if (descontoDevolucao === 40.00) {
        // 🟢 Verde (10-15 usos, ≤60 dias)
        mensagem = `<strong>🟢 Estado Verde - Desconto Máximo!</strong> Sacola em excelente estado (${utilizacoes}/40 usos, ${diasUso}/90 dias). Cliente receberá R$ 40,00 na devolução.`;
        classe = '';
    } else if (descontoDevolucao === 20.00) {
        // 🟡 Amarelo (16-25 usos, ≤80 dias)
        mensagem = `<strong>🟡 Estado Amarelo.</strong> Sacola com ${utilizacoes} usos e ${diasUso} dias. Cliente receberá R$ 20,00 na devolução.`;
        classe = 'alerta';
    } else if (descontoDevolucao === 10.00) {
        // 🔴 Vermelho (26-40 usos, ≤90 dias)
        mensagem = `<strong>🔴 Estado Vermelho - Fim de Vida!</strong> Sacola próxima do limite (${utilizacoes}/40 usos, ${diasUso}/90 dias). Cliente receberá R$ 10,00.`;
        classe = 'urgente';
    } else {
        // ⚫ Sem desconto
        if (utilizacoes < 10) {
            mensagem = `<strong>⚫ Sem Desconto de Devolução.</strong> Sacola com apenas ${utilizacoes} usos. <strong>Mínimo 10 usos para ganhar desconto.</strong> Cliente pode continuar usando.`;
        } else if (utilizacoes > 40 || diasUso > 90) {
            mensagem = `<strong>⚫ Expirado.</strong> Sacola ultrapassou limites (${utilizacoes}/40 usos, ${diasUso}/90 dias). <strong>Sem desconto de devolução.</strong> Cliente pode devolver para descarte adequado.`;
        } else {
            mensagem = `<strong>⚫ Sem Desconto de Devolução.</strong> Condições não atingidas para desconto. Cliente pode continuar usando ou devolver para descarte adequado.`;
        }
        classe = 'urgente';
    }
    
    incentivoDiv.className = `desconto-incentivo ${classe}`;
    incentivoDiv.innerHTML = `<p>${mensagem}</p>`;
}

// Registrar uso
async function registrarUso() {
    const sacolaId = document.getElementById('sacolaId').textContent;
    
    esconderErro();
    esconderSucesso();
    
    try {
        const response = await fetch(`${API_URL}/api/sacolas/registrar-uso?sacola_id=${sacolaId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao registrar uso');
        }
        
        const data = await response.json();
        
        // Mostrar mensagem de sucesso
        mostrarSucesso(`✅ Uso registrado com sucesso! Agora: ${data.sacola.utilizacoes} / 40 utilizações`);
        
        // Atualizar informações diretamente pela API
        setTimeout(async () => {
            try {
                const response = await fetch(`${API_URL}/api/sacolas/${sacolaId}`);
                if (response.ok) {
                    const data = await response.json();
                    mostrarInformacoes(data);
                }
            } catch (error) {
                console.error('Erro ao atualizar:', error);
            }
        }, 1500);
        
    } catch (error) {
        mostrarErro(error.message);
    }
}

// Mostrar modal de devolução
function mostrarModalDevolucao() {
    const sacolaId = document.getElementById('sacolaId').textContent;
    const utilizacoes = document.getElementById('utilizacoes').textContent;
    const diasUso = document.getElementById('diasUso').textContent;
    const descontoDevolucao = document.getElementById('descontoDevolucaoAtual').textContent;
    
    document.getElementById('modalSacolaId').textContent = sacolaId;
    document.getElementById('modalUtilizacoes').textContent = utilizacoes;
    document.getElementById('modalDias').textContent = diasUso;
    document.getElementById('descontoValor').textContent = descontoDevolucao;
    
    document.getElementById('modalDevolucao').classList.remove('hidden');
}

// Fechar modal
function fecharModal() {
    document.getElementById('modalDevolucao').classList.add('hidden');
}

// Confirmar devolução
async function confirmarDevolucao() {
    const sacolaId = document.getElementById('modalSacolaId').textContent;
    
    try {
        const response = await fetch(`${API_URL}/api/sacolas/devolver?sacola_id=${sacolaId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao processar devolução');
        }
        
        const data = await response.json();
        
        fecharModal();
        mostrarSucesso(`✅ Devolução processada! Desconto concedido: R$ ${data.devolucao.desconto_concedido.toFixed(2).replace('.', ',')}`);
        
        // Atualizar informações
        setTimeout(() => {
            buscarSacola();
        }, 2000);
        
    } catch (error) {
        fecharModal();
        mostrarErro(error.message);
    }
}

// Limpar tela
function limparTela() {
    document.getElementById('sacolaInput').value = '';
    document.getElementById('cpfInput').value = '';
    esconderInformacoes();
    document.getElementById('listaSacolas').classList.add('hidden');
    esconderErro();
    esconderSucesso();
    
    // Focar no input ativo
    if (document.getElementById('buscaCodigo').classList.contains('active')) {
        document.getElementById('sacolaInput').focus();
    } else {
        document.getElementById('cpfInput').focus();
    }
}

// Funções auxiliares
function mostrarErro(mensagem) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = '❌ ' + mensagem;
    errorDiv.classList.remove('hidden');
}

function esconderErro() {
    document.getElementById('errorMessage').classList.add('hidden');
}

function mostrarSucesso(mensagem) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = mensagem;
    successDiv.classList.remove('hidden');
    
    setTimeout(() => {
        successDiv.classList.add('hidden');
    }, 5000);
}

function esconderSucesso() {
    document.getElementById('successMessage').classList.add('hidden');
}

function esconderInformacoes() {
    document.getElementById('sacolaInfo').classList.add('hidden');
}

// Enter no input de busca
document.getElementById('sacolaInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        buscarSacola();
    }
});

// Mudar entre tabs
function mudarTab(tab) {
    // Remover active de todos
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Ativar tab selecionada
    if (tab === 'codigo') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('buscaCodigo').classList.add('active');
        document.getElementById('sacolaInput').focus();
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('buscaCpf').classList.add('active');
        document.getElementById('cpfInput').focus();
    }
    
    // Limpar tela
    limparTela();
}

// Formatar CPF automaticamente
document.getElementById('cpfInput').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length <= 11) {
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        e.target.value = value;
    }
});

// Buscar por CPF
async function buscarPorCpf() {
    const input = document.getElementById('cpfInput');
    const cpf = input.value.trim();
    
    // Validar input
    if (!cpf) {
        mostrarErro('Por favor, digite o CPF');
        return;
    }
    
    // Limpar mensagens
    esconderErro();
    esconderSucesso();
    esconderInformacoes();
    
    try {
        // Chamar API
        const response = await fetch(`${API_URL}/api/clientes/${cpf}/sacolas`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Cliente não encontrado');
            }
            throw new Error('Erro ao buscar sacolas');
        }
        
        const data = await response.json();
        
        if (data.total_sacolas === 0) {
            throw new Error('Cliente não possui sacolas ativas');
        }
        
        // Se tem apenas 1 sacola, buscar direto
        if (data.total_sacolas === 1) {
            document.getElementById('sacolaInput').value = data.sacolas[0].id;
            mudarTab('codigo');
            buscarSacola();
            return;
        }
        
        // Se tem múltiplas, mostrar lista
        mostrarListaSacolas(data);
        
    } catch (error) {
        mostrarErro(error.message);
    }
}

// Mostrar lista de sacolas
function mostrarListaSacolas(data) {
    document.getElementById('clienteNomeLista').textContent = data.cliente.nome;
    document.getElementById('clienteCpfLista').textContent = data.cliente.cpf;
    
    const container = document.getElementById('sacolasContainer');
    container.innerHTML = '';
    
    data.sacolas.forEach(sacola => {
        const card = document.createElement('div');
        card.className = 'sacola-card';
        card.onclick = () => selecionarSacola(sacola.id);
        
        // Determinar status visual
        let statusClass = 'novo';
        let statusText = '🟢 Nova';
        
        if (sacola.utilizacoes > 25) {
            statusClass = 'antigo';
            statusText = '🔴 Antiga';
        } else if (sacola.utilizacoes > 15) {
            statusClass = 'medio';
            statusText = '🟡 Média';
        }
        
        card.innerHTML = `
            <div class="sacola-card-header">
                <span class="sacola-card-id">${sacola.id}</span>
                <span class="sacola-card-status ${statusClass}">${statusText}</span>
            </div>
            <div class="sacola-card-info">
                <div><strong>Utilizações:</strong> ${sacola.utilizacoes} / 40</div>
                <div><strong>Dias de uso:</strong> ${sacola.dias_de_uso} / 90</div>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    // Mostrar seção
    document.getElementById('listaSacolas').classList.remove('hidden');
}

// Selecionar sacola da lista
async function selecionarSacola(sacolaId) {
    // Esconder lista
    document.getElementById('listaSacolas').classList.add('hidden');
    
    // Limpar mensagens
    esconderErro();
    esconderSucesso();
    
    try {
        // Buscar informações da sacola diretamente
        const response = await fetch(`${API_URL}/api/sacolas/${sacolaId}`);
        
        if (!response.ok) {
            throw new Error('Erro ao buscar informações da sacola');
        }
        
        const data = await response.json();
        
        // Mostrar informações diretamente
        mostrarInformacoes(data);
        
    } catch (error) {
        mostrarErro(error.message);
    }
}

// Enter no CPF
document.getElementById('cpfInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        buscarPorCpf();
    }
});

// Abrir modal de cadastro
function abrirCadastroCliente() {
    document.getElementById('modalCadastro').classList.remove('hidden');
    document.getElementById('formCadastro').classList.remove('hidden');
    document.getElementById('loadingCadastro').classList.add('hidden');
    document.getElementById('successCadastro').classList.add('hidden');
    esconderErroCadastro();
    document.getElementById('cadastroCpf').focus();
}

// Fechar modal de cadastro
function fecharCadastro() {
    document.getElementById('modalCadastro').classList.add('hidden');
    document.getElementById('cadastroCpf').value = '';
    document.getElementById('cadastroNome').value = '';
    document.getElementById('cadastroQtdSacolas').value = '1';
    esconderErroCadastro();
}

// Formatar CPF no cadastro
document.getElementById('cadastroCpf').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length <= 11) {
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        e.target.value = value;
    }
});

// Mudar quantidade de sacolas
function mudarQtdSacolas(delta) {
    const input = document.getElementById('cadastroQtdSacolas');
    let valor = parseInt(input.value) + delta;
    
    if (valor < 1) valor = 1;
    if (valor > 20) valor = 20;
    
    input.value = valor;
}

// Cadastrar cliente
async function cadastrarCliente(event) {
    event.preventDefault();
    
    const cpf = document.getElementById('cadastroCpf').value.trim();
    const nome = document.getElementById('cadastroNome').value.trim();
    const qtdSacolas = parseInt(document.getElementById('cadastroQtdSacolas').value);
    
    // Limpar erro anterior
    esconderErroCadastro();
    
    // Validações
    if (!cpf || !nome) {
        mostrarErroCadastro('Preencha todos os campos obrigatórios');
        return;
    }
    
    // Validar CPF (deve ter 11 dígitos após remover pontos e traços)
    const cpfNumeros = cpf.replace(/\D/g, '');
    if (cpfNumeros.length !== 11) {
        mostrarErroCadastro('CPF inválido. Deve conter 11 dígitos');
        return;
    }
    
    // Validar nome (mínimo 3 caracteres)
    if (nome.length < 3) {
        mostrarErroCadastro('Nome deve ter pelo menos 3 caracteres');
        return;
    }
    
    // Mostrar loading
    document.getElementById('formCadastro').classList.add('hidden');
    document.getElementById('loadingCadastro').classList.remove('hidden');
    
    try {
        // 1. Criar cliente
        const responseCli = await fetch(`${API_URL}/api/clientes?cpf=${cpf}&nome=${encodeURIComponent(nome)}`, {
            method: 'POST'
        });
        
        if (!responseCli.ok) {
            const error = await responseCli.json();
            throw new Error(error.detail || 'Erro ao cadastrar cliente');
        }
        
        // 2. Criar lote de sacolas
        const responseSac = await fetch(
            `${API_URL}/api/sacolas/criar-lote?cpf_cliente=${cpf}&quantidade=${qtdSacolas}`,
            { method: 'POST' }
        );
        
        if (!responseSac.ok) {
            throw new Error('Cliente criado, mas erro ao criar sacolas');
        }
        
        const dataSac = await responseSac.json();
        
        // Mostrar sucesso
        mostrarSucessoCadastro(nome, dataSac);
        
    } catch (error) {
        // Voltar para form e mostrar erro NO MODAL
        document.getElementById('loadingCadastro').classList.add('hidden');
        document.getElementById('formCadastro').classList.remove('hidden');
        mostrarErroCadastro(error.message);
    }
}

// Mostrar sucesso do cadastro
function mostrarSucessoCadastro(nomeCliente, data) {
    document.getElementById('loadingCadastro').classList.add('hidden');
    document.getElementById('successCadastro').classList.remove('hidden');
    
    // Listar sacolas criadas
    const lista = document.getElementById('sacolasCriadasLista');
    lista.innerHTML = '';
    
    data.sacolas.forEach(sacolaId => {
        const item = document.createElement('div');
        item.className = 'sacola-criada-item';
        item.textContent = sacolaId;
        lista.appendChild(item);
    });
}

// Funções de erro específicas do modal de cadastro
function mostrarErroCadastro(mensagem) {
    const errorDiv = document.getElementById('errorCadastro');
    errorDiv.textContent = '❌ ' + mensagem;
    errorDiv.classList.remove('hidden');
}

function esconderErroCadastro() {
    document.getElementById('errorCadastro').classList.add('hidden');
}