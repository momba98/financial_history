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
    except:
        pass

def mostrar_dados():

    with st.beta_expander('Mostrar meus dados'):

        carregar_dados()

        mostrar_tudo = st.checkbox('Visualizar os dados por completo (mostrar também colunas auxiliares)', value=False)

        if mostrar_tudo:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.write(df) #mostre que eles estão corretos

        else:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.dataframe(df.drop(['Data Cadastro', 'Parcelamento'], axis=1))

def cadastrar():

    global df

    carregar_dados()

    #formulário

    data_financeira = st.date_input(label='Data da movimentação: ')

    fluxo = st.selectbox(label='Fluxo da movimentação: ', options=['','Entrada', 'Saída', 'Transferência'])

    frequencia = st.selectbox(label='Frequência da movimentação: ',
                              options=['','Singular', 'Múltipla Temporária', 'Múltipla Permanente'] if fluxo!='Transferência' else ['Singular'])

    if frequencia == 'Múltipla Temporária':

        parcelamento = st.text_input(label='Indique em quantas vezes o valor foi parcelado:', value='0')
        parcelamento = int(parcelamento)

    elif frequencia == 'Múltipla Permanente':

        tempo = st.text_input(label='Indique em meses (aproximadamente) quanto tempo esta movimentação perdurará:', value='0')
        tempo = int(tempo)

    valor = st.number_input(label='Valor (R$):')

    instituicao_financeira = st.selectbox(
        label='Instituição Financeira (onde a quantia foi ou estava?)',
        options=np.insert(pd.read_csv(f"listas/instituicoes_financeiras.csv", encoding="ISO-8859-1").values,0,'')
    )

    if fluxo != 'Transferência':

        provedor = st.selectbox(
            label = 'Provedor (quem foi o responsável pela movimentação? Nelogica, pai, mãe etc.):',
            options = np.insert(pd.read_csv(f"listas/provedores_entrada.csv", encoding="ISO-8859-1").values,0,'') if fluxo == 'Entrada' else np.insert(pd.read_csv(f"listas/provedores_saida.csv", encoding="ISO-8859-1").values,0,'')
            )

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
                                'Parcelamento' : str(registro)+'/'+str(parcelamento),
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

            for registro in range(1,tempo+1,1): #vou cadastrar para até 3 anos para frente

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

def excluir():

    global df

    carregar_dados()

    exclusao_retroativa = st.checkbox(label='Permitir a exclusão retroativa', value=False, help='Caso marcado, as movimentações que ocorreram até o dia atual também poderão ser excluídas.')

    tipo_exclusao = st.selectbox('Excluir por...', ['', 'Index (número mais à esquerda da tabela, identificação única)', 'ID'])

    if tipo_exclusao == 'ID':

        index_para_excluir = st.selectbox('Indique a ID da movimentação a ser excluída:', df['ID'].unique() if exclusao_retroativa else df[df['Data']>=date.today()]['ID'].unique())

        index_para_excluir = int(index_para_excluir)

        excluir = st.button('Excluir')

        if excluir:
            if exclusao_retroativa:
                filtro = (df['ID'] == index_para_excluir)
            else:
                filtro = ((df['ID'] == index_para_excluir) & (df['Data']>= date.today()))

            #excluindo uma singular
            if df[filtro]['Frequência'].values[0] == 'Singular':
                df = df.drop(df.index[filtro])
                df.to_csv('sheets/data.csv', index=False)

            # excluindo uma Múltipla
            else:
                 df = df.drop(df.index[filtro])
                 df.to_csv('sheets/data.csv', index=False)

            if exclusao_retroativa:
                st.success(f'Você excluiu todas as movimentações de ID {index_para_excluir}')
            else:
                st.success(f'Você excluiu todas as movimentações futuras de ID {index_para_excluir}')

    elif tipo_exclusao == 'Index (número mais à esquerda da tabela, identificação única)':

        index_para_excluir = st.selectbox('Indique o Index da movimentação a ser excluída:', df.index if exclusao_retroativa else df[df['Data']>=date.today()]['ID'].index)

        index_para_excluir = int(index_para_excluir)

        excluir = st.button('Excluir')

        if excluir:

            df = df.drop(index_para_excluir)

            df.to_csv('sheets/data.csv', index=False)

            st.success(f'Você excluiu a movimentação de Index {index_para_excluir}')

