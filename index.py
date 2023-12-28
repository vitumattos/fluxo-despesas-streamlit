import streamlit as st  # python -m streamlit run <filename.py>
from pathlib import Path
from datetime import datetime
import pandas as pd

import plotly.graph_objects as go

cwd = Path(__file__).parent
PASTA_DATABASE = cwd / 'database'

st.set_page_config(
    page_title='Controle de Finanças',
    layout='wide'
)


def inicializa():
    if not 'pagina_dash_financa' in st.session_state:
        st.session_state['pagina_dash_financa'] = "home"
    if not 'descricao' in st.session_state:
        st.session_state['descricao'] = None
    if not 'valor' in st.session_state:
        st.session_state['valor'] = None
    if not 'df' in st.session_state:
        try:
            st.session_state['df'] = pd.read_csv(
                PASTA_DATABASE/'df.csv', sep=';', index_col=0)
        except:
            _add_modal()


def mudar_pagina(nome_pagina):
    st.session_state['pagina_dash_financa'] = nome_pagina


def numero_para_nome_mes(numero):
    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    nome_mes = meses.get(numero, "Mês inválido")
    return nome_mes
# ================= Home ================ #


def pag_home():
    df = st.session_state['df']

    # == Filtro ==
    st.sidebar.divider()
    st.sidebar.subheader('Filtrar Lançamento')
    st.sidebar.caption('EXTRA')
    col1, col2 = st.sidebar.columns(2)
    check_recorrente = col1.checkbox('Recorrente')
    check_credito = col2.checkbox('Crédito', value=True)
    mes_para_analisar = st.sidebar.multiselect(
        label='***Período da Análise***',
        options=[x for x in range(1, 13)],
        default=[datetime.today().month],
        format_func=lambda mes: numero_para_nome_mes(mes),
        placeholder='Selecione o(s) mes/mêses'
    )
    categoria_para_analisar = st.sidebar.multiselect(
        label='***Categoria da Análise***',
        options=df['Categoria'].unique(),
        default=[df['Categoria'].unique()[i]
                 for i, x in enumerate(df['Categoria'].unique())],
        placeholder='Selecione os categorias'
    )

    # == Logica dos dados ==
    df['Data'] = pd.to_datetime(df['Data'], format='mixed')
    df['_mes'] = df['Data'].apply(lambda x: x.month)

    if mes_para_analisar == []:
        mes_atual = datetime.today().month
        dff = df[df['_mes'] == mes_atual]
    else:
        dff = df[df['_mes'].isin(mes_para_analisar)]

    if categoria_para_analisar == []:
        pass
    else:
        dff = dff[dff['Categoria'].isin(categoria_para_analisar)]

    if check_recorrente:
        dff = dff[dff['Fixo'] == 1]
    if not check_credito:
        dff = dff[(dff['Credito'] != 1)]

    # == Variaveis ==
    SALDO = dict(dff.groupby(['Ordem'])['Valor'].sum())
    RESULTADO = round(SALDO['RECEITA'] - SALDO['DESPESA'], 2)

    # == Header ==
    colll1, colll2, colll3 = st.columns(3)
    colll1.metric(label=' ', label_visibility='hidden',
                  value='Saldo', delta=f'R${RESULTADO}')
    colll2.metric(label=' ', label_visibility='hidden',
                  value='Receitas', delta=f'R${SALDO["RECEITA"]}')
    colll3.metric(label=' ', label_visibility='hidden',
                  value='Despesas', delta=f'-R${SALDO["DESPESA"]}')

    # == graph lançamentos ==
    DF_RECEITA = dff[dff['Ordem'] == 'RECEITA']
    DF_DESPESA = dff[dff['Ordem'] == 'DESPESA']
    DF_DESPESA['Valor'] = -DF_DESPESA['Valor']

    fig = pd.concat([DF_RECEITA, DF_DESPESA])
    fig = fig.sort_values('Data')
    fig.index = fig['Data']
    fig = fig.groupby(by=fig.index)['Valor'].sum()
    st.area_chart(fig.cumsum())

    # == graph Roscas ==
    DF_DESPESA['Valor'] = -DF_DESPESA['Valor']
    colors = ['gold', 'mediumturquoise', 'darkorange', 'lightgreen']
    col1, col2 = st.columns(2)

    fig1 = go.Figure(
        data=[go.Pie(labels=DF_DESPESA.Categoria, values=DF_DESPESA.Valor, hole=0.3)])
    fig1.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20,
                       marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    fig2 = go.Figure(
        data=[go.Pie(labels=DF_RECEITA.Categoria, values=DF_RECEITA.Valor, hole=0.3)])
    fig2.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20,
                       marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    col1.subheader('Despesas')
    col1.plotly_chart(fig1)
    col2.subheader('Receitas')
    col2.plotly_chart(fig2)

# ================= Extrato ================== #


