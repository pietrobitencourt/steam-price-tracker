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

app_ids = [413150, 730, 570]

try:
    with open("historico.json", "r") as arquivo:
        historico = json.load(arquivo)
except FileNotFoundError:
    historico = []

for app_id in app_ids:
    resultado = buscar_preco(app_id)
    if resultado is not None:
        anterior = None
        for registro_salvo in historico:
            if registro_salvo["jogo"] == resultado["jogo"]:
                anterior = registro_salvo
        print("Anterior encontrado: ", anterior)
        if anterior is not None and resultado["preco"] < anterior["preco"]:
            print(f"{resultado['jogo']} teve queda: R$ {anterior['preco']} → R$ {resultado['preco']}")
        elif anterior is not None and resultado["preco"] > anterior["preco"]:
            print(f"{resultado['jogo']} teve aumento: R$ {anterior['preco']} → R$ {resultado['preco']}")
        elif anterior is not None:
            print("Preço sem alteração.")


        historico.append(resultado)


with open("historico.json", "w") as arquivo:
    json.dump(historico, arquivo)