def antecipador():

    global df

    carregar_dados()

    #selecionar apenas as compras com parcelas no futuro:

    index_para_antecipar = st.selectbox('Indique a ID da movimentação que terá uma parcela a ser antecipada:', df[((df['Data']>=date.today()) & (df['Frequência']=='Múltipla Temporária'))]['ID'].unique())

    parcela_para_antecipar = st.selectbox('Indique a parcela a ser antecipada:', df[((df['Data']>=date.today()) & (df['ID']==index_para_antecipar))]['Parcelamento'].values)

    st.write('Confirme a parcela a ser antecipada:')

    st.write(df[((df['ID']==index_para_antecipar) & (df['Parcelamento']==parcela_para_antecipar))])

    #dar o drop neste index

    #e criar a linha nova antecipada

    data_financeira = st.date_input(label='Nova data da movimentação (data em que ocorrerá o débito ou crédito): ')

    valor = st.number_input(label='Novo valor em R$ (com possível desconto):')

    descricao = st.text_input(label='Descrição:')

    if st.button('Cadastrar!'):

        if len(df['ID'].dropna()) == 0:
            ID = 0
        else:
            ID = df['ID'].values[-1] + 1

        df = df.append({'Data Cadastro': date.today(),
                        'Data': data_financeira,
                        'Fluxo': df[((df['ID']==index_para_antecipar) & (df['Parcelamento']==parcela_para_antecipar))]['Fluxo'].values[0],
                        'Frequência' : 'Antecipamento',
                        'Valor' : valor if df[((df['ID']==index_para_antecipar) & (df['Parcelamento']==parcela_para_antecipar))]['Fluxo'].values[0]=='Entrada' else -valor,
                        'Instituição Financeira' : df[((df['ID']==index_para_antecipar) & (df['Parcelamento']==parcela_para_antecipar))]['Instituição Financeira'].values[0],
                        'Provedor' : df[((df['ID']==index_para_antecipar) & (df['Parcelamento']==parcela_para_antecipar))]['Provedor'].values[0],
                        'Descrição': f'Parcela {parcela_para_antecipar} antecipada da movimentação {index_para_antecipar} - '+ descricao,
                        'ID': ID
                        },
                        ignore_index=True)

        df.drop(df[((df['ID']==index_para_antecipar) & (df['Parcelamento']==parcela_para_antecipar))].index, inplace=True)

        df.to_csv('sheets/data.csv', index=False)

        st.success('Movimentação realizada com sucesso!')



    pass


def atualizar_dados():

    st.error("Cuidado! Se você atualizar os seus dados, todas informações serão sincronizadas com os arquivos relacionados à última publicação (em 'Publicar dados').")

    att = st.button('Atualizar')

    if att:

        st.write('Stashing o git. O webapp deve estar atualizado em instantes.')
        subprocess.run(["git", "stash", "-u"])
        st.write('Pronto!')

def publicar_dados():

    st.error('Cuidado! Se você publicar os seus dados, as informações serão sobrescritas no servidor e não haverá como recuperar os arquivos antigos (a não ser que você tenha salvado manualmente um backup no seu computador).')

    publicar = st.button('Publicar')

    if publicar:

        with st.spinner('Dando commit no git. O webapp deve estar atualizado em instantes...'):
            subprocess.run(["git", "add", "*"])
            subprocess.run(["git", "commit", "-m", f"{date.today()}"])
            subprocess.run(["git", "push"])

        st.success('Pronto!')

