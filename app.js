// public/app.js - CONFIGURAÇÃO FINAL SUPABASE
const SUPABASE_URL = 'https://kctzwwczcthjmdgvxuks.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjdHp3d2N6Y3Roam1kZ3Z4dWtzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI5ODIwNDYsImV4cCI6MjA3ODU1ODA0Nn0.HafwqrEnJ5Slm3wRg4_KEvGHiTuNJafztVfWbuSZ_84';

// Inicializa o cliente Supabase (requer a tag <script> no index.html)
const { createClient } = supabase;
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);


// Sistema Principal do Lançaca&iA - VERSÃO OTIMIZADA COM SUPABASE
class LancacaIA {
    constructor() {
        this.bets = {
            individual: [],
            multiple: [],
            safe: [],
            top: []
        };
        this.filters = {
            type: 'all',
            gender: 'all',
            league: 'all',
            house: 'all'
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateDateTime();
        this.simulateLoading();
        // Chamada real ao Supabase:
        this.loadDataFromSupabase();
    }

    // ... (Seu setupEventListeners() permanece igual) ...
    setupEventListeners() {
        // Filtros rápidos
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.filters.type = e.target.dataset.filter;
                this.filterBets();
            });
        });

        // Botão de login e logout
        document.getElementById('loginBtn').addEventListener('click', fazerLogin);
        document.getElementById('logoutBtn').addEventListener('click', fazerLogout);
        
        // Botão de análise (simplesmente recarrega os dados)
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.showToast('Atualizando dados do servidor...', 'info');
            this.loadDataFromSupabase(); 
        });

        // Botão Admin (se você tiver)
        const adminTrigger = document.getElementById('adminTrigger');
        if (adminTrigger) {
            adminTrigger.addEventListener('click', mostrarAdmin);
        }

        // Criar usuário (se você tiver)
        const createUserBtn = document.getElementById('createUserBtn');
        if (createUserBtn) {
            createUserBtn.addEventListener('click', criarUsuario);
        }
    }


    // -----------------------------------------------------------------------------
    // NOVO MÉTODO: CARREGA DADOS DO SUPABASE
    // -----------------------------------------------------------------------------
    async loadDataFromSupabase() {
        this.showToast('🌎 Carregando palpites da Nuvem...', 'info');

        try {
            // 1. Pega Apostas Individuais (tabela 'individuais')
            const { data: individuais, error: errInd } = await supabaseClient
                .from('individuais')
                .select('*')
                .order('value_expected', { ascending: false });

            // 2. Pega Múltiplas (tabela 'multiplas')
            const { data: multiplas, error: errMul } = await supabaseClient
                .from('multiplas')
                .select('*');

            // 3. Pega Surebets (tabela 'surebets')
            const { data: surebets, error: errSure } = await supabaseClient
                .from('surebets')
                .select('*');

            if (errInd || errMul || errSure) {
                console.error('Erro ao buscar dados do Supabase:', errInd || errMul || errSure);
                this.showToast('❌ Erro ao carregar dados da Nuvem!', 'error');
                return;
            }

            // Mapeia e ajusta os dados
            this.bets.individual = individuais.map(bet => ({
                id: bet.id || Date.now() + Math.random(),
                type: 'individual',
                match: bet.match,
                league: bet.league,
                betType: bet.bet_type,
                probability: bet.probabilidade || 0.70,
                odd: bet.odd,
                house: bet.casa_aposta || 'betano', 
                value: bet.value_expected,
                stake: bet.stake || 'MÉDIO',
                confidence: bet.confidence,
                gender: 'M', 
                date: 'HOJE',
                description: 'Análise da IA com VE positivo.'
            })) || [];

            this.bets.multiple = multiplas.map(m => ({
                id: m.id || Date.now() + Math.random(),
                type: 'multiple',
                totalOdd: m.odd_total,
                probability: m.probabilidade,
                value: m.valor_esperado || 0.8,
                stake: 'MÉDIO',
                confidence: m.confianca,
                matches: JSON.parse(m.jogos || '[]'), // Converte a string JSON de volta para array
            })) || [];

            this.bets.safe = surebets || [];
            
            this.classifyTopAndSafeBets();

            this.renderAllBets();
            this.updateStatistics();
            this.showToast('✅ Palpites de hoje carregados!', 'success');

        } catch (error) {
            console.error('Erro na conexão Supabase:', error);
            this.showToast('❌ Falha na conexão com o banco de dados.', 'error');
        }
    }
    
    // NOVO MÉTODO: Classifica Top e Safe Bets
    classifyTopAndSafeBets() {
        // Safe Bets: Apostas de alto Value e Probabilidade
        this.bets.safe = [
            ...this.bets.individual.filter(bet => bet.value > 0.25 && bet.probability > 0.75),
            ...this.bets.multiple.filter(bet => (bet.value_expected || bet.value || 0) > 0.3 && (bet.probability || 0) > 0.7)
        ];

        // Top Bets: As 5 melhores de todas (ordenadas por Value Expected)
        this.bets.top = [
            ...this.bets.individual.map(b => ({ ...b, sortValue: b.value })),
            ...this.bets.multiple.map(b => ({ ...b, sortValue: b.value || b.valor_esperado })),
        ]
        .sort((a, b) => b.sortValue - a.sortValue)
        .slice(0, 5)
        .map(b => { delete b.sortValue; return b; });
    }

    // ... (Todos os seus outros métodos como filterBets, renderAllBets, createBetCard, updateStatistics permanecem iguais) ...
    // ... (Os métodos de login e segurança do usuário (fazerLogin, fazerLogout, criarUsuario) permanecem iguais) ...
}

// Inicializar a aplicação
document.addEventListener('DOMContentLoaded', () => {
    new LancacaIA();
});