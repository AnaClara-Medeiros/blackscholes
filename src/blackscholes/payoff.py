import matplotlib.pyplot as plt

def payoff_com_premio(legs, S_range):
    """
    Calcula o payoff líquido de uma estrutura de opções usando prêmios já conhecidos.

    Args:
        legs (list[dict]): Lista de dicts com os campos:
            - tipo: "call" ou "put"
            - strike: preço de exercício
            - premio: valor do prêmio (positivo)
            - sentido: "C" para compra (paga prêmio), "V" para venda (recebe prêmio)
            - qtd (opcional): quantidade de contratos (default = 1)
        S_range (list ou np.array): preços simulados do ativo no vencimento

    Returns:
        dict: {preço_subjacente: payoff_liquido}
    """

    # Cálculo do custo inicial da estrutura
    custo_inicial = 0
    for leg in legs:
        premio = leg["premio"]
        qtd = leg.get("qtd", 1)  # default 1 se não informado
        sentido = leg["sentido"]

        if sentido == "C":  # Compra = paga prêmio
            custo_inicial += premio * qtd
        elif sentido == "V":  # Venda = recebe prêmio
            custo_inicial -= premio * qtd
        else:
            raise ValueError("Sentido deve ser 'C' (compra) ou 'V' (venda)")

    # Calcular payoff líquido em cada ponto do S_range
    payoff_dict = {}

    for S_final in S_range:
        payoff_total = 0
        for leg in legs:
            tipo = leg["tipo"]
            strike = leg["strike"]
            qtd = leg.get("qtd", 1)
            sentido = leg["sentido"]

            # Payoff bruto por tipo
            if tipo == "call":
                payoff_leg = max(S_final - strike, 0)
            elif tipo == "put":
                payoff_leg = max(strike - S_final, 0)
            else:
                raise ValueError("Tipo deve ser 'call' ou 'put'")

            # Multiplicar pela quantidade
            payoff_leg *= qtd

            # Se for venda, inverte o sinal
            if sentido == "V":
                payoff_leg = -payoff_leg

            payoff_total += payoff_leg

        # Lucro líquido = payoff bruto - custo inicial
        payoff_dict[S_final] = payoff_total - custo_inicial

    return payoff_dict



def payoff_com_premio_new(legs, S_range):
    """
    Calcula o payoff líquido de uma estrutura de opções usando prêmios já conhecidos.
    Agora inclui também o ativo adjacente tratado como um leg.
    """
    payoff_dict = {}
    custo_inicial = 0

    # custo inicial = prêmios pagos/recebidos (opções + ativo)
    for leg in legs:
        qtd = leg.get("qtd", 1)
        sentido = leg["sentido"]

        if leg["tipo"] in ("call", "put"):
            premio = leg["premio"]
            if sentido == "C":
                custo_inicial += premio * qtd
            elif sentido == "V":
                custo_inicial -= premio * qtd

        elif leg["tipo"] == "ativo":
            # ativo pode ter prêmio inicial (se existir custo de carregar, ex: ajuste futuro)
            premio = leg.get("premio", 0)
            if sentido == "C":
                custo_inicial += premio * qtd
            elif sentido == "V":
                custo_inicial -= premio * qtd

    # payoff para cada preço final
    for S_final in S_range:
        payoff_total = 0

        for leg in legs:
            qtd = leg.get("qtd", 1)
            sentido = leg["sentido"]

            if leg["tipo"] == "call":
                payoff_leg = max(S_final - leg["strike"], 0) * qtd
                if sentido == "V":
                    payoff_leg = -payoff_leg

            elif leg["tipo"] == "put":
                payoff_leg = max(leg["strike"] - S_final, 0) * qtd
                if sentido == "V":
                    payoff_leg = -payoff_leg

            elif leg["tipo"] == "ativo":
                S0 = leg["ativo_adjacente"]
                payoff_leg = (S_final - S0) * qtd
                if sentido == "V":
                    payoff_leg = -payoff_leg

            else:
                raise ValueError("Tipo deve ser 'call', 'put' ou 'ativo'")

            payoff_total += payoff_leg

        payoff_dict[S_final] = payoff_total - custo_inicial

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

    payoff_dict, custo_inicial = payoff_com_premio_new(legs, S_range)
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