def pag_extrato():
    df = st.session_state['df']

    st.title('Extrato')
    coll1, coll2, coll3, coll4, coll5 = st.columns(5)
    coll1.markdown(f'***{df.columns[0]}***')
    coll2.markdown(f'***{df.columns[1]}***')
    coll3.markdown(f'***{df.columns[2]}***')
    coll4.markdown(f'***{df.columns[3]}***')
    coll5.markdown(f'***{df.columns[4]}***')
    st.divider()
    for _, row in df.iterrows():
        coll1, coll2, coll3, coll4, coll5 = st.columns(5)
        coll1.write(row['Ordem'])
        coll2.write(row['Descrição'])
        coll3.write(row['Valor'])
        coll4.write(row['Categoria'])
        coll5.write(row['Data'])


# ================= MODAL ================== #


def pag_modal():
    descricao_atual = st.session_state['descricao']
    valor_atual = st.session_state['valor']
    df = st.session_state['df']
    st.title("RECEITA/DESPESA")

    ordem = st.radio(' ', ["RECEITA", "DESPESA"],
                     horizontal=True, label_visibility='hidden')

    col1, col2 = st.columns(2)
    descricao = col1.text_input(
        label='Descrição:',
        placeholder='Ex.: Salario, Gasolina...',
        value=descricao_atual
    )
    valor = col2.number_input(
        label='Valor',
        value=valor_atual,
        placeholder="Ex.: R$ 2.000,00",
        min_value=0.00,
        step=0.01
    )
    col1, col2, col3 = st.columns(3)
    period = col1.date_input(
        'Data', datetime.today(), format='DD/MM/YYYY')
    col2.caption('Extra')
    credito = col2.checkbox('Crédito')
    recorrente = col2.checkbox('Recorrente')
    if ordem == 'RECEITA':
        categoria = col3.selectbox(
            label='Categoria',  options=['Salário', 'Transporte', 'Comissão'])
    else:
        categoria = col3.selectbox(
            label='Categoria',  options=['Estudo', 'Transporte', 'Casa', 'Outros', 'Alimentação', 'Skin', 'Investimento','Lazer'])

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.button('Limpar', use_container_width=True, on_click=_limpar_modal)

    col4.button('Adicionar', use_container_width=True,
                on_click=_add_modal)

    st.session_state['descricao'] = descricao
    st.session_state['valor'] = valor
    st.session_state['period'] = period
    st.session_state['credito'] = credito
    st.session_state['recorrente'] = recorrente
    st.session_state['categoria'] = categoria
    st.session_state['ordem'] = ordem


def _limpar_modal():
    st.session_state['descricao'] = None
    st.session_state['valor'] = None
    st.session_state['period'] = datetime.today()
    st.session_state['credito'] = False
    st.session_state['recorrente'] = False

    df = st.session_state['df']

    df['Data'] = pd.to_datetime(df['Data'], format='mixed')
    df = df.sort_values('Data', ascending=False, ignore_index=True)
    df.to_csv(PASTA_DATABASE/'df.csv', sep=';')
    st.session_state['df'] = df
    mudar_pagina('modal')


def _add_modal():

    if 'df.csv' not in [x.name for x in PASTA_DATABASE.glob('*')]:
        df = pd.DataFrame(
            columns=['Ordem', 'Descrição', 'Valor', 'Categoria', 'Data', 'Fixo', 'Credito'])
        df.to_csv(PASTA_DATABASE/'df.csv', sep=';')
        st.session_state['df'] = df
    else:
        if st.session_state['valor'] != None and st.session_state['descricao'] != None:
            df = st.session_state['df']

            new_line = {
                'Ordem': st.session_state['ordem'],
                'Valor': st.session_state['valor'],
                'Fixo': st.session_state['recorrente'],
                'Credito': st.session_state['credito'],
                'Data': st.session_state['period'],
                'Categoria': st.session_state['categoria'],
                'Descrição': st.session_state['descricao']
            }
            df.loc[len(df)] = new_line
            df['Data'] = pd.to_datetime(df['Data'], format='mixed')
            df = df.sort_values('Data', ascending=False, ignore_index=True)
            df.to_csv(PASTA_DATABASE/'df.csv', sep=';')
            st.session_state['df'] = df
            _limpar_modal()

# ================= Start ================== #


def main():

    inicializa()
    st.sidebar.button('Home', use_container_width=True,
                      on_click=mudar_pagina, args=('home',))
    st.sidebar.button('Extrato', use_container_width=True,
                      on_click=mudar_pagina, args=('extrato',))
    st.sidebar.button('ADD/REMOVE', use_container_width=True,
                      on_click=mudar_pagina, args=('modal',))

    if st.session_state['pagina_dash_financa'] == 'home':
        pag_home()
    elif st.session_state['pagina_dash_financa'] == 'extrato':
        pag_extrato()
    elif st.session_state['pagina_dash_financa'] == 'modal':
        pag_modal()


if __name__ == '__main__':
    main()
