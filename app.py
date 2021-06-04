import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time
import os
import xlrd
import numpy as np
import subprocess
from bokeh.plotting import figure


st.set_page_config(page_title='Financial History', page_icon="https://static.streamlit.io/examples/cat.jpg", layout='wide', initial_sidebar_state='auto')

pd.options.display.float_format = '${:,.2f}'.format

st.title("""

Financial History

""")

def atualizar_dados():

    att = st.button('Atualizar')

    if att:

        st.write('Stashing o git. O webapp deve estar atualizado em instantes.')
        subprocess.run(["git", "stash", "-u"])
        st.write('Pronto!')

def carregar_dados():

    global df

    if not len(os.listdir('sheets')): #se não existe nada na pasta,
        file = pd.DataFrame(columns=['ID',
                                    'Data Cadastro',
                                    'Data',
                                    'Fluxo',
                                    'Frequência',
                                    'Valor',
                                    'Instituição Financeira',
                                    'Provedor',
                                    'Descrição',
                                    'Parcelamento',
                                    ])

        file.to_csv('sheets/data.csv', index=False) #crie este arquivo

    data_parser = lambda x: pd.datetime.strptime(x[:10], '%Y-%m-%d')

    df = pd.read_csv('sheets/data.csv', parse_dates=['Data','Data Cadastro'],date_parser=data_parser) #e então carregue este arquivo

    try:
        df['Data'] = df['Data'].dt.date
        df['Data Cadastro'] = df['Data Cadastro'].dt.date
        df['Valor'] = df['Valor'].map('{:,.2f}'.format)
    except:
        pass

def mostrar_dados():

    with st.beta_expander('Mostrar meus dados'):

        carregar_dados()

        mostrar_tudo = st.checkbox('Visualizar os dados por completo (mostrar também colunas auxiliares)', value=False)

        if mostrar_tudo:

            st.write(df) #mostre que eles estão corretos

        else:

            st.dataframe(df.drop(['Data Cadastro', 'Parcelamento'], axis=1))

