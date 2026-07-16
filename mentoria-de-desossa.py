import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO VISUAL DA PÁGINA ---
st.set_page_config(page_title="Gestão de Desossa - Renato Frigotudo", layout="wide")

# --- 2. BANCO DE DADOS INTELIGENTE (MULTI-EMPRESA) ---
def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
    
    # Tabela para guardar as empresas parceiras cadastradas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    
    # Tabela de desossa vinculada à empresa dona dos dados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            data_acao TEXT,
            tipo_animal TEXT,
            peso_bruto REAL,
            preco_animal_kg REAL,
            ossos_muxiba REAL,
            quebra_nao_identificada REAL,
            exsudato_escorrimento REAL,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de cortes vinculada a cada desossa
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

# --- 3. CABEÇALHO COM ESTILO PROFISSIONAL ---
def exibir_cabecalho(nome_empresa="RENATO FRIGOTUDO & ASSOCIADOS"):
    col_logo, col_info = st.columns([1, 4])
    
    with col_logo:
        # Carrega a logo se ela existir no GitHub/Pasta local
        if os.path.exists("logo_renato.png"):
            st.image("logo_renato.png", width=110)
        else:
            st.markdown("### 🍖 [LOGO]")
            
    with col_info:
        st.markdown(
            f"""
            <div style="padding-top: 10px;">
                <h1 style="margin: 0; color: #1C3D5A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 26px; font-weight: bold; letter-spacing: 1px;">
                    {nome_empresa.upper()}
                </h1>
                <p style="margin: 0; color: #555555; font-size: 15px; font-weight: 500;">
                    Rua Paraíso, nº 514 • Pompéu/MG
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

# --- 4. CONTROLE DE SESSÃO (CONTA CONECTADA) ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False # Define se o utilizador atual é o administrador

# --- 5. TELA DE ACESSO (LOGIN CENTRALIZADO COM CABEÇALHO) ---
if not st.session_state.logado:
    # Exibe o cabeçalho oficial diretamente na tela de login!
    exibir_cabecalho("RENATO FRIGOTUDO & ASSOCIADOS")
    
    st.title("🔒 Portal de Acesso - Gestão de Desossa")
    
    with st.form("form_login"):
        st.subheader("Login de Acesso")
        campo_login = st.text_input("Usuário / Login")
        campo_senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar no Sistema")
        
        if btn_entrar:
            # 1. Verifica primeiro se é o Administrador Geral
            if campo_login == "admin" and campo_senha == "renato123":
                st.session_state.logado = True
                st.session_state.empresa_id = 0
                st.session_state.empresa_nome = "Administrador Geral"
                st.session_state.e_admin = True
                st.success("Acesso administrativo concedido!")
                st.rerun()
            else:
                # 2. Se não for admin, consulta as empresas cadastradas no banco de dados
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome FROM empresas WHERE login = ? AND senha = ?", (campo_login, campo_senha))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.logado = True
                    st.session_state.empresa_id = user[0]
                    st.session_state.empresa_nome = user[1]
                    st.session_state.e_admin = False
                    st.success(f"Login realizado com sucesso como: {user[1]}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

else:
    # --- 6. MENU LATERAL DO USUÁRIO LOGADO ---
    st.sidebar.markdown(f"**Ativo como:**\n{st.session_state.empresa_nome}")
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.session_state.empresa_id = None
        st.session_state.empresa_nome = ""
        st.session_state.e_admin = False
        st.rerun()

    # Cabeçalho integrado de acordo com o utilizador ativo
    if st.session_state.e_admin:
        exibir_cabecalho("PAINEL ADMINISTRATIVO")
    else:
        exibir_cabecalho(st.session_state.empresa_nome)
    
    # Definição do menu lateral baseado nas permissões (Admin vs Usuário Comum)
    if st.session_state.e_admin:
        menu = st.sidebar.selectbox("Menu Administrativo", ["Cadastrar Empresa", "Visualizar Todas as Empresas"])
    else:
        menu = st.sidebar.selectbox("Menu de Operações", ["Nova Desossa", "Histórico & Edição"])

    # ==================== TELAS EXCLUSIVAS DO ADMINISTRADOR ====================
    if st.session_state.e_admin:
        if menu == "Cadastrar Empresa":
            st.header("📝 Registar Nova Empresa Parceira")
            st.info("Utilize este formulário oficial para cadastrar novos frigoríficos e marcas parceiras no sistema.")
            
            with st.form("form_cadastro_admin"):
                novo_nome = st.text_input("Nome Comercial (Ex: Frigorífico Renato)")
                novo_login = st.text_input("Crie um Nome de Usuário (Sem espaços)")
                nova_senha = st.text_input("Crie uma Senha de Acesso", type="password")
                btn_salvar_cadastro = st.form_submit_button("💾 Salvar Novo Cadastro")
                
                if btn_salvar_cadastro:
                    if not novo_nome or not novo_login or not nova_senha:
                        st.error("Preencha todos os campos para efetuar o registo!")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO empresas (nome, login, senha) VALUES (?, ?, ?)", (novo_nome, novo_login, nova_senha))
                            conn.commit()
                            conn.close()
                            st.success(f"🎉 Empresa '{novo_nome}' cadastrada com sucesso!")
                        except sqlite3.IntegrityError:
                            st.error("Este nome de usuário já está sendo usado por outra empresa.")
                            
        elif menu == "Visualizar Todas as Empresas":
            st.header("🏢 Empresas Cadastradas no Sistema")
            
            conn = get_connection()
            df_empresas = pd.read_sql_query("SELECT id as 'ID', nome as 'Nome Comercial', login as 'Usuário de Acesso' FROM empresas", conn)
            conn.close()
            
            if df_empresas.empty:
                st.warning("Ainda não existem empresas cadastradas no sistema.")
            else:
                st.dataframe(df_empresas, use_container_width=True)

    # ==================== TELAS DAS EMPRESAS PARCEIRAS ====================
    else:
        # ==================== TELA: NOVA DESOSSA ====================
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
                    st.success(f"Corte {nome_corte.upper()} adicionado temporariamente!")

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
                        INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (st.session_state.empresa_id, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento))
                    acao_id = cursor.lastrowid
                    
                    for c in st.session_state.cortes_temp:
                        cursor.execute("""
                            INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda)
                            VALUES (?, ?, ?, ?, ?)
                        """, (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                        
                    conn.commit()
                    conn.close()
                    st.success("🎉 Ação de Desossa salva com sucesso no seu perfil!")
                    st.session_state.cortes_temp = []
                    st.rerun()

        # ==================== TELA: HISTÓRICO & EDICÃO ====================
        elif menu == "Histórico & Edição":
            st.header("📂 Histórico & Edição de Desossas")
            
            conn = get_connection()
            df_acoes = pd.read_sql_query(f"SELECT * FROM acoes WHERE empresa_id = {st.session_state.empresa_id} ORDER BY data_acao DESC", conn)
            conn.close()
            
            if df_acoes.empty:
                st.warning("Ainda não existem desossas cadastradas para a sua empresa.")
            else:
                opcoes_map = {}
                opcoes_lista = []
                for idx, row in df_acoes.iterrows():
                    data_original = datetime.datetime.strptime(row['data_acao'], "%Y-%m-%d").date()
                    data_br = data_original.strftime("%d/%m/%Y")
                    label = f"ID: {row['id']} - {data_br} | {row['tipo_animal']}"
                    opcoes_map[label] = row['id']
                    opcoes_lista.append(label)
                    
                selecionado = st.selectbox("Selecione um lote para visualizar, editar ou exportar:", opcoes_lista)
                id_selecionado = opcoes_map[selecionado]
                
                acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
                conn = get_connection()
                df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
                conn.close()
                
                # --- SEÇÃO DE EDIÇÃO DA CARCAÇA ---
                with st.expander("📝 EDITAR DADOS GERAIS DA CARCAÇA"):
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
                            WHERE id = ? AND empresa_id = ?
                        """, (str(ed_data), ed_tipo, ed_p_bruto, ed_preco_animal, ed_ossos, ed_quebra, ed_exsudato, id_selecionado, st.session_state.empresa_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ Dados da carcaça updated com sucesso!")
                        st.rerun()

                # --- GERENCIAMENTO INDIVIDUAL DE CADA CORTE ---
                with st.expander("🥩 GERENCIAR CORTES INDIVIDUALMENTE"):
                    st.info("Altere ou remova cortes individuais deste lote:")
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

                # --- CÁLCULOS E MATEMÁTICA ---
                p_bruto = acao_row["peso_bruto"]
                p_comp_kg = acao_row["preco_animal_kg"]
                valor_total_compra = p_bruto * p_comp_kg
                tipo_animal_atual = acao_row["tipo_animal"]
                
                ossos_val = acao_row["ossos_muxiba"] if acao_row["ossos_muxiba"] else 0.0
                quebra_val = acao_row["quebra_nao_identificada"] if acao_row["quebra_nao_identificada"] else 0.0
                exsudato_val = acao_row["exsudato_escorrimento"] if acao_row["exsudato_escorrimento"] else 0.0
                
                peso_final = p_bruto - ossos_val - quebra_val - exsudato_val
                total_quebra = ossos_val + quebra_val + exsudato_val
                
                def formatar_peso_visual(v):
                    return f"{v:.3f}" if v > 0.0 else ""
                
                # --- TABELA DE APURAÇÃO GERAL ---
                st.subheader("📊 Apuração Geral do Lote")
                
                apuracao_data = {
                    "Apuração do Lote": ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NÃO IDENTIF", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"],
                    "Peso (KG)": [formatar_peso_visual(p_bruto), formatar_peso_visual(ossos_val), formatar_peso_visual(quebra_val), formatar_peso_visual(exsudato_val), formatar_peso_visual(peso_final), formatar_peso_visual(total_quebra)],
                    "R$": [f"R$ {valor_total_compra:.2f}", "-", "-", "-", f"R$ {valor_total_compra:.2f}", "-"],
                    "Porcentagem": ["100,00%", f"{(ossos_val / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", f"{(quebra_val / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", f"{(exsudato_val / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", f"{(peso_final / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%", f"{(total_quebra / p_bruto * 100):.2f}%" if p_bruto > 0 else "0,00%"]
                }
                st.table(pd.DataFrame(apuracao_data).set_index("Apuração do Lote"))

                # --- FINANCEIROS ---
                total_vendas_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"] * df_cortes[df_cortes["qualidade"] == "OURO"]["preco_venda"])
                total_vendas_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"] * df_cortes[df_cortes["qualidade"] == "PRATA"]["preco_venda"])
                total_vendas_total = total_vendas_ouro + total_vendas_prata
                
                coeficiente = valor_total_compra / total_vendas_total if total_vendas_total > 0 else 0
                
                compra_ouro = total_vendas_ouro * coeficiente
                compra_prata = total_vendas_prata * coeficiente
                
                peso_desossado_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"])
                peso_desossado_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"])
                peso_desossado_total = peso_desossado_ouro + peso_desossado_prata
                
                # Ajuste de Embalagem conforme a aba SUINO vs BOVINO[cite: 7]
                custo_efetivo_total_ouro = 0
                custo_efetivo_total_prata = 0
                taxa_embalagem = 0.0 if tipo_animal_atual == "SUINO" else 0.0003[cite: 7]
                
                for i, row in df_cortes.iterrows():
                    peso = row['peso']
                    p_venda = row['preco_venda']
                    p_custo_kg = p_venda * coeficiente
                    
                    if i == 0:
                        embalagem = taxa_embalagem * p_venda[cite: 7]
                    else:
                        embalagem = taxa_embalagem * peso[cite: 7]
                        
                    custo_efetivo_kg = p_custo_kg + embalagem
                    custo_efetivo_total = peso * custo_efetivo_kg
                    
                    if row['qualidade'] == "OURO":
                        custo_efetivo_total_ouro += custo_efetivo_total
                    else:
                        custo_efetivo_total_prata += custo_efetivo_total
                        
                custo_efetivo_total_geral = custo_efetivo_total_ouro + custo_efetivo_total_prata
                
                margem_r_ouro = total_vendas_ouro - custo_efetivo_total_ouro
                margem_r_prata = total_vendas_prata - custo_efetivo_total_prata
                margem_r_total = total_vendas_total - custo_efetivo_total_geral
                
                margem_p_ouro = (margem_r_ouro / total_vendas_ouro) if total_vendas_ouro > 0 else 0
                margem_p_prata = (margem_r_prata / total_vendas_prata) if total_vendas_prata > 0 else 0
                margem_p_total = (margem_r_total / total_vendas_total) if total_vendas_total > 0 else 0
                
                markup_ouro = (total_vendas_ouro / custo_efetivo_total_ouro) - 1 if custo_efetivo_total_ouro > 0 else 0
                markup_prata = (total_vendas_prata / custo_efetivo_total_prata) - 1 if custo_efetivo_total_prata > 0 else 0
                markup_total = (total_vendas_total / custo_efetivo_total_geral) - 1 if custo_efetivo_total_geral > 0 else 0
                
                p_medio_compra_ouro = compra_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
                p_medio_compra_prata = compra_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
                p_medio_compra_total = valor_total_compra / peso_desossado_total if peso_desossado_total > 0 else 0
                
                p_medio_compra_com_ouro = custo_efetivo_total_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
                p_medio_compra_com_prata = custo_efetivo_total_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
                p_medio_compra_com_total = custo_efetivo_total_geral / peso_desossado_total if peso_desossado_total > 0 else 0
                
                p_medio_venda_ouro = total_vendas_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
                p_medio_venda_prata = total_vendas_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
                p_medio_venda_total = total_vendas_total / peso_desossado_total if peso_desossado_total > 0 else 0
                
                # --- PALETA VERDE-LIMÃO DO MODELO NO QUADRO ---[cite: 7]
                st.markdown(
                    """
                    <style>
                    div[data-testid="stTable"] {
                        border-radius: 4px;
                    }
                    .limao-container {
                        background-color: #92D050; 
                        padding: 8px; 
                        border-radius: 4px; 
                        margin-bottom: 10px;
                        color: black;
                    }
                    </style>
                    <div class="limao-container">
                        <strong>🟩 Quadro de Indicadores (Fiel à Cor da Planilha)</strong>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                indicadores_data = {
                    "INDICADORES": [
                        "PREÇO TOTAL/Compra Sem Custos Variáveis", "PREÇO TOTAL/Venda", "Peso Desossado", 
                        "COEFICIENTE", "Custo Efetivo Total", "Margem de Contribuição R$", 
                        "Margem de Contribuição %", "Markup", "Preço médio de Compra/KG SEM-Custo Variável",
                        "Preço médio de Compra/KG COM-Custo Variável", "Preço médio de Venda/KG"
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
                
                # --- PALETA AMARELO-OURO DO MODELO NOS CORTES ---[cite: 7]
                st.markdown(
                    """
                    <div style="background-color: #FFC000; padding: 8px; border-radius: 4px; margin-top: 20px; margin-bottom: 10px; color: black;">
                        <strong>🟨 Detalhes de Rendimento e Margens (Fiel à Cor da Planilha)</strong>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                df_cortes_calc = df_cortes.copy()
                df_cortes_calc["Valor Total Venda"] = df_cortes_calc["peso"] * df_cortes_calc["preco_venda"]
                df_cortes_calc["Preço de Custo / KG"] = df_cortes_calc["preco_venda"] * coeficiente
                df_cortes_calc["Preço de Custo Total"] = df_cortes_calc["Valor Total Venda"] * coeficiente
                df_cortes_calc["Lucro Bruto"] = df_cortes_calc["Valor Total Venda"] - df_cortes_calc["Preço de Custo Total"]
                df_cortes_calc["Rendimento %"] = (df_cortes_calc["peso"] / p_bruto) * 100 if p_bruto > 0 else 0
                
                df_formatado = df_cortes_calc.rename(columns={
                    "nome_corte": "Corte", "qualidade": "Qualidade", "peso": "Peso (KG)",
                    "preco_venda": "Preço Venda (R$/KG)", "Valor Total Venda": "Faturamento Total",
                    "Preço de Custo / KG": "Custo por KG", "Preço de Custo Total": "Custo Total",
                    "Lucro Bruto": "Margem Bruta (R$)", "Rendimento %": "Rendimento %"
                })
                
                cols_exibicao = ["Corte", "Qualidade", "Peso (KG)", "Preço Venda (R$/KG)", "Faturamento Total", "Custo por KG", "Custo Total", "Margem Bruta (R$)", "Rendimento %"]
                df_final = df_formatado[cols_exibicao].copy()
                
                total_peso = df_final["Peso (KG)"].sum()
                total_faturamento = df_final["Faturamento Total"].sum()
                total_custo_total = df_final["Custo Total"].sum()
                total_margem_bruta = df_final["Margem Bruta (R$)"].sum()
                total_rendimento = df_final["Rendimento %"].sum()
                
                linha_total = pd.DataFrame([{
                    "Corte": "TOTAL SOMA", "Qualidade": "", "Peso (KG)": total_peso,
                    "Preço Venda (R$/KG)": None, "Faturamento Total": total_faturamento,
                    "Custo por KG": None, "Custo Total": total_custo_total,
                    "Margem Bruta (R$)": total_margem_bruta, "Rendimento %": total_rendimento
                }])
                
                df_com_total = pd.concat([df_final, inline_total if 'inline_total' in locals() else linha_total], ignore_index=True)
                
                st.dataframe(df_com_total.style.format({
                    "Peso (KG)": "{:.3f}",
                    "Preço Venda (R$/KG)": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                    "Faturamento Total": "R$ {:.2f}",
                    "Custo por KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                    "Custo Total": "R$ {:.2f}",
                    "Margem Bruta (R$)": "R$ {:.2f}",
                    "Rendimento %": "{:.2f}%"
                }))
                
                # ==================== GERADOR DE PDF PROFISSIONAL ====================
                st.markdown("### 🖨️ Exportação de Relatórios")
                
                def gerar_pdf_lote():
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    
                    # Cabeçalho do PDF com tom institucional
                    pdf.set_fill_color(28, 61, 90) # Azul Escuro
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(190, 15, f"RELATORIO DE DESOSSA - {st.session_state.empresa_nome.upper()}", ln=1, align="C", fill=True)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(5)
                    
                    # Dados Gerais
                    pdf.set_font("Arial", style="B", size=11)
                    pdf.cell(190, 8, f"LOTE #{id_selecionado} - {tipo_animal_atual} | Data: {data_br}", ln=1)
                    pdf.set_font("Arial", size=10)
                    pdf.cell(95, 6, f"Peso Bruto: {p_bruto:.3f} KG", ln=0)
                    pdf.cell(95, 6, f"Preco de Compra: R$ {p_comp_kg:.2f}/KG", ln=1)
                    pdf.cell(95, 6, f"Ossos / Muxiba: {ossos_val:.3f} KG", ln=0)
                    pdf.cell(95, 6, f"Quebra Nao Identificada: {quebra_val:.3f} KG", ln=1)
                    pdf.cell(95, 6, f"Exsudato: {exsudato_val:.3f} KG", ln=0)
                    pdf.cell(95, 6, f"Peso Final Aproveitado: {peso_final:.3f} KG", ln=1)
                    pdf.ln(5)
                    
                    # Quadro de Indicadores (Colorido com Verde-limão)[cite: 7]
                    pdf.set_fill_color(146, 208, 80) # Verde #92D050[cite: 7]
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.cell(190, 8, "QUADRO DE INDICADORES (VERDE)", ln=1, fill=True, align="C")
                    pdf.set_font("Arial", size=8)
                    
                    # Estrutura de colunas
                    pdf.cell(70, 6, "INDICADOR", border=1)
                    pdf.cell(40, 6, "OURO", border=1, align="C")
                    pdf.cell(40, 6, "PRATA", border=1, align="C")
                    pdf.cell(40, 6, "TOTAL", border=1, align="C")
                    pdf.ln()
                    
                    indicadores_nomes = [
                        "Compra Sem Custos Var.", "Faturamento Venda", "Peso Desossado (KG)",
                        "COEFICIENTE", "Custo Efetivo Total", "Margem de Contrib. R$",
                        "Margem de Contrib. %", "Markup %", "P. Med. Compra S/ Var.",
                        "P. Med. Compra C/ Var.", "P. Med. Venda/KG"
                    ]
                    
                    valores_ouro = [
                        f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f}",
                        f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_ouro:.2f}", f"R$ {margem_r_ouro:.2f}",
                        f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}",
                        f"R$ {p_medio_compra_com_ouro:.2f}", f"R$ {p_medio_venda_ouro:.2f}"
                    ]
                    valores_prata = [
                        f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f}",
                        f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_prata:.2f}", f"R$ {margem_r_prata:.2f}",
                        f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}",
                        f"R$ {p_medio_compra_com_prata:.2f}", f"R$ {p_medio_venda_prata:.2f}"
                    ]
                    valores_totais = [
                        f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f}",
                        f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_geral:.2f}", f"R$ {margem_r_total:.2f}",
                        f"{margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}",
                        f"R$ {p_medio_compra_com_total:.2f}", f"R$ {p_medio_venda_total:.2f}"
                    ]
                    
                    for idx_ind, nome in enumerate(indicadores_nomes):
                        pdf.cell(70, 5, nome, border=1)
                        pdf.cell(40, 5, valores_ouro[idx_ind], border=1, align="C")
                        pdf.cell(40, 5, valores_prata[idx_ind], border=1, align="C")
                        pdf.cell(40, 5, valores_totais[idx_ind], border=1, align="C")
                        pdf.ln()
                    
                    pdf.ln(5)
                    
                    # Detalhamento de Cortes (Amarelo-ouro)[cite: 7]
                    pdf.set_fill_color(255, 192, 0) # Amarelo #FFC000[cite: 7]
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.cell(190, 8, "DETALHAMENTO DE CORTES (AMARELO)", ln=1, fill=True, align="C")
                    pdf.set_font("Arial", size=7)
                    
                    pdf.cell(45, 6, "Corte", border=1)
                    pdf.cell(15, 6, "Qualidade", border=1, align="C")
                    pdf.cell(20, 6, "Peso (KG)", border=1, align="C")
                    pdf.cell(25, 6, "P. Venda (KG)", border=1, align="C")
                    pdf.cell(25, 6, "Fat. Total", border=1, align="C")
                    pdf.cell(20, 6, "Custo/KG", border=1, align="C")
                    pdf.cell(20, 6, "Custo Total", border=1, align="C")
                    pdf.cell(20, 6, "Rend. %", border=1, align="C")
                    pdf.ln()
                    
                    for _, r_corte in df_final.iterrows():
                        pdf.cell(45, 5, str(r_corte["Corte"]), border=1)
                        pdf.cell(15, 5, str(r_corte["Qualidade"]), border=1, align="C")
                        pdf.cell(20, 5, f"{r_corte['Peso (KG)']:.3f}", border=1, align="C")
                        pdf.cell(25, 5, f"R$ {r_corte['Preço Venda (R$/KG)']:.2f}", border=1, align="C")
                        pdf.cell(25, 5, f"R$ {r_corte['Faturamento Total']:.2f}", border=1, align="C")
                        pdf.cell(20, 5, f"R$ {r_corte['Custo por KG']:.2f}", border=1, align="C")
                        pdf.cell(20, 5, f"R$ {r_corte['Custo Total']:.2f}", border=1, align="C")
                        pdf.cell(20, 5, f"{r_corte['Rendimento %']:.2f}%", border=1, align="C")
                        pdf.ln()
                    
                    # Linha de Totais
                    pdf.set_font("Arial", style="B", size=7)
                    pdf.cell(45, 6, "TOTAL SOMA", border=1)
                    pdf.cell(15, 6, "", border=1)
                    pdf.cell(20, 6, f"{total_peso:.3f}", border=1, align="C")
                    pdf.cell(25, 6, "-", border=1, align="C")
                    pdf.cell(25, 6, f"R$ {total_faturamento:.2f}", border=1, align="C")
                    pdf.cell(20, 6, "-", border=1, align="C")
                    pdf.cell(20, 6, f"R$ {total_custo_total:.2f}", border=1, align="C")
                    pdf.cell(20, 6, f"{total_rendimento:.2f}%", border=1, align="C")
                    
                    return pdf.output(dest="S").encode("latin1")
                
                pdf_bytes = gerar_pdf_lote()
                st.download_button(
                    label="📄 Descarregar Relatório em PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_lote_{id_selecionado}.pdf",
                    mime="application/pdf"
                )
                
                if st.button("🗑️ Excluir esta Ação de Desossa Completa", key=f"del_{id_selecionado}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM acoes WHERE id = {id_selecionado} AND empresa_id = {st.session_state.empresa_id}")
                    conn.commit()
                    conn.close()
                    st.success("Registro completo deletado com sucesso!")
                    st.rerun()
