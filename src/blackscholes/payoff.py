import matplotlib.pyplot as plt



def payoff_com_premio(legs, S_range):
    """
    Args:
        legs: lista de dicionários com as pernas, ex:
            {"tipo": "ativo_adjacente", "premio": 100, "sentido": "C", "qtd": 1}
            {"tipo": "put", "strike": 100, "premio": 10, "sentido": "C", "qtd": 1}
            {"tipo": "call", "strike": 110, "premio": 10, "sentido": "V", "qtd": 1}
        S_range: lista de preços do ativo no vencimento (ex: range(70, 140, 5))

    Returns:
        payoff_dict: {S: payoff_total} para cada preço final
        custo_inicial: prêmio líquido (ΔP)
    """
    payoff_dict = {}
    custo_inicial = 0  # soma dos prêmios (Pc - Pp)

    # custo inicial líquido: somatório dos prêmios
    for leg in legs:
        qtd = leg.get("qtd", 1)
        premio = leg.get("premio", 0)
        if leg["tipo"] in ("call", "put"):
            if leg["sentido"] == "C":
                custo_inicial -= premio * qtd   # pagou prêmio
            elif leg["sentido"] == "V":
                custo_inicial += premio * qtd   # recebeu prêmio

    # payoff em cada preço S no vencimento
    for S in S_range:
        payoff_total = 0

        for leg in legs:
            qtd = leg.get("qtd", 1)
            tipo = leg["tipo"]
            sentido = leg["sentido"]

            if tipo == "ativo_adjacente":
                S0 = leg["premio"]
                payoff_leg = (S - S0) * qtd
                if sentido == "V":
                    payoff_leg = -payoff_leg

            elif tipo == "put":
                strike = leg["strike"]
                payoff_leg = max(strike - S, 0) * qtd
                if sentido == "V":  # vendido
                    payoff_leg = -payoff_leg

            elif tipo == "call":
                strike = leg["strike"]
                payoff_leg = -max(S - strike, 0) * qtd
                if sentido == "C":  # comprado
                    payoff_leg = -payoff_leg

            else:
                raise ValueError("Tipo deve ser 'ativo_adjacente', 'put' ou 'call'")

            payoff_total += payoff_leg

        # soma ΔP como constante
        payoff_dict[S] = payoff_total + custo_inicial

    return payoff_dict, custo_inicial


def calcular_break_even(payoff_dict):
    """
    Calcula os pontos de break-even (preço onde payoff cruza zero).

    Args:
        payoff_dict (dict): Resultado de payoff_com_premio

    Returns:
        list[float]: Lista de preços de break-even
    """
    prices = list(payoff_dict.keys())
    payoffs = list(payoff_dict.values())
    break_evens = []

    for i in range(1, len(prices)):
        # Verifica se houve cruzamento de sinal
        if payoffs[i-1] == 0:
            break_evens.append(prices[i-1])
        elif payoffs[i-1] * payoffs[i] < 0:
            # Interpolação linear aproximada
            p1, p2 = prices[i-1], prices[i]
            y1, y2 = payoffs[i-1], payoffs[i]
            be = p1 - y1 * (p2 - p1) / (y2 - y1)
            break_evens.append(round(be, 2))

    return break_evens