def cadastrar():

    global df

    carregar_dados()

    st.header("Cadastre uma movimentação")

    #formulário

    data_financeira = st.date_input(label='Data da movimentação: ')

    fluxo = st.selectbox(label='Fluxo da movimentação: ', options=['','Entrada', 'Saída', 'Transferência'])

    frequencia = st.selectbox(label='Frequência da movimentação: ',
                              options=['','Singular', 'Múltipla Temporária', 'Múltipla Permanente'] if fluxo!='Transferência' else ['Singular'])

    if frequencia == 'Múltipla Temporária':

        parcelamento = st.text_input(label='Indique em quantas vezes o valor foi parcelado:', value='0')
        parcelamento = int(parcelamento)

    valor = st.number_input(label='Valor (R$):')

    instituicao_financeira = st.selectbox(label='Instituição Financeira (onde a quantia foi ou estava?)', options=['','Nubank', 'Inter', 'C6', 'PicPay', 'Hipercard', 'B3', 'Alelo', 'Carteira'])

    if fluxo != 'Transferência':

        provedor = st.selectbox(label = 'Provedor (quem foi o responsável pela movimentação? Nelogica, pai, mãe etc.):',
                                options = ['', 'Trabalho', 'Outros'] if fluxo == 'Entrada' else ['', 'Alimentação', 'Gasolina', 'Lazer', 'Vestiário', 'Transporte', 'Saúde', 'Estudos', 'Casa', 'Outros'])

        descricao = st.text_input(label='Descrição:')

    else:

        instituicao_financeira_2 = st.selectbox(label='Para qual Instituição Financeira o valor foi destiando?', options=['','Nubank', 'Inter', 'C6', 'PicPay', 'Hipercard', 'B3', 'Cofre'])


    data_cadastro = date.today()

    # botão cadastrar

    cadastrar = st.button('Cadastrar')

    if cadastrar:

        if fluxo == 'Transferência': #se for Transferência, tenho que fazer algumas modificações nas info (ficou feio, logo arrumo):

            provedor = None
            descricao = None

            #saída de um banco para outro

            if len(df['ID'].dropna()) == 0:
                ID = 0
            else:
                ID = df['ID'].values[-1] + 1

            df = df.append({'Data Cadastro': data_cadastro,
                            'Data': data_financeira,
                            'Fluxo': fluxo,
                            'Frequência' : frequencia,
                            'Valor' : -valor,
                            'Instituição Financeira' : instituicao_financeira,
                            'Descrição': f'Saída {instituicao_financeira} para {instituicao_financeira_2}',
                            'ID': ID
                            },
                            ignore_index=True)

            df.to_csv('sheets/data.csv', index=False)

            #chegada do um banco para o outro

            df = df.append({'Data Cadastro': data_cadastro,
                            'Data': data_financeira,
                            'Fluxo': fluxo,
                            'Frequência' : frequencia,
                            'Valor' : +valor,
                            'Instituição Financeira' : instituicao_financeira_2,
                            'Descrição': f'Entrada {instituicao_financeira_2} de {instituicao_financeira}',
                            'ID': ID
                            },
                            ignore_index=True)

            df.to_csv('sheets/data.csv', index=False)

            st.success(f'Movimentação (ID {ID}) cadastrada!')

        elif frequencia == 'Múltipla Temporária': #se for parcelamento, tenho que fazer algumas modificações nas info:

            #olhar para o meu df e ver qual é o último parcelamento, nomear este como o último + 1

            if len(df['ID'].dropna()) == 0:
                ID = 0
            else:
                ID = df['ID'].values[-1] + 1

            data_financeira_trabalhada = data_financeira

            for registro in range(1,parcelamento+1,1):

                df = df.append({'Data Cadastro': data_cadastro,
                                'Data': data_financeira_trabalhada,
                                'Fluxo': fluxo,
                                'Frequência' : frequencia,
                                'Parcelamento' : registro,
                                'Valor' : valor/parcelamento if fluxo=='Entrada' else -valor/parcelamento,
                                'Instituição Financeira' : instituicao_financeira,
                                'Provedor' : provedor,
                                'Descrição': descricao + '(PARCELA ' +str(registro) + ')',
                                'ID': ID
                                },
                                ignore_index=True)

                data_financeira_trabalhada = data_financeira_trabalhada + relativedelta(months=1)

            df.to_csv('sheets/data.csv', index=False)

            st.success(f'Movimentação (ID {ID}) cadastrada!')

        elif frequencia == 'Múltipla Permanente': #se for mensalidade, tenho que fazer algumas modificações nas info:

            if len(df['ID'].dropna()) == 0:
                ID = 0
            else:
                ID = df['ID'].values[-1] + 1

            data_financeira_trabalhada = data_financeira

            ano_em_meses = 12

            for registro in range(1,(ano_em_meses*3)+1,1): #vou cadastrar para até 3 anos para frente

                df = df.append({'Data Cadastro': data_cadastro,
                                'Data': data_financeira_trabalhada,
                                'Fluxo': fluxo,
                                'Frequência' : frequencia,
                                'Valor' : valor if fluxo=='Entrada' else -valor,
                                'Instituição Financeira' : instituicao_financeira,
                                'Provedor' : provedor,
                                'Descrição': descricao,
                                'ID': ID
                                },
                                ignore_index=True)

                data_financeira_trabalhada = data_financeira_trabalhada + relativedelta(months=1)

            df.to_csv('sheets/data.csv', index=False)

            st.success(f'Movimentação (ID {ID}) cadastrada!')


        else: #se for um registro singular:

            if len(df['ID'].dropna()) == 0:
                ID = 0
            else:
                ID = df['ID'].values[-1] + 1

            df = df.append({'Data Cadastro': data_cadastro,
                            'Data': data_financeira,
                            'Fluxo': fluxo,
                            'Frequência' : frequencia,
                            'Valor' : valor if fluxo=='Entrada' else -valor,
                            'Instituição Financeira' : instituicao_financeira,
                            'Provedor' : provedor,
                            'Descrição': descricao,
                            'ID': ID
                            },
                            ignore_index=True)

            df.to_csv('sheets/data.csv', index=False)

            st.success(f'Movimentação (ID {ID}) cadastrada!')

