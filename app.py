import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta, date
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
        file = pd.DataFrame(columns=['Data Cadastro',
                                    'Data Financeira',
                                    'Fluxo',
                                    'Frequência',
                                    'Valor',
                                    'Instituição Financeira',
                                    'Provedor',
                                    'Descrição'
                                    ])

        file.to_csv('sheets/data.csv', index=False) #crie este arquivo

    df = pd.read_csv('sheets/data.csv') #e então carregue este arquivo

def mostrar_dados():

    with st.beta_expander('Mostrar meus dados'):

        carregar_dados()

        st.write(df) #mostre que eles estão corretos

def cadastrar():

    global df

    carregar_dados()

    st.header("Cadastre uma movimentação")

    data_financeira = st.date_input(label='Data da movimentação: ')
    fluxo = st.selectbox(label='Fluxo da movimentação: ', options=['','Entrada', 'Saída'])
    frequencia = st.selectbox(label='Frequência da movimentação: ', options=['','Singular (p.ex: jantar)', 'Múltipla Temporária (p.ex: parcelamento)', 'Múltipla Permanente (p. ex: cobrança de mensalidade)'])
    valor = st.number_input(label='Valor (R$):')
    instituicao_financeira = st.selectbox(label='Instituição Financeira (onde a quantia foi ou estava?)', options=['','Nubank', 'Inter', 'C6', 'PicPay', 'Hipercard', 'Cofre'])
    provedor = st.text_input(label='Provedor (quem foi o responsável pela movimentação? Nelogica, pai, mãe etc.):')
    descricao = st.text_input(label='Descrição:')

    data_cadastro = date.today()

    cadastrar = st.button('Cadastrar')

    if cadastrar:

        df = df.append({'Data Cadastro': data_cadastro,
                        'Data Financeira': data_financeira,
                        'Fluxo': fluxo,
                        'Frequência' :frequencia,
                        'Valor' : valor,
                        'Instituição Financeira' : instituicao_financeira,
                        'Provedor' : provedor,
                        'Descrição': descricao
                        },
                        ignore_index=True)

        df.to_csv('sheets/data.csv', index=False)

def selecionar_opcoes():

    opcoes_primarias = st.selectbox(
        label = 'O que você deseja fazer?',
        options = ('', 'Atualizar dados','Cadastrar uma movimentação', 'Excluir uma movimentação', 'Publicar dados'),
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

    index_para_excluir = st.text_input(label='Indique a ID da linha a ser excluída:', value='0')

    index_para_excluir = int(index_para_excluir)

    excluir = st.button('Excluir')

    if excluir:
        try:
            df = df.drop(index_para_excluir)
            df.to_csv('sheets/data.csv', index=False)
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
