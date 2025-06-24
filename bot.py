import requests
import time
from datetime import datetime

# === CONFIGURAÇÃO DO TELEGRAM ===
token = 'SEU_TOKEN_AQUI'
chat_id = 'SEU_CHAT_ID_AQUI'
url_telegram = f'https://api.telegram.org/bot{token}/sendMessage'

# === FUNÇÕES DE ANÁLISE ===
def calcular_rsi(precos, periodo=14):
    if len(precos) <= periodo:
        return 50  # Valor neutro para evitar erro

    ganhos, perdas = [], []
    for i in range(1, periodo + 1):
        dif = precos[i] - precos[i - 1]
        ganhos.append(max(dif, 0))
        perdas.append(abs(min(dif, 0)))
    media_ganho = sum(ganhos) / periodo
    media_perda = sum(perdas) / periodo
    for i in range(periodo + 1, len(precos)):
        dif = precos[i] - precos[i - 1]
        ganho = max(dif, 0)
        perda = abs(min(dif, 0))
        media_ganho = (media_ganho * (periodo - 1) + ganho) / periodo
        media_perda = (media_perda * (periodo - 1) + perda) / periodo
    rs = media_ganho / media_perda if media_perda != 0 else 100
    return round(100 - (100 / (1 + rs)), 2)

def calcular_macd(precos):
    if len(precos) < 26:
        return 0  # MACD neutro se não houver dados suficientes

    def ema(lista, p):
        k = 2 / (p + 1)
        ema = lista[0]
        for preco in lista[1:]:
            ema = (preco - ema) * k + ema
        return ema
    ema12 = ema(precos[-26:], 12)
    ema26 = ema(precos[-26:], 26)
    return round(ema12 - ema26, 4)

def tipo_candle(c):
    try:
        a, m, mi, f = float(c[1]), float(c[2]), float(c[3]), float(c[4])
        corpo = abs(f - a)
        pavio_sup = m - max(a, f)
        pavio_inf = min(a, f) - mi
        if corpo > pavio_sup and corpo > pavio_inf:
            return "Candle de força de alta" if f > a else "Candle de força de baixa"
        elif pavio_inf > corpo * 1.5:
            return "Martelo (absorção compradora)"
        elif pavio_sup > corpo * 1.5:
            return "Enforcado (pressão vendedora)"
        else:
            return "Candle neutro"
    except:
        return "Candle inválido"

# === LOOP INFINITO ===
while True:
    try:
        agora = datetime.now().strftime("%H:%M:%S")

        # === M5 ===
        dados_5m = requests.get('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=100').json()
        closes5m = [float(c[4]) for c in dados_5m]
        vols5m = [float(c[5]) for c in dados_5m]
        candle5m = dados_5m[-1]
        rsi5 = calcular_rsi(closes5m)
        macd5 = calcular_macd(closes5m)
        estrutura5 = tipo_candle(candle5m)

        if rsi5 < 30 and macd5 > 0 and "alta" in estrutura5:
            msg = f"🦈 COMPRA INSTITUCIONAL [M5]\n⏰ {agora}\nRSI: {rsi5} | MACD: {macd5}\n{estrutura5}"
            print(msg)
            requests.post(url_telegram, data={'chat_id': chat_id, 'text': f"🚨 {msg}"})

        elif rsi5 > 70 and macd5 < 0 and "baixa" in estrutura5:
            msg = f"🦈 VENDA INSTITUCIONAL [M5]\n⏰ {agora}\nRSI: {rsi5} | MACD: {macd5}\n{estrutura5}"
            print(msg)
            requests.post(url_telegram, data={'chat_id': chat_id, 'text': f"🚨 {msg}"})
        else:
            print(f"[{agora}] ⏸️ M5 sem sinal | RSI={rsi5} | MACD={macd5} | {estrutura5}")

        # === M1 ===
        dados_1m = requests.get('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100').json()
        closes1m = [float(c[4]) for c in dados_1m]
        vols1m = [float(c[5]) for c in dados_1m]
        candle1m = dados_1m[-1]
        rsi1 = calcular_rsi(closes1m)
        macd1 = calcular_macd(closes1m)
        estrutura1 = tipo_candle(candle1m)

        if rsi1 < 40 and macd1 > -5 and "alta" in estrutura1:
            msg = f"🐟 COMPRA LEVE [M1]\n⏰ {agora}\nRSI: {rsi1} | MACD: {macd1}\n{estrutura1}"
            print(msg)
            requests.post(url_telegram, data={'chat_id': chat_id, 'text': f"⚠️ {msg}"})

        elif rsi1 > 60 and macd1 < 0 and "baixa" in estrutura1:
            msg = f"🐟 VENDA LEVE [M1]\n⏰ {agora}\nRSI: {rsi1} | MACD: {macd1}\n{estrutura1}"
            print(msg)
            requests.post(url_telegram, data={'chat_id': chat_id, 'text': f"⚠️ {msg}"})
        else:
            print(f"[{agora}] ⏸️ M1 sem sinal | RSI={rsi1} | MACD={macd1} | {estrutura1}")

    except Exception as e:
        print("❌ Erro detectado:", e)

    time.sleep(60)
