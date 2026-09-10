import urllib.request
import json
import urllib.parse


def buscar_preco(app_id):
    parametros = {"appids": app_id, "cc": "br", "l": "portuguese"}
    query = urllib.parse.urlencode(parametros)
    resposta = urllib.request.urlopen("https://store.steampowered.com/api/appdetails?" + query)
    conteudo_bruto = resposta.read()
    decodificado = conteudo_bruto.decode("utf-8")
    texto = json.loads(decodificado)

    jogo = texto[str(app_id)]
    dados = jogo.get("data")
    nome = dados.get("name")
    preco = dados.get("price_overview")
    if preco is None:
        print("Sem preço disponível ou o jogo é gratuíto.")
        return
    
    valor_final = preco.get("final")
    valor = valor_final / 100
    game = {"jogo": nome, "preco": valor}
    return game


def carregar_jogos_monitorados():
    try:
        with open("jogos_monitorados.json", "r") as arquivo:
            jogos_monitorados = json.load(arquivo)
    except FileNotFoundError:
        print("Arquivo de configuração não encontrado, usando lista vazia.")
        jogos_monitorados = []
    return jogos_monitorados


app_ids = carregar_jogos_monitorados()


def carregar_historico():
    try:
        with open("historico.json", "r") as arquivo:
            historico = json.load(arquivo)
    except FileNotFoundError:
        historico = []
    return historico


historico = carregar_historico()


def buscar_anterior(historico, nome_jogo):
    anterior = None
    for registro_salvo in historico:
        if registro_salvo["jogo"] == nome_jogo:
            anterior = registro_salvo
    return anterior


def comparar_precos(anterior, resultado):
    if anterior is not None and resultado["preco"] < anterior["preco"]:
        print(f"{resultado['jogo']} teve queda: R$ {anterior['preco']} → R$ {resultado['preco']}")
    elif anterior is not None and resultado["preco"] > anterior["preco"]:
        print(f"{resultado['jogo']} teve aumento: R$ {anterior['preco']} → R$ {resultado['preco']}")
    elif anterior is not None:
        print("Preço sem alteração.")


for app_id in app_ids:
    resultado = buscar_preco(app_id)
    if resultado is not None:
        anterior = buscar_anterior(historico, resultado["jogo"])
        print("Anterior encontrado: ", anterior)
        comparar_precos(anterior, resultado)
        historico.append(resultado)


def salvar_historico(historico):
    with open("historico.json", "w") as arquivo:
        json.dump(historico, arquivo)

salvar_historico(historico)