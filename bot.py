import requests, time
from datetime import datetime

# === TELEGRAM CONFIG ===
token = '8185549719:AAEJyWpN3VZDq5AQ01cstllurqDw55s7h3A'
chat_id = '7594105835'
base_url = f'https://api.telegram.org/bot{token}'
offset = 0

# === FUNÇÕES TÉCNICAS ===
def get_klines():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=100"
        r = requests.get(url)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print("❌ Erro ao obter dados da Binance:", e)
        return []

def calcular_ema(precos, periodo):
    k = 2 / (periodo + 1)
    ema = precos[0]
    for p in precos[1:]:
        ema = (p - ema) * k + ema
    return ema

def tendencia(ema9, ema21):
    if abs(ema9 - ema21) < 0.0003: return "🔄 LATERAL"
    return "📈 ALTA" if ema9 > ema21 else "📉 BAIXA"

def calcular_rsi(precos, periodo=14):
    if len(precos) <= periodo + 1:
        return 50
    ganhos = [max(precos[i] - precos[i-1], 0) for i in range(1, periodo+1)]
    perdas = [abs(min(precos[i] - precos[i-1], 0)) for i in range(1, periodo+1)]
    media_ganho = sum(ganhos) / periodo
    media_perda = sum(perdas) / periodo
    for i in range(periodo+1, len(precos)):
        dif = precos[i] - precos[i-1]
        media_ganho = (media_ganho * (periodo - 1) + max(dif, 0)) / periodo
        media_perda = (media_perda * (periodo - 1) + abs(min(dif, 0))) / periodo
    if media_perda == 0: return 100
    rs = media_ganho / media_perda
    return round(100 - (100 / (1 + rs)), 2)

def calcular_macd(precos):
    if len(precos) < 26:
        return 0
    def ema(p, l):
        k = 2 / (l + 1)
        e = p[0]
        for x in p[1:]:
            e = (x - e) * k + e
        return e
    return round(ema(precos[-26:], 12) - ema(precos[-26:], 26), 4)

def tipo_candle(c):
    if len(c) < 5:
        return "⚠️ Candle inválido"
    try:
        a, h, l, f = map(float, c[1:5])
        corpo = abs(f - a)
        pavio_sup = h - max(f, a)
        pavio_inf = min(f, a) - l
        if corpo > pavio_sup and corpo > pavio_inf:
            return "🔥 Alta" if f > a else "❄️ Baixa"
        elif pavio_inf > corpo * 1.5: return "🟢 Martelo"
        elif pavio_sup > corpo * 1.5: return "🔴 Enforcado"
        else: return "⚪ Neutro"
    except:
        return "⚠️ Erro ao ler candle"

def enviar(txt):
    print(txt)
    try:
        requests.post(f"{base_url}/sendMessage", data={
            'chat_id': chat_id,
            'text': txt,
            'parse_mode': 'Markdown'
        })
    except:
        print("❌ Erro ao enviar mensagem pro Telegram")

def gerar_resumo():
    dados = get_klines()
    if not dados or len(dados) < 30:
        enviar("⚠️ Dados insuficientes da Binance. Tentaremos novamente em breve.")
        return

    try:
        closes = [float(c[4]) for c in dados]
        vols = [float(c[5]) for c in dados]
        preco = closes[-1]
        hora = datetime.now().strftime('%H:%M:%S')

        ema9 = calcular_ema(closes[-10:], 9)
        ema21 = calcular_ema(closes[-25:], 21)
        tend = tendencia(ema9, ema21)
        rsi = calcular_rsi(closes)
        macd = calcular_macd(closes)
        vol_med = sum(vols[-10:]) / 10
        vol = vols[-1]
        cndl = tipo_candle(dados[-1])

        if rsi < 30 and macd > 0:
            leitura = "Possível reversão em formação"
        elif tend == "📉 BAIXA" and vol > vol_med * 1.5:
            leitura = "Pressão vendedora acentuada"
        elif tend == "📈 ALTA" and rsi > 70:
            leitura = "Mercado sobrecomprado — cautela"
        else:
            leitura = "Mercado neutro ou aguardando decisão"

        msg = (
            f"*📍 BTCUSDT – RESUMO M5*\n"
            f"💰 Preço: `{preco:.2f}`\n"
            f"📊 Tendência: {tend}\n"
            f"📈 RSI: *{rsi}*\n"
            f"🧭 MACD: `{macd}`\n"
            f"🕯️ Candle: {cndl}\n"
            f"📦 Volume: `{vol:.2f}` (média: {vol_med:.2f})\n"
            f"🧠 Leitura: _{leitura}_\n"
            f"🕓 {hora}"
        )
        enviar(msg)
    except Exception as e:
        print("❌ Erro ao gerar resumo:", e)

def processar_comando(txt):
    if txt == '/resumo':
        gerar_resumo()
    else:
        enviar("🤖 Comando não reconhecido. Use /resumo")

def checar_msgs():
    global offset
    try:
        r = requests.get(f"{base_url}/getUpdates?offset={offset}").json()
        if "result" in r:
            for msg in r["result"]:
                offset = msg["update_id"] + 1
                if "message" in msg and "text" in msg["message"]:
                    texto = msg["message"]["text"].strip().lower()
                    chat = msg["message"]["chat"]["id"]
                    if str(chat) == chat_id:
                        processar_comando(texto)
    except Exception as e:
        print("❌ Erro ao verificar mensagens:", e)

# === LOOP INFINITO ===
while True:
    checar_msgs()
    time.sleep(3)
