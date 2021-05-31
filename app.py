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

st.set_page_config(page_title='Financial History', page_icon="https://static.streamlit.io/examples/cat.jpg", layout='centered', initial_sidebar_state='auto')

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
                                    ])

        file.to_csv('sheets/data.csv', index=False) #crie este arquivo

    df = pd.read_csv('sheets/data.csv') #e então carregue este arquivo

def mostrar_dados():

    with st.beta_expander('Mostrar meus dados'):

        carregar_dados()

        mostrar_tudo = st.checkbox('Visualizar os dados por completo (mostrar também colunas auxiliares)', value=False)

        if mostrar_tudo:

            st.write(df) #mostre que eles estão corretos

        else:
            st.write(df.drop('Data Cadastro', axis=1))

def cadastrar():

    global df

    carregar_dados()

    st.header("Cadastre uma movimentação")

    data_financeira = st.date_input(label='Data da movimentação: ')
    fluxo = st.selectbox(label='Fluxo da movimentação: ', options=['','Entrada', 'Saída'])
    frequencia = st.selectbox(label='Frequência da movimentação: ', options=['','Singular', 'Múltipla Temporária', 'Múltipla Permanente'])
    if frequencia == 'Múltipla Temporária':
        parcelamento = st.text_input(label='Indique em quantas vezes o valor foi parcelado:', value='0')
        parcelamento = int(parcelamento)
    valor = st.number_input(label='Valor (R$):')
    instituicao_financeira = st.selectbox(label='Instituição Financeira (onde a quantia foi ou estava?)', options=['','Nubank', 'Inter', 'C6', 'PicPay', 'Hipercard', 'Cofre'])
    provedor = st.text_input(label='Provedor (quem foi o responsável pela movimentação? Nelogica, pai, mãe etc.):')
    descricao = st.text_input(label='Descrição:')

    data_cadastro = date.today()

    cadastrar = st.button('Cadastrar')

    if cadastrar:

        if frequencia == 'Múltipla Temporária': #se for parcelamento, tenho que fazer algumas modificações nas info:

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
                                'Valor' : valor/parcelamento,
                                'Instituição Financeira' : instituicao_financeira,
                                'Provedor' : provedor,
                                'Descrição': descricao,
                                'ID': ID
                                },
                                ignore_index=True)

                data_financeira_trabalhada = data_financeira_trabalhada + relativedelta(months=1)

            df.to_csv('sheets/data.csv', index=False)

            st.write(f'Movimentação (ID {ID}) cadastrada!')

        elif frequencia == 'Múltipla Permanente': #se for mensalidade, tenho que fazer algumas modificações nas info:

            if len(df['ID'].dropna()) == 0:
                ID = 0
            else:
                ID = df['ID'].values[-1] + 1

            data_financeira_trabalhada = data_financeira

            ano_em_meses = 12

            for registro in range(1,(ano_em_meses*10)+1,1): #vou cadastrar para até 10 anos para frente

                df = df.append({'Data Cadastro': data_cadastro,
                                'Data': data_financeira_trabalhada,
                                'Fluxo': fluxo,
                                'Frequência' : frequencia,
                                'Valor' : valor,
                                'Instituição Financeira' : instituicao_financeira,
                                'Provedor' : provedor,
                                'Descrição': descricao,
                                'ID': ID
                                },
                                ignore_index=True)

                data_financeira_trabalhada = data_financeira_trabalhada + relativedelta(months=1)

            df.to_csv('sheets/data.csv', index=False)

            st.write(f'Movimentação (ID {ID}) cadastrada!')


        else:

            if len(df['ID'].dropna()) == 0:
                ID = 0
            else:
                ID = df['ID'].values[-1] + 1

            df = df.append({'Data Cadastro': data_cadastro,
                            'Data': data_financeira,
                            'Fluxo': fluxo,
                            'Frequência' : frequencia,
                            'Valor' : valor,
                            'Instituição Financeira' : instituicao_financeira,
                            'Provedor' : provedor,
                            'Descrição': descricao,
                            'ID': ID
                            },
                            ignore_index=True)

            df.to_csv('sheets/data.csv', index=False)

            st.write(f'Movimentação (ID {ID}) cadastrada!')

def selecionar_opcoes():

    opcoes_primarias = st.selectbox(
        label = 'O que você deseja fazer?',
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
            filtro = ((df['ID'] == index_para_excluir) & (pd.to_datetime(df['Data']).dt.date >= date.today())) # q porra, única forma que funcionou

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
                st.write(f'Você excluiu todas as cobranças da movimentação {index_para_excluir}')
            else:
                st.write(f'Você excluiu todas as cobranças futuras da movimentação {index_para_excluir}')
        except:
            st.write('Não foi possível encontrar a linha desejada! Cheque novamente o índice.')

def publicar_dados():

    st.write('Dando commit no git. O webapp deve estar atualizado em instantes.')

    subprocess.run(["git", "add", "*"])
    subprocess.run(["git", "commit", "-m", f"{date.today()}"])
    subprocess.run(["git", "push"])

    st.write('Pronto!')

carregar_dados() #carregue ou crie os dados

selecionar_opcoes()

mostrar_dados()
