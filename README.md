# Rastreador de Preços da Steam

## O Problema
Ele consegue buscar os preços atuais de jogos sem precisar entrar manualmente na Steam pra checar, ele consegue automatizar isso e ainda te mostrar se o jogo teve uma queda de preço (entrando em uma possível promoção) ou se aumentou.

## O que ele faz hoje?
- Busca o preço atual de um jogo a partir do ID dele na Steam
- Indica quando o jogo não tem preço disponível (geralmente por ser gratuito)
- Compara com o histórico e avisa se o preço caiu, subiu, ou se manteve estável

## Próximos passos
- Adicionar um jeito do usuário informar os jogos que quer acompanhar (por nome, URL ou ID — ainda não decidido)
- Automatizar a execução e notificar quando o preço cair
- Mostrar o histórico de forma mais organizada e legível
- Outras melhorias, ainda por definir

## Como Executar

1. Instale o Python ([download oficial](https://www.python.org/downloads/)) — não é necessário instalar nenhuma biblioteca extra, o projeto usa só bibliotecas padrão do Python.

2. Clone o repositório
```bash
git clone https://github.com/pietrobitencourt/steam-price-tracker
```

3. Acesse a pasta do projeto
```bash
cd steam-price-tracker
```

4. Execute o programa
```bash
python rastreador_precos.py
```