def selecionar_opcoes():

    opcoes_primarias = st.selectbox(
        label = 'O que você deseja modificar?',
        options = ('Selecione uma opção', 'Atualizar dados','Cadastrar uma movimentação', 'Excluir uma movimentação', 'Publicar dados'),
        )

    if opcoes_primarias == 'Atualizar dados':
        atualizar_dados()

    elif opcoes_primarias == 'Cadastrar uma movimentação':
        cadastrar()

    elif opcoes_primarias == 'Excluir uma movimentação':
        excluir()

    elif opcoes_primarias == 'Publicar dados':
        publicar = st.button('Publicar')

        if publicar:
            publicar_dados()

def excluir():

    global df

    carregar_dados()

    exclusao_retroativa = st.checkbox(label='Permitir a exclusão retroativa', value=False, help='Caso marcado, as movimentações que ocorreram até o dia atual também serão excluídas.')

    index_para_excluir = st.text_input(label='Indique a ID da linha a ser excluída:', value='0')

    index_para_excluir = int(index_para_excluir)

    excluir = st.button('Excluir')

    if excluir:
        if exclusao_retroativa:
            filtro = (df['ID'] == index_para_excluir)
        else:
            filtro = ((df['ID'] == index_para_excluir) & (df['Data']>= date.today()))

        try:
            #excluindo uma singular
            if df[filtro]['Frequência'].values[0] == 'Singular':
                df = df.drop(df.index[filtro])
                df.to_csv('sheets/data.csv', index=False)

            # excluindo uma Múltipla
            else:
                 df = df.drop(df.index[filtro])
                 df.to_csv('sheets/data.csv', index=False)

            if exclusao_retroativa:
                st.success(f'Você excluiu todas as cobranças da movimentação {index_para_excluir}')
            else:
                st.success(f'Você excluiu todas as cobranças futuras da movimentação {index_para_excluir}')
        except:
            st.error('A movimentação já foi liquidada (aconteceu antes de hoje) ou não foi possível encontrar a linha desejada!')

def publicar_dados():

    st.write('Dando commit no git. O webapp deve estar atualizado em instantes.')

    subprocess.run(["git", "add", "*"])
    subprocess.run(["git", "commit", "-m", f"{date.today()}"])
    subprocess.run(["git", "push"])

    st.write('Pronto!')

