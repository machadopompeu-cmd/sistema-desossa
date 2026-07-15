import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mentoria de Desossa - Tangará", layout="wide")

# --- CONEXÃO COM O BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
    # Tabela principal da Ação de Desossa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_acao TEXT,
            tipo_animal TEXT,
            peso_bruto REAL,
            preco_animal_kg REAL,
            ossos_muxiba REAL,
            quebra_nao_identificada REAL,
            exsudato_escorrimento REAL
        )
    """)
    # Tabela de cortes associados à ação
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acao_id INTEGER,
            nome_corte TEXT,
            qualidade TEXT,
            peso REAL,
            preco_venda REAL,
            FOREIGN KEY(acao_id) REFERENCES acoes(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("desossa_db.db")

# --- INTERFACE ---
st.title("🍖 Sistema de Mentoria de Desossa & Indicadores")
st.markdown("Replicador fiel do modelo de inteligência de custos da desossa.")

# Sidebar para Navegação
menu = st.sidebar.selectbox("Menu de Operações", ["Nova Desossa", "Histórico & Edição"])

if menu == "Nova Desossa":
    st.header("📋 Lançar Nova Ação de Desossa")
    
    col1, col2 = st.columns(2)
    with col1:
        data_acao = st.date_input("Data da Ação", datetime.date.today())
        tipo_animal = st.selectbox("Tipo de Desossa", ["QUARTO TRASEIRO", "QUARTO DIANTEIRO", "VACA CASADA", "BOI CASADO", "SUINO"])
        peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, value=100.0, step=0.1)
        preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, value=20.0, step=0.1)
        
    with col2:
        ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, value=15.0, step=0.1)
        quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, value=2.0, step=0.1)
        exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, value=0.0, step=0.1)

    st.subheader("🥩 Cortes do Lote")
    
    # Gerenciar cortes na sessão do Streamlit
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []
        
    with st.form("adicionar_corte"):
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        nome_corte = col_c1.text_input("Nome do Corte")
        qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"])
        peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, value=10.0, step=0.1)
        preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, value=30.0, step=0.1)
        
        submitted = st.form_submit_button("➕ Adicionar Corte")
        if submitted and nome_corte:
            st.session_state.cortes_temp.append({
                "nome_corte": nome_corte.upper(),
                "qualidade": qualidade,
                "peso": peso_corte,
                "preco_venda": preco_venda
            })
            st.success(f"Corte {nome_corte} adicionado!")

    # Exibe cortes adicionados atualmente
    if st.session_state.cortes_temp:
        df_temp = pd.DataFrame(st.session_state.cortes_temp)
        st.dataframe(df_temp)
        if st.button("Limpar Lista de Cortes"):
            st.session_state.cortes_temp = []
            st.rerun()

    # Botão para salvar ação completa
    if st.button("💾 Salvar Ação no Banco de Dados"):
        if not st.session_state.cortes_temp:
            st.error("Adicione pelo menos um corte antes de salvar a ação!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO acoes (data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(data_acao), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento))
            acao_id = cursor.lastrowid
            
            for c in st.session_state.cortes_temp:
                cursor.execute("""
                    INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda)
                    VALUES (?, ?, ?, ?, ?)
                """, (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                
            conn.commit()
            conn.close()
            st.success("🎉 Ação de Desossa salva com sucesso no banco de dados!")
            st.session_state.cortes_temp = []
            st.rerun()

elif menu == "Histórico & Edição":
    st.header("📂 Histórico de Desossas")
    
    conn = get_connection()
    df_acoes = pd.read_sql_query("SELECT * FROM acoes ORDER BY data_acao DESC", conn)
    conn.close()
    
    if df_acoes.empty:
        st.warning("Nenhum registro encontrado.")
    else:
        # Selecionar uma ação para visualização de indicadores e impressão
        opcoes = [f"ID: {row['id']} - {row['data_acao']} | {row['tipo_animal']}" for idx, row in df_acoes.iterrows()]
        selecionado = st.selectbox("Selecione um lote para visualizar os Indicadores e Fórmulas:", opcoes)
        
        id_selecionado = int(selecionado.split(" ")[1])
        acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
        
        # Carregar cortes
        conn = get_connection()
        df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
        conn.close()
        
        st.markdown("---")
        st.subheader(f"📊 Quadro de Indicadores - Lote #{id_selecionado}")
        
        # --- CÁLCULO DOS INDICADORES CONFORME A PLANILHA ---
        p_bruto = acao_row["peso_bruto"]
        p_comp_kg = acao_row["preco_animal_kg"]
        valor_total_compra = p_bruto * p_comp_kg
        
        total_vendas_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"] * df_cortes[df_cortes["qualidade"] == "OURO"]["preco_venda"])
        total_vendas_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"] * df_cortes[df_cortes["qualidade"] == "PRATA"]["preco_venda"])
        total_vendas_total = total_vendas_ouro + total_vendas_prata
        
        coeficiente = valor_total_compra / total_vendas_total if total_vendas_total > 0 else 0
        
        compra_ouro = total_vendas_ouro * coeficiente
        compra_prata = total_vendas_prata * coeficiente
        
        peso_desossado_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"])
        peso_desossado_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"])
        peso_desossado_total = peso_desossado_ouro + peso_desossado_prata
        
        # Custos Efetivos (Adicionando pequeno fator fixo de simulação das taxas de embalagem como no modelo 0.0003 do excel)
        custo_efetivo_ouro = compra_ouro + (total_vendas_ouro * 0.0001)
        custo_efetivo_prata = compra_prata + (total_vendas_prata * 0.0001)
        custo_efetivo_total = custo_efetivo_ouro + custo_efetivo_prata
        
        margem_r_ouro = total_vendas_ouro - custo_efetivo_ouro
        margem_r_prata = total_vendas_prata - custo_efetivo_prata
        margem_r_total = total_vendas_total - custo_efetivo_total
        
        margem_p_ouro = (margem_r_ouro / total_vendas_ouro) if total_vendas_ouro > 0 else 0
        margem_p_prata = (margem_r_prata / total_vendas_prata) if total_vendas_prata > 0 else 0
        margem_p_total = (margem_r_total / total_vendas_total) if total_vendas_total > 0 else 0
        
        markup_ouro = (total_vendas_ouro / custo_efetivo_ouro) - 1 if custo_efetivo_ouro > 0 else 0
        markup_prata = (total_vendas_prata / custo_efetivo_prata) - 1 if custo_efetivo_prata > 0 else 0
        markup_total = (total_vendas_total / custo_efetivo_total) - 1 if custo_efetivo_total > 0 else 0
        
        p_medio_compra_ouro = compra_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
        p_medio_compra_prata = compra_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
        p_medio_compra_total = valor_total_compra / peso_desossado_total if peso_desossado_total > 0 else 0
        
        # Exibição da Tabela de Indicadores Exatamente como no Excel
        indicadores_data = {
            "INDICADORES": [
                "PREÇO TOTAL/Compra", "PREÇO TOTAL/Venda", "Peso Desossado (KG)", 
                "COEFICIENTE", "Custo Efetivo Total", "Margem de Contribuição R$", 
                "Margem de Contribuição %", "Markup", "Preço Médio de Compra/KG"
            ],
            "OURO": [
                f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f}",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_ouro:.2f}", f"R$ {margem_r_ouro:.2f}",
                f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}"
            ],
            "PRATA": [
                f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f}",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_prata:.2f}", f"R$ {margem_r_prata:.2f}",
                f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}"
            ],
            "Total": [
                f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f}",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_total:.2f}", f"R$ {margem_r_total:.2f}",
                f"{margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}"
            ]
        }
        
        st.table(pd.DataFrame(indicadores_data).set_index("INDICADORES"))
        
        # Visualizar a tabela de cortes detalhada
        st.subheader("🥩 Cortes Detalhados deste Lote")
        df_cortes_calc = df_cortes.copy()
        df_cortes_calc["Valor Total Venda"] = df_cortes_calc["peso"] * df_cortes_calc["preco_venda"]
        df_cortes_calc["Preço de Custo / KG"] = df_cortes_calc["preco_venda"] * coeficiente
        df_cortes_calc["Preço de Custo Total"] = df_cortes_calc["Valor Total Venda"] * coeficiente
        df_cortes_calc["Lucro Bruto"] = df_cortes_calc["Valor Total Venda"] - df_cortes_calc["Preço de Custo Total"]
        
        st.dataframe(df_cortes_calc[["nome_corte", "qualidade", "peso", "preco_venda", "Valor Total Venda", "Preço de Custo / KG", "Preço de Custo Total", "Lucro Bruto"]])
        
        # Deletar Registro
        if st.button("🗑️ Excluir esta Ação de Desossa", key=f"del_{id_selecionado}"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM acoes WHERE id = {id_selecionado}")
            conn.commit()
            conn.close()
            st.success("Registro deletado com sucesso!")
            st.rerun()