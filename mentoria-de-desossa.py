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
st.markdown("Replicador fiel do modelo de inteligência de custos da desossa com edição de dados.")

# Sidebar para Navegação
menu = st.sidebar.selectbox("Menu de Operações", ["Nova Desossa", "Histórico & Edição"])

if menu == "Nova Desossa":
    st.header("📋 Lançar Nova Ação de Desossa")
    
    col1, col2 = st.columns(2)
    with col1:
        data_input = st.date_input("Data da Ação", datetime.date.today())
        # Formatando para exibição em formato BR
        data_acao_br = data_input.strftime("%d/%m/%Y")
        st.write(f"Data selecionada: **{data_acao_br}**")
        
        tipo_animal = st.selectbox("Tipo de Desossa", ["QUARTO TRASEIRO", "QUARTO DIANTEIRO", "VACA CASADA", "BOI CASADO", "SUINO"])
        peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, value=178.000, step=0.001, format="%.3f")
        preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, value=24.00, step=0.01)
        
    with col2:
        ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, value=28.022, step=0.001, format="%.3f")
        quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, value=2.360, step=0.001, format="%.3f")
        exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, value=0.000, step=0.001, format="%.3f")

    st.subheader("🥩 Cortes do Lote")
    
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []
        
    with st.form("adicionar_corte"):
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        nome_corte = col_c1.text_input("Nome do Corte")
        qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"])
        peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, value=10.000, step=0.001, format="%.3f")
        preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, value=30.00, step=0.01)
        
        submitted = st.form_submit_button("➕ Adicionar Corte")
        if submitted and nome_corte:
            st.session_state.cortes_temp.append({
                "nome_corte": nome_corte.upper(),
                "qualidade": qualidade,
                "peso": peso_corte,
                "preco_venda": preco_venda
            })
            st.success(f"Corte {nome_corte.upper()} adicionado!")

    if st.session_state.cortes_temp:
        df_temp = pd.DataFrame(st.session_state.cortes_temp)
        st.dataframe(df_temp.style.format({"peso": "{:.3f}", "preco_venda": "R$ {:.2f}"}))
        if st.button("Limpar Lista de Cortes"):
            st.session_state.cortes_temp = []
            st.rerun()

    if st.button("💾 Salvar Ação no Banco de Dados"):
        if not st.session_state.cortes_temp:
            st.error("Adicione pelo menos um corte antes de salvar a ação!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            # Salvamos no banco como string YYYY-MM-DD
            cursor.execute("""
                INSERT INTO acoes (data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento))
            acao_id = cursor.lastrowid
            
            for c in st.session_state.cortes_temp:
                cursor.execute("""
                    INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda)
                    VALUES (?, ?, ?, ?, ?)
                """, (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                
            conn.commit()
            conn.close()
            st.success("🎉 Ação de Desossa salva com sucesso!")
            st.session_state.cortes_temp = []
            st.rerun()

elif menu == "Histórico & Edição":
    st.header("📂 Histórico & Edição de Desossas")
    
    conn = get_connection()
    df_acoes = pd.read_sql_query("SELECT * FROM acoes ORDER BY data_acao DESC", conn)
    conn.close()
    
    if df_acoes.empty:
        st.warning("Nenhum registro de desossa encontrado no banco de dados.")
    else:
        # Criando as opções de seleção exibindo a data formatada em DD/MM/AAAA
        opcoes_map = {}
        opcoes_lista = []
        for idx, row in df_acoes.iterrows():
            data_original = datetime.datetime.strptime(row['data_acao'], "%Y-%m-%d").date()
            data_br = data_original.strftime("%d/%m/%Y")
            label = f"ID: {row['id']} - {data_br} | {row['tipo_animal']}"
            opcoes_map[label] = row['id']
            opcoes_lista.append(label)
            
        selecionado = st.selectbox("Selecione um lote para visualizar, editar ou imprimir:", opcoes_lista)
        id_selecionado = opcoes_map[selecionado]
        
        # Obter dados atuais do banco
        acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
        conn = get_connection()
        df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
        conn.close()
        
        # --- SEÇÃO DE EDIÇÃO DOS DADOS ---
        with st.expander("📝 EDITAR DADOS DESTE LOTE"):
            st.warning("Altere os dados abaixo e clique em 'Atualizar Dados' para salvar as modificações.")
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                ed_data = st.date_input("Editar Data", datetime.datetime.strptime(acao_row["data_acao"], "%Y-%m-%d").date(), key="ed_data")
                ed_tipo = st.selectbox("Editar Tipo", ["QUARTO TRASEIRO", "QUARTO DIANTEIRO", "VACA CASADA", "BOI CASADO", "SUINO"], index=["QUARTO TRASEIRO", "QUARTO DIANTEIRO", "VACA CASADA", "BOI CASADO", "SUINO"].index(acao_row["tipo_animal"]), key="ed_tipo")
                ed_p_bruto = st.number_input("Editar Peso Bruto (KG)", value=float(acao_row["peso_bruto"]), step=0.001, format="%.3f", key="ed_p_bruto")
                ed_preco_animal = st.number_input("Editar Preço Animal (R$/KG)", value=float(acao_row["preco_animal_kg"]), step=0.01, key="ed_preco_animal")
            with col_ed2:
                ed_ossos = st.number_input("Editar Ossos/Muxiba (KG)", value=float(acao_row["ossos_muxiba"]), step=0.001, format="%.3f", key="ed_ossos")
                ed_quebra = st.number_input("Editar Quebra Não Identificada (KG)", value=float(acao_row["quebra_nao_identificada"]), step=0.001, format="%.3f", key="ed_quebra")
                ed_exsudato = st.number_input("Editar Exsudato/Escorrimento (KG)", value=float(acao_row["exsudato_escorrimento"]), step=0.001, format="%.3f", key="ed_exsudato")
            
            st.markdown("##### Editar Cortes Associados")
            cortes_editados_lista = []
            for i, corte_row in df_cortes.iterrows():
                st.markdown(f"**Corte: {corte_row['nome_corte']}**")
                c_col1, c_col2, c_col3 = st.columns(3)
                c_qual = c_col1.selectbox("Qualidade", ["OURO", "PRATA"], index=["OURO", "PRATA"].index(corte_row["qualidade"]), key=f"c_qual_{corte_row['id']}")
                c_peso = c_col2.number_input("Peso (KG)", value=float(corte_row["peso"]), step=0.001, format="%.3f", key=f"c_peso_{corte_row['id']}")
                c_preco = c_col3.number_input("Preço de Venda (R$/KG)", value=float(corte_row["preco_venda"]), step=0.01, key=f"c_preco_{corte_row['id']}")
                cortes_editados_lista.append({
                    "id": corte_row["id"],
                    "nome_corte": corte_row["nome_corte"],
                    "qualidade": c_qual,
                    "peso": c_peso,
                    "preco_venda": c_preco
                })
                
            if st.button("💾 CONFIRMAR E SALVAR EDIÇÃO"):
                conn = get_connection()
                cursor = conn.cursor()
                # Atualizar tabela principal
                cursor.execute("""
                    UPDATE acoes 
                    SET data_acao = ?, tipo_animal = ?, peso_bruto = ?, preco_animal_kg = ?, ossos_muxiba = ?, quebra_nao_identificada = ?, exsudato_escorrimento = ?
                    WHERE id = ?
                """, (str(ed_data), ed_tipo, ed_p_bruto, ed_preco_animal, ed_ossos, ed_quebra, ed_exsudato, id_selecionado))
                
                # Atualizar cortes
                for corte_edt in cortes_editados_lista:
                    cursor.execute("""
                        UPDATE cortes 
                        SET qualidade = ?, peso = ?, preco_venda = ?
                        WHERE id = ?
                    """, (corte_edt["qualidade"], corte_edt["peso"], corte_edt["preco_venda"], corte_edt["id"]))
                
                conn.commit()
                conn.close()
                st.success("✅ Lote e cortes atualizados com sucesso no banco de dados!")
                st.rerun()

        # --- RE-CÁLCULO DOS INDICADORES CONFORME A PLANILHA REVISADA ---
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
        
        # Custos Variáveis (Ex: Embalagem fixa de 0.0003 ou 0.03% conforme modelo de faturamento de vendas)
        custo_efetivo_ouro = compra_ouro + (total_vendas_ouro * 0.0003)
        custo_efetivo_prata = compra_prata + (total_vendas_prata * 0.0003)
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
        
        # --- EXIBIÇÃO DA TABELA DE INDICADORES FIEL ---
        st.markdown("---")
        st.subheader(f"📊 Quadro de Indicadores - Lote #{id_selecionado}")
        
        indicadores_data = {
            "INDICADORES": [
                "PREÇO TOTAL/Compra Sem Custos Variáveis", "PREÇO TOTAL/Venda", "Peso Desossado", 
                "COEFICIENTE", "Custo Efetivo Total", "Margem de Contribuição R$", 
                "Margem de Contribuição %", "Markup", "Preço médio de Compra/KG SEM-Custo Variável"
            ],
            "OURO": [
                f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f} KG",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_ouro:.2f}", f"R$ {margem_r_ouro:.2f}",
                f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}"
            ],
            "PRATA": [
                f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f} KG",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_prata:.2f}", f"R$ {margem_r_prata:.2f}",
                f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}"
            ],
            "Total": [
                f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f} KG",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_total:.2f}", f"R$ {margem_r_total:.2f}",
                f"{margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}"
            ]
        }
        
        st.table(pd.DataFrame(indicadores_data).set_index("INDICADORES"))
        
        # Tabela Detalhada de Cortes para Impressão
        st.subheader("📝 Detalhamento de Rendimento e Margens")
        df_cortes_calc = df_cortes.copy()
        df_cortes_calc["Valor Total Venda"] = df_cortes_calc["peso"] * df_cortes_calc["preco_venda"]
        df_cortes_calc["Preço de Custo / KG"] = df_cortes_calc["preco_venda"] * coeficiente
        df_cortes_calc["Preço de Custo Total"] = df_cortes_calc["Valor Total Venda"] * coeficiente
        df_cortes_calc["Lucro Bruto"] = df_cortes_calc["Valor Total Venda"] - df_cortes_calc["Preço de Custo Total"]
        df_cortes_calc["Rendimento %"] = (df_cortes_calc["peso"] / p_bruto) * 100
        
        # Formatando a tabela do usuário final
        df_formatado = df_cortes_calc.rename(columns={
            "nome_corte": "Corte",
            "qualidade": "Qualidade",
            "peso": "Peso (KG)",
            "preco_venda": "Preço Venda (R$/KG)",
            "Valor Total Venda": "Faturamento Total",
            "Preço de Custo / KG": "Custo por KG",
            "Preço de Custo Total": "Custo Total",
            "Lucro Bruto": "Margem Bruta (R$)"
        })
        
        st.dataframe(df_formatado[["Corte", "Qualidade", "Peso (KG)", "Preço Venda (R$/KG)", "Faturamento Total", "Custo por KG", "Custo Total", "Margem Bruta (R$)", "Rendimento %"]].style.format({
            "Peso (KG)": "{:.3f}",
            "Preço Venda (R$/KG)": "R$ {:.2f}",
            "Faturamento Total": "R$ {:.2f}",
            "Custo por KG": "R$ {:.2f}",
            "Custo Total": "R$ {:.2f}",
            "Margem Bruta (R$)": "R$ {:.2f}",
            "Rendimento %": "{:.2f}%"
        }))
        
        # Deletar Registro
        if st.button("🗑️ Excluir esta Ação de Desossa", key=f"del_{id_selecionado}"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM acoes WHERE id = {id_selecionado}")
            conn.commit()
            conn.close()
            st.success("Registro deletado com sucesso!")
            st.rerun()
