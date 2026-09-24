import urllib.request
import json
import urllib.parse
import logging
import os
import time


logging.basicConfig(
    filename="radar.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def buscar_preco(app_id):
    """
    Busca o preço atual de um jogo na Steam, dado seu app_id.

    Usa a API pública appdetails da Steam. Só devolve um resultado
    quando o jogo tem preço de fato (não é gratuito e não está
    indisponível/sem dados) — nesses casos, devolve None.

    Use esta função quando precisar do preço para comparação/histórico.
    Se só precisar confirmar que um app_id existe e pegar o nome do
    jogo (mesmo sem preço, como jogos grátis), use buscar_nome_jogo().
    """

    parametros_precos = {"appids": app_id, "cc": "br", "l": "portuguese"}
    query = urllib.parse.urlencode(parametros_precos)
    resposta = urllib.request.urlopen("https://store.steampowered.com/api/appdetails?" + query)
    conteudo_bruto = resposta.read()
    decodificado = conteudo_bruto.decode("utf-8")
    texto = json.loads(decodificado)

    jogo = texto.get(str(app_id), None)
    if jogo is None:
        logging.warning(f"Não foi possível obter dados da Steam para o app_id {app_id}.")
        return
    
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
    """
    Busca apenas o nome de um jogo na Steam, dado seu app_id.

    Diferente de buscar_preco(), não exige que o jogo tenha preço —
    funciona também para jogos grátis ou sem price_overview. Só
    devolve None se o app_id não existir na Steam ou a resposta
    vier sem dados.

    Use esta função para validar/nomear um app_id ao adicioná-lo à
    lista de jogos monitorados (menu ou comandos do Telegram).
    """

    parametros_precos = {"appids": app_id, "cc": "br", "l": "portuguese"}
    query = urllib.parse.urlencode(parametros_precos)
    resposta = urllib.request.urlopen("https://store.steampowered.com/api/appdetails?" + query)
    conteudo_bruto = resposta.read()
    decodificado = conteudo_bruto.decode("utf-8")
    texto = json.loads(decodificado)

    jogo = texto.get(str(app_id), None)
    if jogo is None:
        return None
    dados = jogo.get("data")
    if dados is None:
        return None
    nome = dados.get("name")
    return nome


def carregar_jogos_monitorados():
    """
    Lê a lista de jogos monitorados de jogos_monitorados.json.

    Cada item é um dicionário {"app_id": ..., "nome": ...}. Se o
    arquivo ainda não existir (primeira execução), devolve lista vazia.
    """
    try:
        with open("jogos_monitorados.json", "r") as arquivo:
            jogos_monitorados = json.load(arquivo)
    except FileNotFoundError:
        logging.warning("Arquivo de configuração não encontrado, usando lista vazia.")
        jogos_monitorados = []
    return jogos_monitorados


def carregar_historico():
    """
    Lê o histórico de preços de historico.json.

    Formato: {"Nome do Jogo": [preco1, preco2, ...]}, com um preço
    por execução em que o jogo teve preço disponível. Se o arquivo
    ainda não existir, devolve dicionário vazio.
    """
    try:
        with open("historico.json", "r") as arquivo:
            historico = json.load(arquivo)
    except FileNotFoundError:
        historico = {}
    return historico


def buscar_anterior(historico, nome_jogo):
    """
    Devolve o último preço registrado de um jogo no histórico.

    É o preço da execução mais recente antes da atual. Devolve None
    se esse jogo ainda não tiver nenhum registro salvo.
    """
    lista_precos = historico.get(nome_jogo, [])
    if lista_precos:
        return lista_precos[-1]
    return None


def buscar_menor_preco(historico, nome_jogo):
    """
    Devolve o menor preço já registrado de um jogo no histórico.

    Percorre todo o histórico daquele jogo (não só o último), útil
    para saber se uma queda atual representa o melhor preço de sempre.
    Devolve None se não houver nenhum registro salvo.
    """
    lista_precos = historico.get(nome_jogo, [])
    if lista_precos:
        return min(lista_precos)
    return None


def carregar_config_telegram():
    """
    Lê o token do bot e o chat_id de config_telegram.json.

    Esse arquivo é local e nunca é versionado (está no .gitignore),
    pois contém credenciais sensíveis.
    """
    with open("config_telegram.json", "r") as arquivo:
        config_telegram = json.load(arquivo)
    return config_telegram


def enviar_notificacao(mensagem):
    """
    Envia uma mensagem de texto para o Telegram via sendMessage.

    Usa as credenciais de carregar_config_telegram(). Não trata o
    conteúdo da resposta — só dispara o envio.
    """
    codigo = carregar_config_telegram()
    token = codigo["token"]
    chat_id = codigo["chat_id"]
    url_base = "https://api.telegram.org/bot" + token + "/sendMessage?"
    parametros_mensagem = {"chat_id": chat_id, "text": mensagem}
    query_mensagem = urllib.parse.urlencode(parametros_mensagem)
    url_final = url_base + query_mensagem
    urllib.request.urlopen(url_final)


def comparar_precos(anterior, resultado, menor_preco):
    """
    Compara o preço atual com o último registrado e notifica.

    Só envia notificação no Telegram em caso de queda ou aumento —
    "sem alteração" fica só no log local, para evitar notificar o
    usuário todo dia sem necessidade (silêncio = nada mudou).
    """
    if anterior is not None and resultado["preco"] < anterior:
       enviar_notificacao(f"{resultado['jogo']} teve queda: R$ {anterior} → R$ {resultado['preco']} (menor preço já visto: R$ {menor_preco})")
       logging.info(f"{resultado['jogo']} teve queda: R$ {anterior} → R$ {resultado['preco']} (menor preço já visto: R$ {menor_preco})")
    elif anterior is not None and resultado["preco"] > anterior:
       enviar_notificacao(f"{resultado['jogo']} teve aumento: R$ {anterior} → R$ {resultado['preco']}")
       logging.info(f"{resultado['jogo']} teve aumento: R$ {anterior} → R$ {resultado['preco']}")
    elif anterior is not None:
        logging.info(f"Preço de {resultado['jogo']} sem alteração. Preço atual: R$ {resultado['preco']}")


def salvar_historico(historico):
    """Grava o dicionário de histórico em historico.json."""
    with open("historico.json", "w") as arquivo:
        json.dump(historico, arquivo)


def rodar_varredura(app_ids, historico):
    """
    Busca o preço de todos os jogos monitorados, compara e notifica.

    Para cada jogo: busca o preço, compara com o histórico, envia
    notificação se necessário, e acumula o novo preço no histórico.
    Inclui uma pausa (time.sleep) entre requisições para reduzir o
    risco de a Steam limitar/bloquear chamadas em sequência rápida.
    Salva o histórico atualizado no final, uma única vez.
    """
    for jogo_monitorado in app_ids:
        app_id = jogo_monitorado["app_id"]
        resultado = buscar_preco(app_id)
        time.sleep(1)
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
    """Grava a lista de jogos monitorados em jogos_monitorados.json."""
    with open("jogos_monitorados.json", "w") as arquivo:
        json.dump(app_ids, arquivo)


def carregar_offset():
    """
    Lê o último update_id do Telegram já processado, de telegram_offset.json.

    Evita reprocessar mensagens antigas toda vez que o programa roda.
    Se o arquivo ainda não existir, começa do zero (processa tudo).
    """
    try:
        with open("telegram_offset.json", "r") as arquivo:
            telegram_offset = json.load(arquivo)
    except FileNotFoundError:
        telegram_offset = {"ultimo_update_id": 0}
    return telegram_offset


def salvar_offset(offset):
    """Grava o dicionário de offset em telegram_offset.json."""
    with open("telegram_offset.json", "w") as arquivo:
        json.dump(offset, arquivo)


def buscar_mensagens_novas():
    """
    Busca mensagens novas do Telegram, a partir do offset salvo.

    Usa offset + 1 porque o Telegram devolveria de novo a própria
    mensagem do último update_id se pedíssemos exatamente esse valor.
    """
    codigo = carregar_config_telegram()
    token = codigo["token"]
    offset = carregar_offset()

    url_base = "https://api.telegram.org/bot" + token + "/getUpdates?"
    parametros = {"offset": offset["ultimo_update_id"] + 1} # +1 evita repetir a última mensagem já processada
    query = urllib.parse.urlencode(parametros)
    url_final = url_base + query

    resposta = urllib.request.urlopen(url_final)
    conteudo_bruto = resposta.read()
    decodificado = conteudo_bruto.decode("utf-8")
    dados = json.loads(decodificado)

    return dados["result"]


def processar_comandos(app_ids):
    """
    Lê mensagens novas do Telegram e executa comandos nelas.

    Comandos suportados: /add <app_id>, /remove <app_id>, /list.
    Modifica app_ids diretamente (a lista é mutável) e salva o offset
    do update_id mais recente ao final, para não reprocessar depois.
    """
    mensagens = buscar_mensagens_novas()
    ids_processados = []
    for mensagem in mensagens:
        ids_processados.append(mensagem["update_id"])
        texto = mensagem["message"]["text"]
        print(f"Comando recebido: {texto}")

        if texto.startswith("/add"):
            partes = texto.split()
            try:
                app_id_texto = partes[1]
                app_id_numero = int(app_id_texto)
            except (IndexError, ValueError):
                print("Comando /add precisa vir com um número. Exemplo: /add 730")
                continue

            nome_encontrado = buscar_nome_jogo(app_id_numero)
            if nome_encontrado is not None:
                app_ids.append({"app_id": app_id_numero, "nome": nome_encontrado})
                salvar_jogos_monitorados(app_ids)
                print(f"{nome_encontrado} adicionado via Telegram!")
            else:
                print("Não foi possível encontrar esse app_id.")
        elif texto.startswith("/remove"):
            partes = texto.split()
            try:
                app_id_texto = partes[1]
                app_id_numero = int(app_id_texto)
            except (IndexError, ValueError):
                print("Comando /remove precisa vir com um número. Exemplo: /remove 730")
                continue

            encontrado = None
            for jogo in app_ids:
                if jogo["app_id"] == app_id_numero:
                    encontrado = jogo
            if encontrado is not None:
                app_ids.remove(encontrado)
                salvar_jogos_monitorados(app_ids)
                print(f"{encontrado['nome']} removido via Telegram!")
            else:
                print("Esse app_id não está na sua lista.")
        elif texto.startswith("/list"):
            if not app_ids:
                enviar_notificacao("Nenhum jogo monitorado ainda.")
            else:
                lista_texto = ""
                for jogo in app_ids:
                    lista_texto = lista_texto + f"{jogo['app_id']} - {jogo['nome']}\n"
                enviar_notificacao(lista_texto)
    if ids_processados:
        novo_offset = {"ultimo_update_id": max(ids_processados)}
        salvar_offset(novo_offset)


app_ids = carregar_jogos_monitorados()
historico = carregar_historico()
processar_comandos(app_ids)

# GITHUB_ACTIONS existe automaticamente nas execuções do workflow;
# nesse modo, roda só a varredura (sem menu, já que não há alguém digitando)
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
            texto_digitado = input("Digite o(s) app_id(s) que você quer adicionar (separados por vírgula): ")
            pedacos = texto_digitado.split(",")
            for pedaco in pedacos:
                try:
                    adicionar_app_id = int(pedaco.strip())
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