def identificar_estrutura(legs):
    """
    Identifica estruturas de opções clássicas com base nos legs fornecidos.

    Args:
        legs (list[dict]): Cada leg contém:
            - tipo: "call" ou "put"
            - strike: preço de exercício
            - sentido: "C" (compra) ou "V" (venda)

    Returns:
        str: Nome da estrutura ou "Estrutura não reconhecida"
    """

    calls = [l for l in legs if l["tipo"] == "call"]
    puts = [l for l in legs if l["tipo"] == "put"]

    n_calls = len(calls)
    n_puts = len(puts)

    # ---------- STRADDLE ----------
    if n_calls == 1 and n_puts == 1 and calls[0]["strike"] == puts[0]["strike"]:
        return "Straddle"

    # ---------- STRANGLE ----------
    if n_calls == 1 and n_puts == 1 and calls[0]["strike"] != puts[0]["strike"]:
        return "Strangle"

    # ---------- BULL/BEAR CALL SPREAD ----------
    if n_calls == 2 and n_puts == 0:
        sorted_calls = sorted(calls, key=lambda x: x["strike"])
        low, high = sorted_calls[0], sorted_calls[1]
        if low["sentido"] == "C" and high["sentido"] == "V":
            return "Bull Call Spread"
        elif low["sentido"] == "V" and high["sentido"] == "C":
            return "Bear Call Spread"

    # ---------- BULL/BEAR PUT SPREAD ----------
    if n_puts == 2 and n_calls == 0:
        sorted_puts = sorted(puts, key=lambda x: x["strike"])
        low, high = sorted_puts[0], sorted_puts[1]
        if low["sentido"] == "V" and high["sentido"] == "C":
            return "Bull Put Spread"
        elif low["sentido"] == "C" and high["sentido"] == "V":
            return "Bear Put Spread"

    # ---------- BUTTERFLY (CALL ou PUT) ----------
    if n_calls == 3 and n_puts == 0:
        strikes = sorted([c["strike"] for c in calls])
        if strikes[2] - strikes[1] == strikes[1] - strikes[0]:
            return "Butterfly (Call)"
    if n_puts == 3 and n_calls == 0:
        strikes = sorted([p["strike"] for p in puts])
        if strikes[2] - strikes[1] == strikes[1] - strikes[0]:
            return "Butterfly (Put)"

    # ---------- IRON BUTTERFLY ----------
    if n_calls == 2 and n_puts == 2:
        strikes_calls = sorted([c["strike"] for c in calls])
        strikes_puts = sorted([p["strike"] for p in puts])
        if strikes_calls[0] == strikes_puts[1] and strikes_calls[1] == strikes_puts[0]:
            return "Iron Butterfly"

    # ---------- IRON CONDOR ----------
    if n_calls == 2 and n_puts == 2:
        strikes_calls = sorted([c["strike"] for c in calls])
        strikes_puts = sorted([p["strike"] for p in puts])
        # Iron condor: put spread + call spread (simétricos ou não)
        if strikes_calls[0] > strikes_puts[1]:
            return "Iron Condor"

    return "Estrutura não reconhecida"

def calcular_estrutura_api(legs, S_range):
    """
    Gera saída completa para API com nome da estrutura,
    payoff, break-evens e custo inicial.
    """
    nome = identificar_estrutura(legs)

    payoff_dict, custo_inicial = payoff_com_premio(legs, S_range)
    break_evens = calcular_break_even(payoff_dict)

    return {
        "estrutura": nome,
        "custo_inicial": round(custo_inicial, 2),
        "payoff": {float(k): round(v, 2) for k, v in payoff_dict.items()},
        "break_evens": break_evens,
    }


def plot_payoff(payoff_dict, break_evens=None, titulo="Payoff da Estrutura"):
    """
    Plota gráfico de payoff líquido.    

    Args:
        payoff_dict (dict): Resultado de payoff_com_premio
        break_evens (list): Pontos de break-even para destacar
        titulo (str): Título do gráfico
    """
    prices = list(payoff_dict.keys())
    payoffs = list(payoff_dict.values())

    plt.figure(figsize=(10, 5))
    plt.plot(prices, payoffs, label="Payoff", color="blue", linewidth=2)
    plt.axhline(0, color="black", linewidth=1)  # linha de zero

    # Marcar break-even se houver
    if break_evens:
        for be in break_evens:
            plt.axvline(be, color="red", linestyle="--", linewidth=1)
            plt.text(be, 0, f"{be}", color="red", ha="center", va="bottom")

    plt.title(titulo)
    plt.xlabel("Preço do Ativo no Vencimento")
    plt.ylabel("Lucro / Prejuízo")
    plt.grid(True)
    plt.legend()
    plt.show()
