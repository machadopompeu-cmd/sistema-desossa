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
        data_input = st.date_input("Data da Ação", datetime.date.today())
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

    # Se houver cortes adicionados temporariamente, exibe-os com botões de exclusão
    if st.session_state.cortes_temp:
        st.markdown("##### Gerenciar Cortes Adicionados:")
        for idx, c in enumerate(st.session_state.cortes_temp):
            col_ver, col_btn = st.columns([5, 1])
            col_ver.write(f"**{c['nome_corte']}** ({c['qualidade']}) - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}/KG")
            if col_btn.button("❌ Remover", key=f"rem_temp_{idx}"):
                st.session_state.cortes_temp.pop(idx)
                st.rerun()
                
        if st.button("Limpar Todos os Cortes"):
            st.session_state.cortes_temp = []
            st.rerun()

    if st.button("💾 Salvar Ação no Banco de Dados"):
        if not st.session_state.cortes_temp:
            st.error("Adicione pelo menos um corte antes de salvar a ação!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
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
        
        # Obter dados do banco
        acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
        conn = get_connection()
        df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
        conn.close()
        
        # --- SEÇÃO DE EDIÇÃO DA CARCAÇA ---
        with st.expander("📝 EDITAR DADOS GERAIS DA CARCAÇA"):
            st.warning("Altere os dados da carcaça abaixo e clique em 'Atualizar Dados' para salvar.")
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
                
            if st.button("💾 CONFIRMAR ATUALIZAÇÃO DA CARCAÇA"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE acoes 
                    SET data_acao = ?, tipo_animal = ?, peso_bruto = ?, preco_animal_kg = ?, ossos_muxiba = ?, quebra_nao_identificada = ?, exsudato_escorrimento = ?
                    WHERE id = ?
                """, (str(ed_data), ed_tipo, ed_p_bruto, ed_preco_animal, ed_ossos, ed_quebra, ed_exsudato, id_selecionado))
                conn.commit()
                conn.close()
                st.success("✅ Dados da carcaça atualizados com sucesso!")
                st.rerun()

        # --- GERENCIAMENTO INDIVIDUAL DE CADA CORTE ---
        with st.expander("🥩 GERENCIAR CORTES INDIVIDUALMENTE"):
            st.info("Aqui pode Editar ou Excluir cada corte deste lote individualmente:")
            for i, corte_row in df_cortes.iterrows():
                with st.container():
                    st.markdown(f"##### Corte: **{corte_row['nome_corte']}**")
                    col_c1, col_c2, col_c3, col_btn_salvar, col_btn_excluir = st.columns([2, 2, 2, 1, 1])
                    
                    c_qual = col_c1.selectbox("Qualidade", ["OURO", "PRATA"], index=["OURO", "PRATA"].index(corte_row["qualidade"]), key=f"c_qual_{corte_row['id']}")
                    c_peso = col_c2.number_input("Peso (KG)", value=float(corte_row["peso"]), step=0.001, format="%.3f", key=f"c_peso_{corte_row['id']}")
                    c_preco = col_c3.number_input("Preço (R$/KG)", value=float(corte_row["preco_venda"]), step=0.01, key=f"c_preco_{corte_row['id']}")
                    
                    if col_btn_salvar.button("💾 Salvar", key=f"save_c_{corte_row['id']}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE cortes 
                            SET qualidade = ?, peso = ?, preco_venda = ?
                            WHERE id = ?
                        """, (c_qual, c_peso, c_preco, corte_row["id"]))
                        conn.commit()
                        conn.close()
                        st.success(f"Corte {corte_row['nome_corte']} atualizado!")
                        st.rerun()
                        
                    if col_btn_excluir.button("🗑️ Excluir", key=f"del_c_{corte_row['id']}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM cortes WHERE id = ?", (corte_row["id"],))
                        conn.commit()
                        conn.close()
                        st.warning(f"Corte {corte_row['nome_corte']} removido!")
                        st.rerun()
                st.markdown("---")

        # --- RE-CÁLCULO DOS INDICADORES CONFORME A PLANILHA ---
        p_bruto = acao_row["peso_bruto"]
        p_comp_kg = acao_row["preco_animal_kg"]
        valor_total_compra = p_bruto * p_comp_kg
        
        # Deduções e Apuração do Lote
        ossos_val = acao_row["ossos_muxiba"] if acao_row["ossos_muxiba"] else 0.0
        quebra_val = acao_row["quebra_nao_identificada"] if acao_row["quebra_nao_identificada"] else 0.0
        exsudato_val = acao_row["exsudato_escorrimento"] if acao_row["exsudato_escorrimento"] else 0.0
        
        peso_final = p_bruto - ossos_val - quebra_val - exsudato_val
        total_quebra = ossos_val + quebra_val + exsudato_val
        
        # Função interna auxiliar para ocultar zeros na coluna de pesos (idêntico à imagem)
        def formatar_peso_visual(v):
            return f"{v:.3f}" if v > 0.0 else ""
        
        # --- TABELA DE APURAÇÃO DO ANIMAL (REPLICANDO EXATAMENTE A PRIMEIRA IMAGEM) ---
        st.subheader("📊 Apuração Geral do Lote")
        
        apuracao_data = {
            "Apuração do Lote": [
                "PESO BRUTO/KG", 
                "OSSOS/MUXIBA", 
                "QUEBRA NÃO IDENTIF", 
                "ESCORRIMENTO", 
                "Peso Final", 
                "TOTAL DE QUEBRA"
            ],
            "Peso (KG)": [
                formatar_peso_visual(p_bruto), 
                formatar_peso_visual(ossos_val), 
                formatar_peso_visual(quebra_val), 
                formatar_peso_visual(exsudato_val), 
                formatar_peso_visual(peso_final), 
                formatar_peso_visual(total_quebra)
            ],
            "R$": [
                f"R$ {valor_total_compra:.2f}", 
                "-", 
                "-", 
                "-", 
                f"R$ {valor_total_compra:.2f}", 
                "-"
            ],
            "Porcentagem": [
                "100,00%", 
                f"{(ossos_val / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", 
                f"{(quebra_val / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", 
                f"{(exsudato_val / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", 
                f"{(peso_final / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", 
                f"{(total_quebra / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%"
            ]
        }
        
        st.table(pd.DataFrame(apuracao_data).set_index("Apuração do Lote"))

        # --- CÁLCULO DOS INDICADORES FINANCEIROS ---
        total_vendas_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"] * df_cortes[df_cortes["qualidade"] == "OURO"]["preco_venda"])
        total_vendas_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"] * df_cortes[df_cortes["qualidade"] == "PRATA"]["preco_venda"])
        total_vendas_total = total_vendas_ouro + total_vendas_prata
        
        coeficiente = valor_total_compra / total_vendas_total if total_vendas_total > 0 else 0
        
        compra_ouro = total_vendas_ouro * coeficiente
        compra_prata = total_vendas_prata * coeficiente
        
        peso_desossado_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"])
        peso_desossado_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"])
        peso_desossado_total = peso_desossado_ouro + peso_desossado_prata
        
        # Custo Efetivo Total
        custo_efetivo_total_ouro = 0
        custo_efetivo_total_prata = 0
        
        for i, row in df_cortes.iterrows():
            peso = row['peso']
            p_venda = row['preco_venda']
            p_custo_kg = p_venda * coeficiente
            
            # Ajuste exato das fórmulas do Excel (Bisteca multiplica pelo preço; outros pelo peso)
            if i == 0:
                embalagem = 0.0003 * p_venda
            else:
                embalagem = 0.0003 * peso
                
            custo_efetivo_kg = p_custo_kg + embalagem
            custo_efetivo_total = peso * custo_efetivo_kg
            
            if row['qualidade'] == "OURO":
                custo_efetivo_total_ouro += custo_efetivo_total
            else:
                custo_efetivo_total_prata += custo_efetivo_total
                
        custo_efetivo_total_geral = custo_efetivo_total_ouro + custo_efetivo_total_prata
        
        # Margens de Contribuição
        margem_r_ouro = total_vendas_ouro - custo_efetivo_total_ouro
        margem_r_prata = total_vendas_prata - custo_efetivo_total_prata
        margem_r_total = total_vendas_total - custo_efetivo_total_geral
        
        margem_p_ouro = (margem_r_ouro / total_vendas_ouro) if total_vendas_ouro > 0 else 0
        margem_p_prata = (margem_r_prata / total_vendas_prata) if total_vendas_prata > 0 else 0
        margem_p_total = (margem_r_total / total_vendas_total) if total_vendas_total > 0 else 0
        
        # Markup
        markup_ouro = (total_vendas_ouro / custo_efetivo_total_ouro) - 1 if custo_efetivo_total_ouro > 0 else 0
        markup_prata = (total_vendas_prata / custo_efetivo_total_prata) - 1 if custo_efetivo_total_prata > 0 else 0
        markup_total = (total_vendas_total / custo_efetivo_total_geral) - 1 if custo_efetivo_total_geral > 0 else 0
        
        # Preços Médios de Compra e Venda
        p_medio_compra_ouro = compra_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
        p_medio_compra_prata = compra_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
        p_medio_compra_total = valor_total_compra / peso_desossado_total if peso_desossado_total > 0 else 0
        
        p_medio_compra_com_ouro = custo_efetivo_total_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
        p_medio_compra_com_prata = custo_efetivo_total_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
        p_medio_compra_com_total = custo_efetivo_total_geral / peso_desossado_total if peso_desossado_total > 0 else 0
        
        p_medio_venda_ouro = total_vendas_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
        p_medio_venda_prata = total_vendas_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
        p_medio_venda_total = total_vendas_total / peso_desossado_total if peso_desossado_total > 0 else 0
        
        # --- EXIBIÇÃO DO QUADRO DE INDICADORES ---
        st.subheader(f"📊 Quadro de Indicadores - Lote #{id_selecionado}")
        
        indicadores_data = {
            "INDICADORES": [
                "PREÇO TOTAL/Compra Sem Custos Variáveis", 
                "PREÇO TOTAL/Venda", 
                "Peso Desossado", 
                "COEFICIENTE", 
                "Custo Efetivo Total", 
                "Margem de Contribuição R$", 
                "Margem de Contribuição %", 
                "Markup", 
                "Preço médio de Compra/KG SEM-Custo Variável",
                "Preço médio de Compra/KG COM-Custo Variável",
                "Preço médio de Venda/KG"
            ],
            "OURO": [
                f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f}",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_ouro:.2f}", f"R$ {margem_r_ouro:.2f}",
                f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}",
                f"R$ {p_medio_compra_com_ouro:.2f}", f"R$ {p_medio_venda_ouro:.2f}"
            ],
            "PRATA": [
                f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f}",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_prata:.2f}", f"R$ {margem_r_prata:.2f}",
                f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}",
                f"R$ {p_medio_compra_com_prata:.2f}", f"R$ {p_medio_venda_prata:.2f}"
            ],
            "Total": [
                f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f}",
                f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_geral:.2f}", f"R$ {margem_r_total:.2f}",
                f"{margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}",
                f"R$ {p_medio_compra_com_total:.2f}", f"R$ {p_medio_venda_total:.2f}"
            ]
        }
        
        st.table(pd.DataFrame(indicadores_data).set_index("INDICADORES"))
        
        # --- TABELA DE RENDIMENTO E MARGENS COM LINHA DE SOMA ---
        st.subheader("📝 Detalhamento de Rendimento e Margens")
        
        df_cortes_calc = df_cortes.copy()
        df_cortes_calc["Valor Total Venda"] = df_cortes_calc["peso"] * df_cortes_calc["preco_venda"]
        df_cortes_calc["Preço de Custo / KG"] = df_cortes_calc["preco_venda"] * coeficiente
        df_cortes_calc["Preço de Custo Total"] = df_cortes_calc["Valor Total Venda"] * coeficiente
        df_cortes_calc["Lucro Bruto"] = df_cortes_calc["Valor Total Venda"] - df_cortes_calc["Preço de Custo Total"]
        df_cortes_calc["Rendimento %"] = (df_cortes_calc["peso"] / p_bruto) * 100 if p_bruto > 0 else 0
        
        # Renomeação de colunas para exibição amigável
        df_formatado = df_cortes_calc.rename(columns={
            "nome_corte": "Corte",
            "qualidade": "Qualidade",
            "peso": "Peso (KG)",
            "preco_venda": "Preço Venda (R$/KG)",
            "Valor Total Venda": "Faturamento Total",
            "Preço de Custo / KG": "Custo por KG",
            "Preço de Custo Total": "Custo Total",
            "Lucro Bruto": "Margem Bruta (R$)",
            "Rendimento %": "Rendimento %"
        })
        
        # Filtrar as colunas corretas para exibição
        cols_exibicao = ["Corte", "Qualidade", "Peso (KG)", "Preço Venda (R$/KG)", "Faturamento Total", "Custo por KG", "Custo Total", "Margem Bruta (R$)", "Rendimento %"]
        df_final = df_formatado[cols_exibicao].copy()
        
        # --- CÁLCULO DA SOMA DAS COLUNAS NUMÉRICAS ---
        total_peso = df_final["Peso (KG)"].sum()
        total_faturamento = df_final["Faturamento Total"].sum()
        total_custo_total = df_final["Custo Total"].sum()
        total_margem_bruta = df_final["Margem Bruta (R$)"].sum()
        total_rendimento = df_final["Rendimento %"].sum()
        
        # Criar linha de Totais de forma limpa
        linha_total = pd.DataFrame([{
            "Corte": "TOTAL SOMA",
            "Qualidade": "",
            "Peso (KG)": total_peso,
            "Preço Venda (R$/KG)": None,
            "Faturamento Total": total_faturamento,
            "Custo por KG": None,
            "Custo Total": total_custo_total,
            "Margem Bruta (R$)": total_margem_bruta,
            "Rendimento %": total_rendimento
        }])
        
        df_com_total = pd.concat([df_final, line_total if 'line_total' in locals() else linha_total], ignore_index=True)
        
        # Renderização visual com tratamento das colunas de preços por KG no Total
        st.dataframe(df_com_total.style.format({
            "Peso (KG)": "{:.3f}",
            "Preço Venda (R$/KG)": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
            "Faturamento Total": "R$ {:.2f}",
            "Custo por KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
            "Custo Total": "R$ {:.2f}",
            "Margem Bruta (R$)": "R$ {:.2f}",
            "Rendimento %": "{:.2f}%"
        }))
        
        if st.button("🗑️ Excluir esta Ação de Desossa Completa", key=f"del_{id_selecionado}"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM acoes WHERE id = {id_selecionado}")
            conn.commit()
            conn.close()
            st.success("Registro completo deletado com sucesso!")
            st.rerun()
