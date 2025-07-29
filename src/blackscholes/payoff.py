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
    calls = [l for l in legs if l["tipo"] == "call"]
    puts = [l for l in legs if l["tipo"] == "put"]
    compras = [l for l in legs if l["sentido"] == "C"]
    vendas = [l for l in legs if l["sentido"] == "V"]

    n_calls = len(calls)
    n_puts = len(puts)
    n_compras = len(compras)
    n_vendas = len(vendas)

    # Exemplo: Butterfly clássica
    if n_calls == 3 and n_puts == 0:
        strikes = sorted([l["strike"] for l in calls])
        if strikes[2] - strikes[1] == strikes[1] - strikes[0]:
            return "Butterfly (Call)"

    # Exemplo: Straddle
    if n_calls == 1 and n_puts == 1 and all(l["strike"] == calls[0]["strike"] for l in puts):
        return "Straddle"

    # Exemplo: Iron Condor
    if n_calls == 2 and n_puts == 2:
        strikes_calls = sorted([l["strike"] for l in calls])
        strikes_puts = sorted([l["strike"] for l in puts])
        if strikes_calls[1] - strikes_calls[0] == strikes_puts[1] - strikes_puts[0]:
            return "Iron Condor"

    # Exemplo: Strangle
    if n_calls == 1 and n_puts == 1 and calls[0]["strike"] != puts[0]["strike"]:
        return "Strangle"

    return "Estrutura não reconhecida"



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
