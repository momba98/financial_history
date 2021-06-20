
# financial_history

Sistema de gestão financeira pessoal.

Com financial_history, o usuário consegue **controlar suas movimentações financeiras** em várias instituições financeiras diferentes de forma personalizada, além de conseguir **classificar todos os motivos de seus gastos e ganhos** (com os chamados provedores), entendo melhor seu comportamento e conseguindo **tomar decisões em fatos** - e não achismos.

**As áreas do software são:**

1. **Modificar os dados**
	Área destinada para manipulação do banco de dados do usuário - onde toda e qualquer movimentação será criada, alterada ou excluída.

    1.1 **Cadastrar uma movimentação:** criar movimentações financeiras.

    1.2 **Excluir uma movimentação:** apagar movimentações financeiras.
	
    1.3 **Antecipar uma parcela**: antecipar parcelas de alguma movimentação financeira já criada.

    1.4 **Atualizar os dados:** sincronizar com últimos dados salvos no servidor (GitHub). Serve como um backup!

    1.5 **Publicar os dados:** enviar os dados para o servidor (GitHub).

2. **Visualizar os dados**
	Área destinada para observação do banco de dados do usuário - onde a análise financeira pode ser feita de fato.
	
    2.1 **Conferir cadastros:** visualizar as movimentações cadastradas de forma escrita. Pode ajudar na compreensão quando as coisas ficam mais complexas ou volumosas.

    2.2 **Dados com filtros:** filtro simples, bem como se faz numa planilha qualquer.

    2.3 **Fluxo de caixa:** agrupamento das movimentações, previsão de caixa futuro, visualização de provisões, extratos financeiros. 

    2.4 **Visualização diária:** acompanhamento diário dos gastos. Ferramenta útil para averiguação da consistência dos cadastros e procura por padrão comportamental.

3. **Configurações**
	Área destinada para uniformização e personalização dos dados. 
	> :warning: **A primeira ação de um usuário iniciante no software é criar suas listas de opções nesta aba!**

    3.1 **Configurar Instituições Financeiras:** neste campo, o usuário consegue informar ao software todas as formas de armazenar dinheiro que ele deseja.

    3.2 **Configurar Provedores:** neste campo, o usuário consegue informar ao software todas as formas de explicar as movimentações que ele deseja.

    3.3 **Configurar Provisões:** neste campo, o usuário consegue informar ao software todas as provisões que possui.

**Instruções de utilização:**

1. Baixe o repositório e possuir o software [Anaconda (com Python versão 3.8)](https://repo.anaconda.com/archive/Anaconda3-2021.05-Windows-x86_64.exe) instalado em seu computador.

2. Instale os pacotes requisitados com o comando no prompt `pip install -r requirements.txt` (ir até a pasta com o repositório baixado com o Explorador de Arquivos e digitar `cmd` no browser). **DEPOIS DE DIGITAR O CÓDIGO APERTAR ENTER!**

3. Abrir o arquivo `Financial History` e começar utilizar!

> O software foi feito para facilitar a manipulação das movimentações financeiras. Porém, caso o usuário ache conveniente, o arquivo `dados.xlsx` pode ser manipulado manualmente também.