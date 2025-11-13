import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Configurações
SUPABASE_URL = "https://kctzwwczcthjmdgvxuks.supabase.co"
SUPABASE_KEY = "SUA_CHAVE_REAL_SUPABASE"  # Substitua pela real!
ODDS_API_KEY = "ac044320ba772d0167f705db13cbd294"
FOOTBALL_DATA_KEY = "2a2017966e56443c9e63a8fa0bda2097"

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class FutebolIA:
    def __init__(self):
        self.modelo_1x2 = None
        self.modelo_btts = None
        self.modelo_over_under = None
        self.dados_historicos = []
        
    def buscar_partidas_ao_vivo(self):
        """Busca partidas em tempo real do football-data.org"""
        url = "https://api.football-data.org/v4/matches"
        headers = {'X-Auth-Token': FOOTBALL_DATA_KEY}
        
        # Buscar partidas de hoje
        hoje = datetime.now().strftime('%Y-%m-%d')
        params = {
            'dateFrom': hoje,
            'dateTo': hoje,
            'status': 'SCHEDULED,LIVE'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()['matches']
            else:
                print(f"Erro API Football: {response.status_code}")
                return []
        except Exception as e:
            print(f"Erro ao buscar partidas: {e}")
            return []
    
    def buscar_odds_reais(self):
        """Busca odds em tempo real da The Odds API"""
        url = "https://api.the-odds-api.com/v4/sports/soccer_brazil_campeonato/odds"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'eu',
            'markets': 'h2h,totals,btts',
            'oddsFormat': 'decimal'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro Odds API: {response.status_code}")
                return []
        except Exception as e:
            print(f"Erro ao buscar odds: {e}")
            return []
    
    def analisar_valor_odds(self, probabilidade_real, odds_disponiveis):
        """Calcula valor nas odds baseado na probabilidade real"""
        probabilidade_implícita = 1 / odds_disponiveis
        valor = probabilidade_real - probabilidade_implícita
        return valor * 100  # Retorna em porcentagem
    
    def prever_resultado_ia(self, partida):
        """Modelo de IA para prever resultados"""
        # Features para o modelo (dados históricos, forma, etc.)
        features = self.extrair_features_partida(partida)
        
        # Aqui viria o modelo treinado - por enquanto usamos lógica baseada em odds
        odds_casa = partida.get('odds_home', 2.0)
        odds_empate = partida.get('odds_draw', 3.0)
        odds_visitante = partida.get('odds_away', 3.5)
        
        # Probabilidades implícitas
        prob_casa = 1 / odds_casa
        prob_empate = 1 / odds_empate
        prob_visitante = 1 / odds_visitante
        
        # Ajustar pelo overround
        total_prob = prob_casa + prob_empate + prob_visitante
        prob_casa_ajustada = prob_casa / total_prob
        prob_empate_ajustada = prob_empate / total_prob
        prob_visitante_ajustada = prob_visitante / total_prob
        
        return {
            'casa': prob_casa_ajustada,
            'empate': prob_empate_ajustada,
            'visitante': prob_visitante_ajustada,
            'confianca': max(prob_casa_ajustada, prob_empate_ajustada, prob_visitante_ajustada)
        }
    
    def gerar_palpites_inteligentes(self):
        """Gera palpites com IA baseado em dados reais"""
        print("🔄 Buscando dados em tempo real...")
        
        # Buscar dados reais
        partidas = self.buscar_partidas_ao_vivo()
        odds_data = self.buscar_odds_reais()
        
        palpites = []
        
        for partida in partidas:
            try:
                # Informações básicas da partida
                home_team = partida['homeTeam']['name']
                away_team = partida['awayTeam']['name']
                championship = partida['competition']['name']
                match_time = partida['utcDate']
                
                # Encontrar odds correspondentes
                odds_partida = self.encontrar_odds_partida(odds_data, home_team, away_team)
                
                if odds_partida:
                    # Gerar previsão com IA
                    previsao = self.prever_resultado_ia(odds_partida)
                    
                    # Analisar valor nas odds
                    melhor_odd_casa = odds_partida.get('odds_home', 0)
                    valor_casa = self.analisar_valor_odds(previsao['casa'], melhor_odd_casa)
                    
                    # Determinar confiança
                    if previsao['confianca'] > 0.65:
                        confianca = "MUITO ALTA"
                    elif previsao['confianca'] > 0.55:
                        confianca = "ALTA"
                    elif previsao['confianca'] > 0.45:
                        confianca = "MEDIA"
                    else:
                        confianca = "BAIXA"
                    
                    palpite = {
                        'partida': f"{home_team} vs {away_team}",
                        'campeonato': championship,
                        'horario': match_time,
                        'previsao_ia': previsao,
                        'odds_casa': melhor_odd_casa,
                        'odds_empate': odds_partida.get('odds_draw', 0),
                        'odds_visitante': odds_partida.get('odds_away', 0),
                        'valor_aposta': valor_casa,
                        'confianca': confianca,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    palpites.append(palpite)
                    
            except Exception as e:
                print(f"Erro ao processar partida: {e}")
                continue
        
        return palpites
    
    def encontrar_odds_partida(self, odds_data, home_team, away_team):
        """Encontra odds correspondentes para uma partida"""
        for evento in odds_data:
            if (evento['home_team'].lower() in home_team.lower() or 
                home_team.lower() in evento['home_team'].lower()):
                return self.processar_odds_evento(evento)
        return None
    
    def processar_odds_evento(self, evento):
        """Processa as odds de um evento específico"""
        try:
            odds_resultado = {'odds_home': 0, 'odds_draw': 0, 'odds_away': 0}
            
            for bookmaker in evento['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == evento['home_team']:
                                odds_resultado['odds_home'] = outcome['price']
                            elif outcome['name'] == evento['away_team']:
                                odds_resultado['odds_away'] = outcome['price']
                            else:  # Empate
                                odds_resultado['odds_draw'] = outcome['price']
            
            return odds_resultado
        except:
            return None
    
    def salvar_palpites_supabase(self, palpites):
        """Salva os palpites no Supabase"""
        try:
            for palpite in palpites:
                data = {
                    'partida': palpite['partida'],
                    'campeonato': palpite['campeonato'],
                    'horario': palpite['horario'],
                    'previsao_casa': palpite['previsao_ia']['casa'],
                    'previsao_empate': palpite['previsao_ia']['empate'],
                    'previsao_visitante': palpite['previsao_ia']['visitante'],
                    'odds_casa': palpite['odds_casa'],
                    'odds_empate': palpite['odds_empate'],
                    'odds_visitante': palpite['odds_visitante'],
                    'valor_aposta': palpite['valor_aposta'],
                    'confianca': palpite['confianca'],
                    'criado_em': palpite['timestamp']
                }
                
                supabase.table('palpites').insert(data).execute()
            
            print(f"✅ {len(palpites)} palpites salvos no Supabase!")
            
        except Exception as e:
            print(f"❌ Erro ao salvar no Supabase: {e}")

def main():
    print("🤖 INICIANDO SISTEMA DE PALPITES COM IA...")
    
    # Inicializar IA
    ia_futebol = FutebolIA()
    
    # Gerar palpites
    palpites = ia_futebol.gerar_palpites_inteligentes()
    
    print(f"🎯 Gerados {len(palpites)} palpites com IA")
    
    # Salvar no banco de dados
    if palpites:
        ia_futebol.salvar_palpites_supabase(palpites)
        
        # Mostrar melhores palpites
        for i, palpite in enumerate(palpites[:5]):  # Top 5
            print(f"\n--- PALPITE {i+1} ---")
            print(f"🏆 {palpite['partida']}")
            print(f"📊 Confiança: {palpite['confianca']}")
            print(f"💰 Valor: {palpite['valor_aposta']:.1f}%")
            print(f"🎲 Odds: Casa {palpite['odds_casa']} | Empate {palpite['odds_empate']} | Fora {palpite['odds_visitante']}")
    else:
        print("❌ Nenhum palpite gerado - verifique as APIs")

if __name__ == "__main__":
    main()