def dados_com_filtros():

    opcao_de_filtro = st.radio('Qual informação você deseja filtrar?', ['Selecionar','Sem filtro', 'Datas', 'Fluxo', 'Provedor', 'Instituição Financeira', 'ID'])

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

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'Fluxo':

        operador = st.selectbox('Selecione o fluxo desejado:', ['Entrada', 'Saída', 'Transferência'])

        filtro = (df['Fluxo'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'Provedor':

        operador = st.selectbox('Selecione o provedor desejado:', df['Provedor'].unique())

        filtro = (df['Provedor'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'ID':

        operador = st.selectbox('Selecione o ID desejado:', df['ID'].unique())

        filtro = (df['ID'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'Instituição Financeira':

        operador = st.selectbox('Selecione a Instituição Financeira desejada:', df['Instituição Financeira'].unique())

        filtro = (df['Instituição Financeira'] == operador)

        filtrar = st.button('Filtrar')

        if filtrar:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

            st.table(df[filtro].drop(['Data Cadastro', 'Parcelamento'], axis=1))

    elif opcao_de_filtro == 'Sem filtro':

        filtrar = st.button('Filtrar')

        if filtrar:

            df['Valor'] = df['Valor'].map('{:,.2f}'.format)

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
                             '{:,.2f}'.format((row['Valor']*int(str(df[df['ID'] == row['ID']]['Parcelamento'].iloc[0]).split('/')[-1]))), #isso é o valor vezes o número de parcelas
                             int(str(df[df['ID'] == row['ID']]['Parcelamento'].iloc[0]).split('/')[-1]), #isso é o número de parcelas
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

                elif row['Frequência'] == 'Antecipamento':

                    st.markdown(
                            """
                            {} - Movimentação de antecipação da parcela {} da movimentação de ID {} de <span style="color:rgb(6, 191, 0);font-size:larger">**R$ {}**</span>, agora creditado dia {} de {} de {} na conta {}.
                            """.format(
                             contador,
                             row['Descrição'].split(' ')[1],
                             row['Descrição'].split(' ')[5][:-1],
                             row['Valor'], #isso é o valor vezes o número de parcelas
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.values[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().values[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.values[0],
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
                             '{:,.2f}'.format((row['Valor']*int(str(df[df['ID'] == row['ID']]['Parcelamento'].iloc[0]).split('/')[-1]))), #isso é o valor vezes o número de parcelas
                             int(str(df[df['ID'] == row['ID']]['Parcelamento'].iloc[0]).split('/')[-1]), #isso é o número de parcelas
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

                elif row['Frequência'] == 'Antecipamento':

                    st.markdown(
                            """
                            {} - Movimentação de antecipação da parcela {} da movimentação de ID {} de <span style="color:rgb(255, 15, 0);font-size:larger">**R$ {}**</span>, agora debitado dia {} de {} de {} na conta {}.
                            """.format(
                             contador,
                             row['Descrição'].split(' ')[1],
                             row['Descrição'].split(' ')[5][:-1],
                             row['Valor'], #isso é o valor vezes o número de parcelas
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.day.values[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.month_name().values[0],
                             pd.to_datetime(df[df['ID'] == row['ID']]['Data']).dt.year.values[0],
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

    range = st.radio('Selecione o range do Fluxo de Caixa:', ['Selecionar', 'Mensal', 'Anual'], index=2)

    if st.checkbox('Adicionar filtro por Instituição Financeira'):

        ifescolhida = st.selectbox(
            'Selecionar a Instiuição Financeira a ser filtrada:',
            options=df['Instituição Financeira'].unique()
        )

        filtro = df['Instituição Financeira'] == ifescolhida

        texto = '- ' + ifescolhida.upper()

    else:
        filtro = df==df

        texto = ''

    m_indx = []

    for a in pd.read_csv(f"listas/provedores_entrada.csv", encoding="ISO-8859-1").values:
        m_indx.append(('Entrada', a[0]))

    for a in pd.read_csv(f"listas/provedores_saida.csv", encoding="ISO-8859-1").values:
        m_indx.append(('Saída', a[0]))

    for checar_casos in (df[filtro]['Fluxo']+'-'+df[filtro]['Provedor']).unique():
        try: #tente adicionar a tupla de fluxo e de provedor ao db caso não esteja na lista atual
            if (tuple(checar_casos.split('-')) in m_indx): # se já estiver no meu index duplo, faça nada
                pass
            else: #se não estiver, adicione
                #if len(tuple(checar_casos.split(' ')))==2: #desde que tenha apenas
                m_indx.append(tuple(checar_casos.split('-')))
        except: # se nao der (por exemplo, quando é nan, avise.)
            st.warning(f'Algumas movimentações não puderam ser agrupadas (não possuem Provedor ou Fluxo): {checar_casos}')

    m_indx.sort()

    df['Data'] = pd.to_datetime(df['Data']) #NÃO funciona com date apenas, precisa ser datetime... putarias do pandas;

    #independende do range escolhido, preciso do fluxo de caixa anual (mensal necessita saldos dos anos prévios)

    tabela_fluxo_anual = pd.DataFrame(data=None,
        index=pd.MultiIndex.from_tuples(m_indx, names=["Fluxo", "Provedor"]),
        columns=df[filtro]['Data'].dt.year.unique()
    )

    tabela_gp_anual = df[filtro][filtro].groupby(
        [pd.Grouper(key='Data',freq='Y'), 'Fluxo', 'Provedor']
        )['Valor'].sum() #o grouper é o responsável pelo resample no groupby... complexo!

    for ano in tabela_fluxo_anual.columns:
        for fluxo_prov in tabela_fluxo_anual.index:
            try:
                tabela_fluxo_anual.loc[fluxo_prov,ano] = tabela_gp_anual[
                                                             (tabela_gp_anual.index.get_level_values(0).year == ano) &
                                                             (tabela_gp_anual.index.get_level_values(1) == fluxo_prov[0]) &
                                                             (tabela_gp_anual.index.get_level_values(2) == fluxo_prov[1])
                                                             ].values[0]
            except:
                tabela_fluxo_anual.loc[fluxo_prov,ano] = 0

        tabela_fluxo_anual.loc[('', 'Total'),ano] = tabela_fluxo_anual[ano].sum()

    tabela_fluxo_anual.loc[('','Total')] = tabela_fluxo_anual.loc[('','Total')].cumsum()

    saldos_previos = tabela_fluxo_anual.loc[('', 'Total')].to_dict()

    if range == 'Anual':

        st.markdown(f'## FLUXO DE CAIXA ANUAL {texto}')

        table = tabela_fluxo_anual
        x_axis = df[filtro]['Data'].dt.year.unique().astype('str')
        line = table.loc[('','Total')]

    elif range == 'Mensal':

        ano = st.selectbox('Computar os dados para o ano:', df[filtro]['Data'].dt.year.unique())

        st.markdown(f'## FLUXO DE CAIXA - {ano} {texto}')

        meses = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

        tabela_fluxo_mensal = pd.DataFrame(data=None,
            index=pd.MultiIndex.from_tuples(m_indx, names=["Fluxo", "Provedor"]),
            columns=meses
        )

        tabela_gp_mensal = df[filtro].groupby([pd.Grouper(key='Data',freq='M'), 'Fluxo', 'Provedor'])['Valor'].sum() #o grouper é o responsável pelo resample no groupby... complexo!

        for mes in tabela_fluxo_mensal.columns:
            for fluxo_prov in tabela_fluxo_mensal.index:
                try:
                    tabela_fluxo_mensal.loc[fluxo_prov,mes] = tabela_gp_mensal[
                                                                 (tabela_gp_mensal.index.get_level_values(0).month_name() == mes) &
                                                                 (tabela_gp_mensal.index.get_level_values(0).year == ano) &
                                                                 (tabela_gp_mensal.index.get_level_values(1) == fluxo_prov[0]) &
                                                                 (tabela_gp_mensal.index.get_level_values(2) == fluxo_prov[1])
                                                                 ].values[0]
                except:
                    tabela_fluxo_mensal.loc[fluxo_prov,mes] = 0

            saldo = 0

            if mes == 'January':
                try:
                    saldo = saldos_previos[ano-1]
                except:
                    pass

            tabela_fluxo_mensal.loc[('', 'Total'),mes] = tabela_fluxo_mensal[mes].sum() + saldo

        tabela_fluxo_mensal.loc[('','Total')] = tabela_fluxo_mensal.loc[('','Total')].cumsum()

        table = tabela_fluxo_mensal
        x_axis = meses
        line = table.loc[('','Total')]

    #tudo que é comum aos dois

    acumulado = st.checkbox('Visualizar linha de saldo acumulado', True)

    teste = table.T

    teste[('Totais', 'Entrada')] = teste['Entrada'].sum(axis=1)
    teste[('Totais', 'Saída')] = teste['Saída'].sum(axis=1)

    teste.replace(0,np.nan, inplace=True)

    teste.columns = teste.columns.map(''.join).str.strip('')

    trocas = {
        'á': 'a',
        'ã': 'a',
        'à': 'a',
        'â': 'a',
        'é': 'e',
        'ê': 'e',
        'í': 'i',
        'ó': 'o',
        'ô': 'o',
        'õ': 'o',
        'ú': 'u',
        'ç': 'c',
        ' ': ''
    }

    for coluna in teste.columns:
        coluna_corrigida = coluna
        for crt_errado,crt_certo in trocas.items():
            coluna_corrigida = coluna_corrigida.lower().replace(crt_errado, crt_certo)

        teste = teste.rename(
                {
                f'{coluna}': f'{coluna_corrigida}'
                },
            axis='columns'
            )

    teste.index = teste.index.map(str)

    for cr_pct in teste.columns:
        if cr_pct[0] == 'e':
            teste['pct'+cr_pct] = teste[cr_pct]/teste['totaisentrada']

        elif cr_pct[0] == 's':
            teste['pct'+cr_pct] = teste[cr_pct]/teste['totaissaida']
        else:
            pass

    from bokeh.models import ColumnDataSource
    from bokeh.models import HoverTool
    import bokeh.models as bkm
    import bokeh.plotting as bkp

    source = bkm.ColumnDataSource(data=teste)

    p = bkp.figure(
        x_range=x_axis,
        height=400
    )

    # BARRA DE BAIXA

    info_baixa = bkm.Scatter(
        x='index',
        marker='diamond',
        y='totaissaida',
        line_width=15,
        fill_color='rgb(135, 32, 32)',
        line_color ='rgb(135, 32, 32)',
        line_alpha=0.3,
        fill_alpha=0.3
    )

    info_baixa_r = p.add_glyph(source_or_glyph=source, glyph=info_baixa)

    keys = [k for k in dict(source.data).keys() if k[:8] == 'pctsaida']

    arr_keys = ['@'+ak+"{:.2%}" for ak in keys]

    keys = [k.replace('pctsaida', '').capitalize() for k in dict(source.data).keys() if k[:8] == 'pctsaida']

    keys.append('Total')
    arr_keys.append('@'+'totaissaida'+'{$ 0.00}')

    tt_s = dict(zip(keys,arr_keys))

    info_baixa_hover = bkm.HoverTool(renderers=[info_baixa_r],
                             tooltips=tt_s
                        )

    p.add_tools(info_baixa_hover)

    baixa = bkm.VBar(
        x='index',
        bottom=0.,
        top='totaissaida',
        line_width=30,
        #source=source,
        fill_color='rgb(135, 32, 32)',
        line_color ='rgb(135, 32, 32)'
    )

    baixa_r = p.add_glyph(source_or_glyph=source, glyph=baixa)

    # BARRA DE ALTA

    info_alta = bkm.Scatter(
        x='index',
        marker='diamond',
        y='totaisentrada',
        line_width=15,
        fill_color='rgb(150, 150, 150)',
        line_color ='rgb(150, 150, 150)',
        line_alpha=0.3,
        fill_alpha=0.3
    )

    info_alta_r = p.add_glyph(source_or_glyph=source, glyph=info_alta)

    keys = [k for k in dict(source.data).keys() if k[:8] == 'pctentra']

    arr_keys = ['@'+ak+"{:.2%}" for ak in keys]

    keys = [k.replace('pctentrada', '').capitalize() for k in dict(source.data).keys() if k[:8] == 'pctentra']

    keys.append('Total')
    arr_keys.append('@'+'totaisentrada'+'{$ 0.00}')

    tt_e = dict(zip(keys,arr_keys))

    info_alta_hover = bkm.HoverTool(renderers=[info_alta_r],
                             tooltips=tt_e)

    p.add_tools(info_alta_hover)

    alta = bkm.VBar(
        x='index',
        bottom=0.,
        top='totaisentrada',
        line_width=30,
        #source=source,
        fill_color='rgb(32, 135, 60)',
        line_color ='rgb(32, 135, 60)'
    )

    alta_r = p.add_glyph(source_or_glyph=source, glyph=alta)

    # LINHA DE ACUMULADO

    if acumulado:

        info_acum = bkm.Line(
            x='index',
            y='total',
            #line_width=15,
        )

        info_acum_r = p.add_glyph(source_or_glyph=source, glyph=info_acum)

        keys = [k for k in dict(source.data).keys() if k[:3] == 'tot']

        arr_keys = ['@'+ak+'{$ 0.00}' for ak in keys]

        keys = ['Acumulado Total', 'Entrada Período', 'Saída Período']

        tt_t = dict(zip(keys,arr_keys))

        info_acum_hover = bkm.HoverTool(renderers=[info_acum_r],
                                 tooltips=tt_t)

        p.add_tools(info_acum_hover)

    else:
        pass

    from bokeh.models import NumeralTickFormatter

    p.yaxis[0].ticker.desired_num_ticks = 7
    p.yaxis.formatter=NumeralTickFormatter(format="$ 0")
    p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    p.outline_line_alpha = 0
    p.xaxis.major_label_text_font_size = '12pt'
    p.yaxis.major_label_text_font_size = '12pt'

    st.bokeh_chart(
        p,
        use_container_width=True
    )

    with st.beta_expander('Mostrar o extrato'):

        st.dataframe(table.applymap('{:,.2f}'.format), height=1000)

def visual_diario():

    if st.checkbox('Adicionar filtro por Instituição Financeira'):

        ifescolhida = st.selectbox(
            'Selecionar a Instiuição Financeira a ser filtrada:',
            options=df['Instituição Financeira'].unique()
        )

        filtro = df['Instituição Financeira'] == ifescolhida

        texto = '- ' + ifescolhida.upper()

    else:
        filtro = df==df

        texto = ''

    col1, col2 = st.beta_columns(2)

    ano = col1.selectbox(
        'Selecione o ano para visualização:',
         pd.to_datetime(df[filtro]['Data']).dt.year.unique()
    )

    mes = col2.selectbox(
        'Selecione o mês para visualização:',
        np.sort(pd.to_datetime(df[filtro][pd.to_datetime(df[filtro]['Data']).dt.year==ano]['Data']).dt.month.unique())
    )



    format_dict = {}

    raw_data = df[filtro][
        (
        (pd.to_datetime(df[filtro]['Data']).dt.month == mes) &
        (pd.to_datetime(df[filtro]['Data']).dt.year == ano)
        )
    ].drop(['Data Cadastro'], axis='columns')

    visual_diario = pd.DataFrame(
        data = None,
        columns = None,
    )

    for coluna in range(1,raw_data.groupby('Data').count()['ID'].max()+1,1):
        visual_diario[f'Valor {coluna}'] = np.nan
        visual_diario[f'Provedor {coluna}'] = np.nan
        format_dict[f'Valor {coluna}'] = '{:,.2f}'
        format_dict[f'Provedor {coluna}'] = '{:s}'

    for linha in range(1,pd.to_datetime(raw_data.iloc[0]['Data']).days_in_month,1):
        visual_diario.loc[linha] = np.nan

    raw_data.sort_values('Data', inplace=True)

    dia = 0

    for a,b in raw_data.iterrows():

        if b['Data'] != dia:
            constante=1

        visual_diario.loc[pd.to_datetime(b['Data']).day,f'Valor {constante}']=b['Valor']
        visual_diario.loc[pd.to_datetime(b['Data']).day,f'Provedor {constante}']=b['Provedor']

        dia = b['Data']
        constante+=1

    visual_diario.sort_index(inplace=True)

    def color(val):
        color = 'rgba(32, 135, 60, 0.5)' if val > 0 else ('rgba(135, 32, 32, 0.3)' if val < 0 else 'white')
        return 'background-color: %s' % color

    def weekend(val):
        color = 'rgba(32, 135, 60, 0.5)' if val > 0 else ('rgba(135, 32, 32, 0.3)' if val < 0 else 'white')
        return 'background-color: %s' % color

    import calendar

    st.subheader(f'GASTOS DIÁRIOS DE {calendar.month_name[mes].upper()}/{ano} {texto}')

    st.dataframe(visual_diario.style.format(format_dict, na_rep='').applymap(color, subset=pd.IndexSlice[:, [vk for vk in format_dict.keys() if vk[0] == 'V']]).set_properties(**{'font-weight': 'bold','border-color': 'black'}), height=2000)

def configuracoes():

    item = ''
    tipo = ''
    file = ''

    config = st.selectbox('Configurar...',
        ['Selecionar uma opção', 'Instituições Financeiras', 'Provedores', 'Provisionar']
    )

    if config == 'Instituições Financeiras':
        item = 'Instituições Financeiras'
        file = 'instituicoes_financeiras'

    elif config == 'Provisionar':
        item = 'Provisionar'
        file = 'provisionar'

    elif config == 'Provedores':

        tipo = st.selectbox('Qual tipo de provedor você deseja alterar?', ['Entrada', 'Saída'])

        item = 'Provedores'

        if tipo == 'Entrada':
            file = 'provedores_entrada'

        elif tipo == 'Saída':
            file = 'provedores_saida'

    if config == f'{item}':

        arquivo = pd.read_csv(f"listas/{file}.csv", encoding="ISO-8859-1", sep=';')

        if tipo=='':
            st.markdown(f"#### Minha lista de {item} é...")
        else:
            st.markdown(f"#### Minha lista de {item} de {tipo} é...")

        st.write('')
        st.write(arquivo)
        st.markdown("#### **Eu quero...**")
        st.write('')

        acao = st.radio('', ['Selecionar uma opção', f'Adicionar {item}', f'Excluir {item}'])

        if acao == f'Adicionar {item}':

            if file == 'provisionar':

                posi_ou_nega = st.selectbox('Escolha o tipo de provisão:', ['','Entrada', 'Saída'])

                if posi_ou_nega == 'Entrada':

                    inst_add = st.selectbox(
                        f'Escolha o item para criar provisão positiva (baseado na lista de Provedores):',
                        pd.read_csv(f"listas/provedores_entrada.csv", encoding="ISO-8859-1")['Provedores'].tolist()
                    )
                    valor_add = st.number_input(f'Digite o valor em R$')

                elif posi_ou_nega == 'Saída':

                    inst_add = st.selectbox(
                        f'Escolha o item para criar provisão negativa (baseado na lista de Provedores):',
                        pd.read_csv(f"listas/provedores_saida.csv", encoding="ISO-8859-1")['Provedores'].tolist()
                    )
                    valor_add = st.number_input(f'Digite o valor em R$ (não se preocupe com o sinal)')*-1

            else:
                inst_add = st.text_input(f'Digite o nome ({item})')


        elif acao == f'Excluir {item}':

            inst_exd = st.selectbox(
                f'Escolha o item ({item}) a ser excluído',
                options=arquivo[item]
                )

        if st.button('Modificar!'):

            if acao == f'Adicionar {item}':
                if file == 'provisionar':
                    arquivo = arquivo.append({item:inst_add, 'Valor':valor_add}, True)
                else:
                    arquivo = arquivo.append({item:inst_add}, True)

            elif acao == f'Excluir {item}':
                arquivo.drop(arquivo[arquivo[item]==inst_exd].index, inplace=True)

            arquivo.to_csv(f"listas/{file}.csv", index=False, encoding="ISO-8859-1", sep=';')

            st.success('Realizado!')
            st.markdown(f"#### **Sua lista de {item} atualizada é:**")
            st.write('')

            st.write(arquivo)

st.sidebar.title("""

Financial History

""")

st.sidebar.image(Image.open('img/logo3.png'), output_format='png', width=300, )

st.sidebar.markdown("### Selecione uma das opções")

st.markdown(
    """ <style>
            div[role="radiogroup"] >  :first-child{
                display: none !important;
            }
        </style>
        """,
    unsafe_allow_html=True
)

menu = st.sidebar.radio('', ['Selecione uma opção no menu ao lado!', 'Modificar os dados', 'Visualizar os dados', 'Configurações'])

st.markdown(f"# **{menu}**")

if menu == 'Modificar os dados':

    carregar_dados() #carregue ou crie os dados

    st.sidebar.markdown("#### **O que você deseja fazer?**")

    opcoes_primarias = st.sidebar.radio(
        label='',
        options = (
            'Selecione mais uma opção no menu ao lado!',
            'Cadastrar uma movimentação',
            'Excluir uma movimentação',
            'Antecipar uma parcela',
            'Atualizar dados',
            'Publicar dados'),
        )

    st.markdown(f"## **{opcoes_primarias}**")

    if opcoes_primarias == 'Atualizar dados':
        atualizar_dados()

    elif opcoes_primarias == 'Cadastrar uma movimentação':
        cadastrar()
        mostrar_dados()

    elif opcoes_primarias == 'Excluir uma movimentação':
        excluir()
        mostrar_dados()

    elif opcoes_primarias == 'Antecipar uma parcela':
        antecipador()
        mostrar_dados()

    elif opcoes_primarias == 'Publicar dados':
        publicar_dados()

elif menu == 'Visualizar os dados':

    carregar_dados()

    st.sidebar.markdown("#### **O que você deseja fazer?**")

    opcoes_secundarias = st.sidebar.radio(
        label = '',
        options = (
            'Selecione mais uma opção no menu ao lado!',
            'Conferir cadastros',
            'Dados com filtros',
            'Fluxo de caixa',
            'Visualização diária'),
        )

    st.markdown(f"## **{opcoes_secundarias}**")

    if opcoes_secundarias == 'Conferir cadastros':
        conferir_cadastros()
        mostrar_dados()

    elif opcoes_secundarias == 'Dados com filtros':
        dados_com_filtros()
        mostrar_dados()

    elif opcoes_secundarias == 'Fluxo de caixa':
        fluxo_de_caixa()

    elif opcoes_secundarias == 'Visualização diária':
        visual_diario()


elif menu == 'Configurações':

    configuracoes()