def dados_com_filtros():

    opcao_de_filtro = st.selectbox('Qual dado você deseja filtrar?', ['Sem filtro', 'Datas', 'Fluxo', 'Provedor', 'ID'])

    if opcao_de_filtro == 'Datas':

        tipo_data = st.selectbox('Selecione a data a ser filtrada:', ['Cadastro', 'Financeira'])

        if tipo_data == 'Cadastro':
            a_data_e = 'Data Cadastro'
        else:
            a_data_e = 'Data'

        operador = st.selectbox('Selecione o operador matemático:', ['>=', '=', '<='])

        data_filtrada = st.date_input(label='Data para filtrar: ')

        if operador == '>=':
            filtro = (df[a_data_e] >= data_filtrada)

        elif operador == '=':
            filtro = (df[a_data_e] == data_filtrada)

        elif operador == '<=':
            filtro = (df[a_data_e] <= data_filtrada)

        filtrar = st.button('Filtrar')

        if filtrar:

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'Fluxo':

        operador = st.selectbox('Selecione o fluxo desejado:', ['Entrada', 'Saída', 'Transferência'])

        filtro = (df['Fluxo'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'Provedor':

        operador = st.selectbox('Selecione o fluxo desejado:', df['Provedor'].unique())

        filtro = (df['Provedor'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'ID':

        operador = st.selectbox('Selecione o fluxo desejado:', df['ID'].unique())

        filtro = (df['ID'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    else:

        filtrar = st.button('Filtrar')

        if filtrar:

            st.table(df.drop(['Data Cadastro', 'Parcelamento'], axis=1))

def conferir_cadastros():

    data_registrada = st.selectbox('Selecione a data de cadastro:', np.append(df['Data Cadastro'].unique(), values='Sem Filtro'))

    if data_registrada == 'Sem Filtro':
        filtro = (df == df)
    else:
        filtro = (df['Data Cadastro'] == data_registrada)

    filtrar = st.button('Filtrar')

    if filtrar:

        contador = 0

        for index, row in df[filtro].drop_duplicates(subset=['ID']).iterrows(): #itrar sobre todos os itens únicos cadastrados no meu extrato

            if row['Fluxo'] == 'Entrada':

                if row['Frequência'] == 'Singular':

                    st.markdown(
                            """
                            {} - Movimentação esporádica de <span style="color:rgb(6, 191, 0);font-size:larger">**R$ {}**</span> com data de crédito {} de {} de {} na conta {}.
                            """.format(
                             contador,
                             row['Valor'],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().unique()[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.unique()[0],
                             row['Instituição Financeira']
                             ),
                             True
                        )

                elif row['Frequência'] == 'Múltipla Temporária':

                    st.markdown(
                            """
                            {} - Movimentação parcelada de <span style="color:rgb(6, 191, 0);font-size:larger">**R$ {}**</span> em {} vezes, creditado todo dia {} (de {}/{} até {}/{}) na conta {}.
                            """.format(
                             contador,
                             row['Valor']*(df[df['ID'] == row['ID']]['Parcelamento'].iloc[-1]), #isso é o valor vezes o número de parcelas
                             int(df[df['ID'] == row['ID']]['Parcelamento'].iloc[-1]), #isso é o número de parcelas
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0], #isso é o dia do mês que será creditado
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().iloc[0], #o mês que começará o crédito
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.iloc[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().iloc[-1], #o mês que começará o crédito
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.iloc[-1], #e o que terminará
                             row['Instituição Financeira']
                             ), True
                        )

                elif row['Frequência'] == 'Múltipla Permanente':

                    st.markdown(
                            """
                            {} - Movimentação fixa de <span style="color:rgb(6, 191, 0);font-size:larger">**R$ {}**</span>, creditado todo dia {} na conta {}.
                            """.format(
                             contador,
                             row['Valor'], #isso é o valor vezes o número de parcelas
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0],
                             row['Instituição Financeira']
                             ), True
                        )


            elif row['Fluxo'] == 'Saída':

                if row['Frequência'] == 'Singular':

                    st.markdown(
                            """
                            {} - Movimentação esporádica de <span style="color:rgb(255, 15, 0);font-size:larger">**R$ {}**</span> com data de débito {} de {} de {} da conta {}.
                            """.format(
                             contador,
                             row['Valor'],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().unique()[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.unique()[0],
                             row['Instituição Financeira']
                             ),
                             True
                        )

                elif row['Frequência'] == 'Múltipla Temporária':

                    st.markdown(
                            """
                            {} - Movimentação parcelada de <span style="color:rgb(255, 15, 0);font-size:larger">**R$ {}**</span> em {} vezes, debitado todo dia {} (de {}/{} até {}/{}) da conta {}.
                            """.format(
                             contador,
                             row['Valor']*(df[df['ID'] == row['ID']]['Parcelamento'].iloc[-1]), #isso é o valor vezes o número de parcelas
                             int(df[df['ID'] == row['ID']]['Parcelamento'].iloc[-1]), #isso é o número de parcelas
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0], #isso é o dia do mês que será creditado
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().iloc[0], #o mês que começará o crédito
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.iloc[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().iloc[-1], #o mês que começará o crédito
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.iloc[-1], #e o que terminará
                             row['Instituição Financeira']
                             ), True
                        )

                elif row['Frequência'] == 'Múltipla Permanente':

                    st.markdown(
                            """
                            {} - Movimentação fixa de <span style="color:rgb(255, 15, 0);font-size:larger">**R$ {}**</span>, debitado todo dia {} da conta {}.
                            """.format(
                             contador,
                             row['Valor'], #isso é o valor vezes o número de parcelas
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0],
                             row['Instituição Financeira']
                             ), True
                        )

            elif row['Fluxo'] == 'Transferência':

                st.markdown(
                        """
                        {} - Transferência de <span style="color:rgb(232, 183, 7);font-size:larger">**R$ {}**</span> de {} para {} no dia {} de {} de {}.
                        """.format(
                        contador,
                        abs(row['Valor']), #isso é o valor vezes o número de parcelas
                        row['Instituição Financeira'],
                        df['Instituição Financeira'].iloc[index+1],
                        pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.unique()[0],
                        pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().unique()[0],
                        pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.unique()[0],
                        ), True
                    )

            else:
                pass

            contador += 1

def fluxo_de_caixa():

    df['Data'] = pd.to_datetime(df['Data']) #NÃO funciona com date apenas, precisa ser datetime... putarias do pandas;

    ano = st.selectbox('Computar os dados para o ano:', df['Data'].dt.year.unique())

    st.markdown(f'## FLUXO DE CAIXA - {ano}')

    m_indx = [('Entrada', 'Trabalho'),
              ('Entrada', 'Outros'),
              ('Saída', 'Alimentação'),
              ('Saída', 'Gasolina'),
              ('Saída', 'Lazer'),
              ('Saída', 'Vestiário'),
              ('Saída', 'Transporte'),
              ('Saída', 'Saúde'),
              ('Saída', 'Estudos'),
              ('Saída', 'Casa'),
              ('Saída', 'Outros'),
              ('', 'Total'),
              ]

    tabela_fluxo = pd.DataFrame(data=None,
        index=pd.MultiIndex.from_tuples(m_indx, names=["Fluxo", "Provedor"]),
        columns=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    )

    df['Data'] = pd.to_datetime(df['Data']) #NÃO funciona com date apenas, precisa ser datetime... putarias do pandas;

    tabela_gp = df.groupby([pd.Grouper(key='Data',freq='M'), 'Fluxo', 'Provedor'])['Valor'].sum() #o grouper é o responsável pelo resample no groupby... complexo!

    for mes in tabela_fluxo.columns:
        for fluxo_prov in tabela_fluxo.index:
            try:
                tabela_fluxo.loc[fluxo_prov,mes] = tabela_gp[(tabela_gp.index.get_level_values(0).month_name() == mes) &
                                                             (tabela_gp.index.get_level_values(0).year == ano) &
                                                             (tabela_gp.index.get_level_values(1) == fluxo_prov[0]) &
                                                             (tabela_gp.index.get_level_values(2) == fluxo_prov[1])
                                                             ].values[0]
            except:
                tabela_fluxo.loc[fluxo_prov,mes] = 0

        tabela_fluxo.loc[('', 'Total'),mes] = tabela_fluxo[mes].sum()

    tabela_fluxo.rename(dict(zip(tabela_fluxo.columns, [a[:3] for a in tabela_fluxo.columns])), axis='columns', inplace=True)

    st.dataframe(tabela_fluxo.applymap('{:,.2f}'.format), height=1000)

def grafico():
        """

        x = df['Data']
        y = df['Valor']

        p = figure(
            title='simple line example',
            x_axis_label='x',
            x_axis_type='datetime',
            y_axis_label='y')

        p.vbar(x, bottom=0, top=y, legend_label='Trend', line_width=30)

        st.bokeh_chart(p, use_container_width=True)
        """

menu = st.sidebar.selectbox('Escolha entre as oções:', ['Modificar os dados', 'Visualizar os dados'])

if menu == 'Modificar os dados':

    carregar_dados() #carregue ou crie os dados

    selecionar_opcoes()

    mostrar_dados()

elif menu == 'Visualizar os dados':

    carregar_dados()

    opcoes_secundarias = st.selectbox(
        label = 'O que você deseja visualizar?',
        options = ('Selecione uma opção', 'Conferir cadastros', 'Dados com filtros', 'Fluxo de caixa', 'Métricas'),
        )

    if opcoes_secundarias == 'Conferir cadastros':
        conferir_cadastros()

    if opcoes_secundarias == 'Dados com filtros':
        dados_com_filtros()

    if opcoes_secundarias == 'Fluxo de caixa':
        fluxo_de_caixa()

    mostrar_dados()
