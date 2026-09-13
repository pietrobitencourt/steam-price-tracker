import urllib.request
import json
import urllib.parse
import logging
import os


logging.basicConfig(
    filename="radar.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def buscar_preco(app_id):
    parametros_precos = {"appids": app_id, "cc": "br", "l": "portuguese"}
    query = urllib.parse.urlencode(parametros_precos)
    resposta = urllib.request.urlopen("https://store.steampowered.com/api/appdetails?" + query)
    conteudo_bruto = resposta.read()
    decodificado = conteudo_bruto.decode("utf-8")
    texto = json.loads(decodificado)

    jogo = texto[str(app_id)]
    dados = jogo.get("data")
    nome = dados.get("name")
    preco = dados.get("price_overview")
    if preco is None:
        logging.warning("Sem preço disponível ou o jogo é gratuíto.")
        return
    
    valor_final = preco.get("final")
    valor = valor_final / 100
    game = {"jogo": nome, "preco": valor}
    return game


def buscar_nome_jogo(app_id):
    parametros_precos = {"appids": app_id, "cc": "br", "l": "portuguese"}
    query = urllib.parse.urlencode(parametros_precos)
    resposta = urllib.request.urlopen("https://store.steampowered.com/api/appdetails?" + query)
    conteudo_bruto = resposta.read()
    decodificado = conteudo_bruto.decode("utf-8")
    texto = json.loads(decodificado)

    jogo = texto[str(app_id)]
    dados = jogo.get("data")
    if dados is None:
        return None
    nome = dados.get("name")
    return nome


def carregar_jogos_monitorados():
    try:
        with open("jogos_monitorados.json", "r") as arquivo:
            jogos_monitorados = json.load(arquivo)
    except FileNotFoundError:
        logging.warning("Arquivo de configuração não encontrado, usando lista vazia.")
        jogos_monitorados = []
    return jogos_monitorados


def carregar_historico():
    try:
        with open("historico.json", "r") as arquivo:
            historico = json.load(arquivo)
    except FileNotFoundError:
        historico = {}
    return historico


def buscar_anterior(historico, nome_jogo):
    lista_precos = historico.get(nome_jogo, [])
    if lista_precos:
        return lista_precos[-1]
    return None


def buscar_menor_preco(historico, nome_jogo):
    lista_precos = historico.get(nome_jogo, [])
    if lista_precos:
        return min(lista_precos)
    return None


def carregar_config_telegram():
    with open("config_telegram.json", "r") as arquivo:
        config_telegram = json.load(arquivo)
    return config_telegram


def enviar_notificacao(mensagem):
    codigo = carregar_config_telegram()
    token = codigo["token"]
    chat_id = codigo["chat_id"]
    url_base = "https://api.telegram.org/bot" + token + "/sendMessage?"
    parametros_mensagem = {"chat_id": chat_id, "text": mensagem}
    query_mensagem = urllib.parse.urlencode(parametros_mensagem)
    url_final = url_base + query_mensagem
    urllib.request.urlopen(url_final)


def comparar_precos(anterior, resultado, menor_preco):
    if anterior is not None and resultado["preco"] < anterior:
       enviar_notificacao(f"{resultado['jogo']} teve queda: R$ {anterior} → R$ {resultado['preco']} (menor preço já visto: R$ {menor_preco})")
       logging.info(f"{resultado['jogo']} teve queda: R$ {anterior} → R$ {resultado['preco']} (menor preço já visto: R$ {menor_preco})")
    elif anterior is not None and resultado["preco"] > anterior:
       enviar_notificacao(f"{resultado['jogo']} teve aumento: R$ {anterior} → R$ {resultado['preco']}")
       logging.info(f"{resultado['jogo']} teve aumento: R$ {anterior} → R$ {resultado['preco']}")
    elif anterior is not None:
        logging.info(f"Preço de {resultado['jogo']} sem alteração. Preço atual: R$ {resultado['preco']}")


def salvar_historico(historico):
    with open("historico.json", "w") as arquivo:
        json.dump(historico, arquivo)


def rodar_varredura(app_ids, historico):
    for jogo_monitorado in app_ids:
        app_id = jogo_monitorado["app_id"]
        resultado = buscar_preco(app_id)
        if resultado is not None:
            print(f"{resultado['jogo']}: R$ {resultado['preco']}")
            anterior = buscar_anterior(historico, resultado["jogo"])
            menor_preco = buscar_menor_preco(historico, resultado["jogo"])
            logging.info(f"Anterior encontrado: {anterior}")
            logging.info(f"Menor preço já visto: {menor_preco}")
            comparar_precos(anterior, resultado, menor_preco)
            if resultado["jogo"] not in historico:
                historico[resultado["jogo"]] = []
            historico[resultado["jogo"]].append(resultado["preco"])

    salvar_historico(historico)


def salvar_jogos_monitorados(app_ids):
    with open("jogos_monitorados.json", "w") as arquivo:
        json.dump(app_ids, arquivo)


app_ids = carregar_jogos_monitorados()
historico = carregar_historico()

if os.environ.get("GITHUB_ACTIONS"):
    rodar_varredura(app_ids, historico)
else:
    while True:
        print("=====Steam Price Tracker=====")
        escolha = input("[1] - Ver preços\n[2] - Adicionar jogo\n[3] - Remover jogo\n[4] - Listar jogos monitorados\n[5] - Ver histórico de um jogo\n[6] - Sair\nEscolha uma opção: ").strip()

        if escolha == "1":
            rodar_varredura(app_ids, historico)
            print("Varredura concluída.")
        elif escolha == "2":
            try:
                adicionar_app_id = int(input("Digite o app_id que você quer adicionar: "))
                nome_encontrado = buscar_nome_jogo(adicionar_app_id)
                if nome_encontrado is not None:
                    app_ids.append({"app_id": adicionar_app_id, "nome": nome_encontrado})
                    salvar_jogos_monitorados(app_ids)
                    print(f"{nome_encontrado} adicionado com sucesso!")
                else:
                    print("Não foi possível encontrar esse app_id.")
            except ValueError:
                print("App_Id inválido!")
        elif escolha == "3":
            try:
                remover_jogo = int(input("Digite o app_id que você quer remover: "))
                encontrado = None
                for jogo in app_ids:
                    if jogo["app_id"] == remover_jogo:
                        encontrado = jogo
                if encontrado is not None:
                    app_ids.remove(encontrado)
                    salvar_jogos_monitorados(app_ids)
                    print("Jogo removido com sucesso!")
                else:
                    print("O app_id não foi encontrado em sua lista.")
            except ValueError:
                print("App_Id inválido!")
        elif escolha == "4":
            if not app_ids:
                print("Nenhum jogo monitorado ainda.")
            else:
                for jogo in app_ids:
                    print(f"{jogo['app_id']} - {jogo['nome']}")
        elif escolha == "5":
            nome_jogo = input("Digite o nome do jogo que você quer ver o histórico: ")
            lista_precos = historico.get(nome_jogo, [])
            if lista_precos:
                print(lista_precos)
            else:
                print("Não há histórico para esse nome.")
        elif escolha == "6":
            print("Saindo...")
            break
        else:
            print("Opção inválida")