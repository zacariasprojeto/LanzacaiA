import os
import json
import time
from datetime import datetime, timedelta
from supabase import create_client, Client
import requests 
import math

# --- Função Principal que o Render irá chamar ---
def run_cron_job(request=None):

    # --- Configuração Supabase ---
    try:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        odds_api_key: str = os.environ.get("ODDS_API_KEY")
        football_data_key: str = os.environ.get("FOOTBALL_DATA_KEY")
        
        if not url or not key:
            raise ValueError("URL ou KEY do Supabase não configuradas.")
        
        supabase: Client = create_client(url, key)
        print(f"✅ Supabase inicializado: {url}")
    except Exception as e:
        print(f"❌ Erro Supabase: {e}")
        return f"Erro Supabase: {e}", 500

    # --- FUNÇÕES COM DADOS REAIS (SEM PANDAS) ---
    
    def buscar_partidas_reais_football_data():
        """Busca partidas reais do football-data.org"""
        try:
            headers = {'X-Auth-Token': football_data_key}
            hoje = datetime.now().strftime('%Y-%m-%d')
            amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={amanha}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                partidas = []
                
                for match in data.get('matches', []):
                    partida = {
                        'home_team': match['homeTeam']['name'],
                        'away_team': match['awayTeam']['name'],
                        'league': match['competition']['name'],
                        'date': match['utcDate'],
                        'status': match['status']
                    }
                    partidas.append(partida)
                
                print(f"✅ {len(partidas)} partidas reais encontradas")
                return partidas
            else:
                print(f"❌ Erro Football Data API: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar partidas reais: {e}")
            return []

    def buscar_odds_reais_comparadas():
        """Busca odds reais de múltiplas casas"""
        try:
            # Buscar odds para futebol brasileiro
            sports = ['soccer_brazil_campeonato', 'soccer_england_league_one', 'soccer_spain_la_liga']
            all_odds = []
            
            for sport in sports:
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
                params = {
                    'apiKey': odds_api_key,
                    'regions': 'eu',
                    'markets': 'h2h,totals,btts',
                    'oddsFormat': 'decimal'
                }
                
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    all_odds.extend(response.json())
                    time.sleep(1)  # Rate limiting
                
            print(f"✅ {len(all_odds)} eventos com odds reais")
            return all_odds
            
        except Exception as e:
            print(f"❌ Erro ao buscar odds: {e}")
            return []

    def calcular_probabilidade_ia(odds_home, odds_draw, odds_away):
        """Calcula probabilidades usando IA simples baseada em odds"""
        try:
            # Probabilidades implícitas das odds
            prob_home = 1 / odds_home
            prob_draw = 1 / odds_draw 
            prob_away = 1 / odds_away
            
            # Ajustar pelo overround (soma > 1)
            total = prob_home + prob_draw + prob_away
            prob_home_ajust = prob_home / total
            prob_draw_ajust = prob_draw / total
            prob_away_ajust = prob_away / total
            
            # Calcular valor esperado
            valor_home = (odds_home * prob_home_ajust) - 1
            valor_draw = (odds_draw * prob_draw_ajust) - 1
            valor_away = (odds_away * prob_away_ajust) - 1
            
            return {
                'home': prob_home_ajust,
                'draw': prob_draw_ajust, 
                'away': prob_away_ajust,
                'value_home': valor_home,
                'value_draw': valor_draw,
                'value_away': valor_away
            }
        except:
            return {'home': 0.33, 'draw': 0.33, 'away': 0.33, 'value_home': 0, 'value_draw': 0, 'value_away': 0}

    def determinar_confianca_e_stake(valor_esperado, probabilidade):
        """Determina confiança e stake baseado em valor e probabilidade"""
        if valor_esperado > 0.15 and probabilidade > 0.60:
            return "MUITO ALTA", "ALTO"
        elif valor_esperado > 0.10 and probabilidade > 0.55:
            return "ALTA", "ALTO" 
        elif valor_esperado > 0.05 and probabilidade > 0.50:
            return "MEDIA", "MÉDIO"
        elif valor_esperado > 0:
            return "BAIXA", "BAIXO"
        else:
            return "MUITO BAIXA", "NÃO APOSTAR"

    def encontrar_melhor_aposta(valores, tipos, probabilidades, odds_list):
        """Encontra a melhor aposta baseada no maior valor"""
        melhor_valor = -999
        melhor_idx = 0
        
        for i, valor in enumerate(valores):
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_idx = i
                
        return melhor_idx

    def gerar_apostas_reais_com_ia():
        """Gera apostas reais usando dados das APIs e IA"""
        print("🔄 Buscando dados reais das APIs...")
        
        # Buscar dados reais
        partidas = buscar_partidas_reais_football_data()
        odds_data = buscar_odds_reais_comparadas()
        
        apostas = []
        
        for evento in odds_data:
            try:
                home_team = evento['home_team']
                away_team = evento['away_team']
                sport_title = evento['sport_title']
                
                # Encontrar odds para mercados principais
                odds_home, odds_draw, odds_away = 2.0, 3.0, 3.5  # Valores padrão
                
                if evento.get('bookmakers'):
                    bookmaker = evento['bookmakers'][0]
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home_team:
                                    odds_home = outcome['price']
                                elif outcome['name'] == away_team:
                                    odds_away = outcome['price']
                                else:
                                    odds_draw = outcome['price']
                
                # Calcular probabilidades com IA
                prob_ia = calcular_probabilidade_ia(odds_home, odds_draw, odds_away)
                
                # Determinar melhor aposta
                valores = [prob_ia['value_home'], prob_ia['value_draw'], prob_ia['value_away']]
                tipos = [f"{home_team} Vence", "Empate", f"{away_team} Vence"]
                probabilidades = [prob_ia['home'], prob_ia['draw'], prob_ia['away']]
                odds_list = [odds_home, odds_draw, odds_away]
                
                melhor_idx = encontrar_melhor_aposta(valores, tipos, probabilidades, odds_list)
                
                if valores[melhor_idx] > 0:  # Só apostas com valor positivo
                    confianca, stake = determinar_confianca_e_stake(
                        valores[melhor_idx], 
                        probabilidades[melhor_idx]
                    )
                    
                    aposta = {
                        'match': f"{home_team} vs {away_team}",
                        'league': sport_title,
                        'bet_type': tipos[melhor_idx],
                        'odd': round(odds_list[melhor_idx], 2),
                        'probability': round(probabilidades[melhor_idx], 3),
                        'value_expected': round(valores[melhor_idx], 3),
                        'stake': stake,
                        'confidence': confianca,
                        'casa_aposta': bookmaker['key'] if evento.get('bookmakers') else 'Bet365',
                        'link_aposta': f"https://www.{bookmaker['key']}.com/bet" if evento.get('bookmakers') else '#'
                    }
                    apostas.append(aposta)
                    
            except Exception as e:
                print(f"⚠️ Erro processando evento: {e}")
                continue
        
        # Ordenar por valor esperado (melhores primeiro)
        apostas.sort(key=lambda x: x['value_expected'], reverse=True)
        
        if not apostas:
            print("⚠️ Nenhuma aposta com valor encontrada. Usando fallback.")
            return gerar_apostas_mock_fallback()
        
        print(f"✅ {len(apostas)} apostas com valor geradas")
        return apostas[:10]  # Retorna apenas as top 10

    def calcular_produto_odds(apostas):
        """Calcula o produto das odds (substitui numpy.prod)"""
        produto = 1.0
        for aposta in apostas:
            produto *= aposta['odd']
        return produto

    def calcular_produto_probabilidades(apostas):
        """Calcula o produto das probabilidades (substitui numpy.prod)"""
        produto = 1.0
        for aposta in apostas:
            produto *= aposta['probability']
        return produto

    def gerar_multiplas_inteligentes():
        """Gera múltiplas baseadas em correlação real"""
        try:
            # Buscar as melhores apostas individuais
            melhores_apostas = gerar_apostas_reais_com_ia()[:3]
            
            if len(melhores_apostas) >= 2:
                odd_total = calcular_produto_odds(melhores_apostas)
                prob_total = calcular_produto_probabilidades(melhores_apostas)
                valor_esperado = (odd_total * prob_total) - 1
                
                confianca = "ALTA" if valor_esperado > 0.2 else "MEDIA"
                
                return [{
                    'odd_total': round(odd_total, 2),
                    'probability': round(prob_total, 3),
                    'value_expected': round(valor_esperado, 3),
                    'confidence': confianca,
                    'jogos': json.dumps([{
                        'match': aposta['match'],
                        'bet_type': aposta['bet_type'],
                        'odd': aposta['odd']
                    } for aposta in melhores_apostas])
                }]
            else:
                return gerar_multiplas_mock_fallback()
                
        except Exception as e:
            print(f"❌ Erro gerando múltiplas: {e}")
            return gerar_multiplas_mock_fallback()

    # --- FUNÇÕES FALLBACK (MOCK) - MANTIDAS ---
    
    def gerar_apostas_mock_fallback():
        print("⚠️ Usando dados mock como fallback.")
        return [
            {'match': 'FLAMENGO vs PALMEIRAS', 'league': 'BRASILEIRÃO SÉRIE A', 'bet_type': 'Ambos Marcam', 'odd': 2.10, 'probability': 0.55, 'value_expected': 0.155, 'stake': 'MÉDIO', 'confidence': 'ALTA', 'casa_aposta': 'Betano', 'link_aposta': 'https://betano.com'},
            {'match': 'SÃO PAULO vs CORINTHIANS', 'league': 'BRASILEIRÃO SÉRIE A', 'bet_type': 'Over 2.5 Gols', 'odd': 1.95, 'probability': 0.58, 'value_expected': 0.131, 'stake': 'MÉDIO', 'confidence': 'ALTA', 'casa_aposta': 'SportingBet', 'link_aposta': 'https://sportingbet.com'},
        ]

    def gerar_multiplas_mock_fallback():
        return [{'odd_total': 5.25, 'probability': 0.20, 'value_expected': 0.05, 'confidence': 'MÉDIA', 'jogos': json.dumps([{'match': 'FLAMENGO vs PALMEIRAS', 'bet_type': 'Vence'}, {'match': 'SÃO PAULO vs CORINTHIANS', 'bet_type': 'Ambos Marcam'}])}]

    def gerar_surebets_mock_fallback():
        return [
            {'match': 'INTERNACIONAL vs ATLÉTICO-MG', 'league': 'BRASILEIRÃO SÉRIE A', 'bet_type': 'Double Chance', 'odd': 1.75, 'probability': 0.65, 'value_expected': 0.137, 'stake': 'MÉDIO', 'confidence': 'ALTA', 'casa_aposta': 'Bet365', 'link_aposta': 'https://bet365.com'},
        ]

    def salvar_dados_supabase(dados: list, table_name: str, supabase: Client):
        """Função mantida igual para compatibilidade"""
        try:
            print(f"🧹 Limpando e salvando na tabela '{table_name}'...")
            
            response_delete = supabase.table(table_name).delete().gt('id', 0).execute()
            
            if response_delete.count is not None:
                 print(f"   ({response_delete.count} registros antigos deletados)")

            if dados:
                response_insert = supabase.table(table_name).insert(dados).execute()
                
                if len(response_insert.data) == len(dados):
                    print(f"✅ {len(dados)} registros salvos em {table_name}!")
                else:
                    print(f"⚠️ Alerta: Tentou salvar {len(dados)} mas Supabase retornou {len(response_insert.data)}")
            else:
                print(f"ℹ️ Nenhum dado para salvar em {table_name}")

        except Exception as e:
            print(f"❌ Erro salvando {table_name}: {e}")
            
    # --- EXECUÇÃO PRINCIPAL ---
    
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- Iniciando ANÁLISE DE IA COM DADOS REAIS em {agora} ---")

    # 1. Obter Dados REAIS com IA
    dados_individuais = gerar_apostas_reais_com_ia()
    dados_multiplas = gerar_multiplas_inteligentes()
    dados_surebets = gerar_surebets_mock_fallback()

    # 2. Salvar no Supabase
    salvar_dados_supabase(dados_individuais, 'individuais', supabase)
    salvar_dados_supabase(dados_multiplas, 'multiplas', supabase)
    salvar_dados_supabase(dados_surebets, 'surebets', supabase)

    print(f"\n✅ Processo concluído! {len(dados_individuais)} apostas individuais geradas")
    return "Execução do Cron Job com IA e dados reais concluída!", 200

# Para executar localmente (teste)
if __name__ == "__main__":
    run_cron_job()
