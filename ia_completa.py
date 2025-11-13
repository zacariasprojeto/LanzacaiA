import os
import json
import time
from datetime import datetime
from supabase import create_client, Client

# --- Configuração ---
# As variáveis de ambiente foram lidas do Render (SUPABASE_URL e SUPABASE_KEY)
# O log anterior confirmou que esta parte agora está funcionando!
try:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("URL ou KEY do Supabase não configuradas nas variáveis de ambiente.")
    
    # Inicializa o cliente Supabase
    supabase: Client = create_client(url, key)
    print(f"✅ Supabase inicializado e conectado ao URL: {url}")
except Exception as e:
    print(f"❌ Erro Crítico ao inicializar Supabase: {e}")
    print("--- ERRO: Supabase não configurado. Verifique o Render Cron Job e as chaves. ---")
    exit(1)


# --- Funções de Mock Data (Substitua esta seção pela sua lógica de API real depois) ---

# Mock para Apostas Individuais (12 registros)
def gerar_apostas_mock():
    # Estrutura deve ser a mesma que o Front-end espera:
    return [
        {'match': 'Flamengo vs Palmeiras', 'league': 'Brasileirão Série A', 'bet_type': 'Mais de 2.5 Gols', 'odd': 2.10, 'probabilidade': 0.55, 'value_expected': 0.155, 'stake': 'MÉDIO', 'confidence': 'ALTA', 'casa_aposta': 'Betano', 'link_aposta': 'http://link.betano.com/1'},
        {'match': 'Internacional vs Atlético-MG', 'league': 'Brasileirão Série A', 'bet_type': 'Empate', 'odd': 3.40, 'probabilidade': 0.35, 'value_expected': 0.19, 'stake': 'ALTO', 'confidence': 'MUITO ALTA', 'casa_aposta': 'SportingBet', 'link_aposta': 'http://link.sportingbet.com/2'},
        {'match': 'Fluminense vs São Paulo', 'league': 'Brasileirão Série A', 'bet_type': 'Fluminense Vence', 'odd': 1.80, 'probabilidade': 0.65, 'value_expected': 0.17, 'stake': 'MÉDIO', 'confidence': 'ALTA', 'casa_aposta': 'Bet365', 'link_aposta': 'http://link.bet365.com/3'},
        # Mais 9 palpites para totalizar 12
        # ...
    ] * 4  # Apenas multiplicando para ter 12 dados de teste


# Mock para Múltiplas (1 registro)
def gerar_multiplas_mock():
    return [
        {
            'odd_total': 5.25,
            'probabilidade': 0.20,
            'valor_esperado': 0.05,
            'confianca': 'MÉDIA',
            'jogos': json.dumps([
                {'match': 'Flamengo Vence', 'bet_type': 'Flamengo'},
                {'match': 'São Paulo Vence', 'bet_type': 'São Paulo'}
            ])
        }
    ]

# Mock para Surebets (3 registros - Assumindo que você usa isso para Top 5/Apostas Seguras)
def gerar_surebets_mock():
    return [
        {'match': 'Surebet Teste 1', 'league': 'Arbitragem', 'odd': 1.95, 'probabilidade': 0.51, 'value_expected': 0.005, 'stake': 'BAIXO', 'confidence': 'MÉDIA', 'casa_aposta': 'Pinnacle', 'link_aposta': 'http://link.pinnacle.com/s1'},
        {'match': 'Surebet Teste 2', 'league': 'Arbitragem', 'odd': 2.05, 'probabilidade': 0.49, 'value_expected': 0.005, 'stake': 'BAIXO', 'confidence': 'MÉDIA', 'casa_aposta': 'Betfair', 'link_aposta': 'http://link.betfair.com/s2'},
        {'match': 'Surebet Teste 3', 'league': 'Arbitragem', 'odd': 1.85, 'probabilidade': 0.54, 'value_expected': 0.005, 'stake': 'BAIXO', 'confidence': 'MÉDIA', 'casa_aposta': 'Betano', 'link_aposta': 'http://link.betano.com/s3'},
    ]


# --- Função Principal de Salvamento com a Correção ---

def salvar_dados_supabase(dados: list, table_name: str, supabase: Client):
    try:
        # 1. Limpa dados antigos
        print(f"\n🧹 Limpando e salvando na tabela '{table_name}'...")
        
        # --- CORREÇÃO CRÍTICA AQUI ---
        # Substituímos .not_eq('id', 'algum_valor') por .gt('id', 0)
        # O gt('id', 0) é universalmente suportado para deletar todas as linhas.
        response_delete = supabase.table(table_name).delete().gt('id', 0).execute()
        
        if response_delete.count is not None:
             print(f"   ({response_delete.count} registros antigos deletados)")

        # 2. Salva novos dados
        if dados:
            response_insert = supabase.table(table_name).insert(dados).execute()
            
            # Verifica se a resposta foi bem-sucedida
            if len(response_insert.data) == len(dados):
                print(f"✅ {len(dados)} registros salvos em {table_name}!")
            else:
                print(f"⚠️ Alerta: Tentou salvar {len(dados)} mas Supabase retornou {len(response_insert.data)}. Verifique o log.")
        else:
            print(f"ℹ️ Nenhum dado para salvar em {table_name}.")

    except Exception as e:
        print(f"❌ Erro durante a operação de salvamento na tabela {table_name}: {e}")
        # Se for erro na tabela, ainda tentamos continuar para as próximas
        
# --- Execução Principal ---

if __name__ == "__main__":
    if 'supabase' in locals(): # Garante que o cliente foi inicializado
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n--- Iniciando Análise de IA em {agora} ---")

        # 1. Salvar Apostas Individuais
        individuais_mock = gerar_apostas_mock()
        salvar_dados_supabase(individuais_mock, 'individuais', supabase)

        # 2. Salvar Múltiplas
        multiplas_mock = gerar_multiplas_mock()
        salvar_dados_supabase(multiplas_mock, 'multiplas', supabase)

        # 3. Salvar Surebets
        surebets_mock = gerar_surebets_mock()
        salvar_dados_supabase(surebets_mock, 'surebets', supabase)

        print("\n--- Processo concluído ---")
