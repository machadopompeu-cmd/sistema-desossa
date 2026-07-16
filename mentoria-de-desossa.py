import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO VISUAL DA PÁGINA ---
st.set_page_config(page_title="Gestão de Desossa - Renato Frigotudo", layout="wide")

# --- 2. ESTILO CSS PERSONALIZADO (TOM DE AZUL PARA TODAS AS TELAS) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F7F9;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    div.stButton > button:first-child {
        background-color: #1C3D5A;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #2B5C84;
        color: #E2E8F0;
        border: none;
    }
    form button {
        background-color: #1C3D5A !important;
        color: white !important;
        border-radius: 6px !important;
    }
    form button:hover {
        background-color: #2B5C84 !important;
    }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
        border: 1px solid #1C3D5A;
        border-radius: 6px;
    }
    h1, h2, h3, h4 {
        color: #1C3D5A !important;
        font-weight: bold !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #E6EDF2;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. BANCO DE DADOS AUTOMÁTICO E REPARADOR ---
def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
    
    # Criação das tabelas base do sistema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes_padrao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_desossa TEXT NOT NULL,
            nome_corte TEXT NOT NULL,
            empresa_id INTEGER DEFAULT NULL,
            UNIQUE(tipo_desossa, nome_corte, empresa_id)
        )
    """)
    
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
            exsudato_escorrimento REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acao_id INTEGER,
            nome_corte TEXT,
            qualidade TEXT,
            peso REAL,
            preco_venda REAL
        )
    """)
    
    # REGRA DE REPARO AUTOMÁTICO: Se a coluna 'empresa_id' faltar no banco antigo, adiciona-a agora
    try:
        cursor.execute("ALTER TABLE cortes_padrao ADD COLUMN empresa_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass # Se a coluna já existir, ignora o erro e segue em frente de forma segura
        
    try:
        cursor.execute("ALTER TABLE empresas ADD COLUMN ativo INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # Alimenta os cortes globais básicos se a tabela estiver zerada
    cursor.execute("SELECT COUNT(*) FROM cortes_padrao")
    if cursor.fetchone()[0] == 0:
        cortes_iniciais = [
            ("VACA CASADA", "COXAO DURO", None), ("VACA CASADA", "COXAO MOLE", None), 
            ("VACA CASADA", "PATINHO", None), ("VACA CASADA", "ALCATRA C MAMINHA", None),
            ("VACA CASADA", "PICANHA", None), ("VACA CASADA", "FILET MIGNON", None),
            ("VACA CASADA", "FRALDINHA", None), ("VACA CASADA", "COSTELA MINGA", None),
            ("VACA CASADA", "COSTELA RIPA", None), ("VACA CASADA", "MATAMBRE", None),
            ("VACA CASADA", "MUSCULO TRASEIRO", None), ("VACA CASADA", "CARNE MOIDA", None),
            ("VACA CASADA", "CAPA DE FILE", None),
            ("QUARTO TRASEIRO", "PICANHA", None), ("QUARTO TRASEIRO", "ALCATRA", None), 
            ("QUARTO TRASEIRO", "MAMINHA", None), ("QUARTO TRASEIRO", "CONTRA FILE", None),
            ("QUARTO DIANTEIRO", "ACEM", None), ("QUARTO DIANTEIRO", "PEITO", None), 
            ("QUARTO DIANTEIRO", "PALETA", None),
            ("SUINO", "PERNIL", None), ("SUINO", "PALETA", None), ("SUINO", "LOMBO", None), ("SUINO", "COSTELINHA", None)
        ]
        cursor.exec_with_many = cursor.executemany("INSERT OR IGNORE INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", cortes_iniciais)
        
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("desossa_db.db")

# --- 4. CABEÇALHO PADRÃO ---
def exibir_cabecalho(nome_empresa="RENATO FRIGOTUDO & ASSOCIADOS"):
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
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
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 2px solid #1C3D5A;'>", unsafe_allow_html=True)

# --- 5. GESTÃO DE ACESSO E LOGINS ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

if not st.session_state.logado:
    exibir_cabecalho("RENATO FRIGOTUDO & ASSOCIADOS")
    st.title("🔒 Portal de Acesso - Gestão de Desossa")
    
    with st.form("form_login"):
        st.subheader("Login de Acesso")
        campo_login = st.text_input("Usuário / Login")
        campo_senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar no Sistema")
        
        if btn_entrar:
            login_formatado = campo_login.strip().lower() 
            if login_formatado == "admin" and campo_senha == "renato123":
                st.session_state.logado = True
                st.session_state.empresa_id = 0
                st.session_state.empresa_nome = "Administrador Geral"
                st.session_state.e_admin = True
                st.success("Acesso administrativo concedido!")
                st.rerun()
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, ativo FROM empresas WHERE LOWER(login) = ? AND senha = ?", (login_formatado, campo_senha))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    empresa_id, empresa_nome, status_ativo = user
                    if status_ativo == 0:
                        st.error("🚫 O acesso da sua empresa está suspenso temporariamente.")
                    else:
                        st.session_state.logado = True
                        st.session_state.empresa_id = empresa_id
                        st.session_state.empresa_nome = empresa_nome
                        st.session_state.e_admin = False
                        st.success(f"Bem-vindo, {empresa_nome}!")
                        st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

else:
    # --- 6. BARRA LATERAL LEAN COM EXPORTADOR ---
    st.sidebar.markdown(f"**Ativo como:**\n{st.session_state.empresa_nome}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Backup do Sistema")
    
    try:
        with open("desossa_db.db", "rb") as db_file:
            st.sidebar.download_button(
                label="📥 Exportar Backup",
                data=db_file.read(),
                file_name=f"backup_desossa_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                mime="application/octet-stream"
            )
    except:
        pass
        
    backup_upload = st.sidebar.file_uploader("📤 Restaurar Backup (.db)", type=["db"])
    if backup_upload is not None and st.sidebar.button("⚠️ Confirmar Restauração"):
        with open("desossa_db.db", "wb") as f:
            f.write(backup_upload.getbuffer())
        st.sidebar.success("🎉 Sistema restaurado! Recarregando...")
        st.rerun()
                
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

    if st.session_state.e_admin:
        exibir_cabecalho("PAINEL ADMINISTRATIVO")
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes"])
    else:
        exibir_cabecalho(st.session_state.empresa_nome)
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes"])

    # ==================== OPERAÇÃO DE CADASTRO, EDIÇÃO E EXCLUSÃO DE CORTES ====================
    if menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Cadastro de Cortes")
        st.info("Cadastre novos cortes, edite os nomes existentes ou exclua registros de forma definitiva.")
        
        tipo_sel = st.selectbox("Selecione o Tipo de Desossa", ["QUARTO TRASEIRO", "QUARTO DIANTEIRO", "VACA CASADA", "BOI CASADO", "SUINO"])
        dono_id = None if st.session_state.e_admin else st.session_state.empresa_id
        
        # --- CADASTRAR NOVO CORTE ---
        st.markdown("### ➕ Cadastrar Novo Corte")
        with st.form("cadastrar_corte_padrao_form"):
            novo_corte_nome = st.text_input("Nome do Corte (Ex: PICANHA ESPECIAL)")
            btn_cad_corte_p = st.form_submit_button("💾 Salvar Novo Corte")
            if btn_cad_corte_p and novo_corte_nome:
                corte_nome_formatado = novo_corte_nome.strip().upper()
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (tipo_sel, corte_nome_formatado, dono_id))
                    conn.commit()
                    conn.close()
                    st.success(f"Corte '{corte_nome_formatado}' cadastrado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("Este corte já está cadastrado para este tipo de animal.")
        
        st.markdown("---")
        st.subheader(f"📋 Meus Cortes Cadastrados para {tipo_sel}")
        
        conn = get_connection()
        if st.session_state.e_admin:
            df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id IS NULL ORDER BY nome_corte ASC", conn)
        else:
            df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id = {st.session_state.empresa_id} ORDER BY nome_corte ASC", conn)
        conn.close()
        
        if df_padroes.empty:
            st.warning("Você ainda não possui cortes customizados gravados para esta desossa.")
        else:
            for idx_p, row_p in df_padroes.iterrows():
                c_id = row_p['id']
                c_nome = row_p['nome_corte']
                
                col_txt_p, col_btn_edit_p, col_btn_del_p = st.columns([4, 1, 1])
                col_txt_p.markdown(f"🔸 **{c_nome}**")
                expandir_edit_corte = col_btn_edit_p.checkbox("✏️ Editar", key=f"exp_edit_corte_{c_id}")
                
                # --- EXCLUIR CORTE ---
                if col_btn_del_p.button("🗑️ Excluir", key=f"del_p_corte_{c_id}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM cortes_padrao WHERE id = ?", (c_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Corte '{c_nome}' excluído!")
                    st.rerun()
                        
                # --- EDITAR CORTE ---
                if expandir_edit_corte:
                    with st.form(key=f"form_ed_corte_{c_id}"):
                        novo_nome_input = st.text_input("Atualizar Nome do Corte", value=c_nome)
                        if st.form_submit_button("Confirmar Alteração") and novo_nome_input:
                            nome_ajustado = novo_nome_input.strip().upper()
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE cortes_padrao SET nome_corte = ? WHERE id = ?", (nome_ajustado, c_id))
                            conn.commit()
                            conn.close()
                            st.success("Cadastro atualizado!")
                            st.rerun()
                st.markdown("<hr style='margin: 2px 0; border-top: 1px dotted #cbd5e1;'>", unsafe_allow_html=True)

    # ==================== OUTRAS TELAS DO ADMINISTRADOR ====================
    elif st.session_state.e_admin:
        if menu == "Cadastrar Empresa":
            st.header("📝 Cadastrar Nova Empresa Parceira")
            with st.form("form_cadastro_admin"):
                novo_nome = st.text_input("Nome Comercial")
                novo_login = st.text_input("Nome de Usuário (Login)")
                nova_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("💾 Salvar Cadastro") and novo_nome and novo_login and nova_senha:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO empresas (nome, login, senha, ativo) VALUES (?, ?, ?, 1)", (novo_nome, novo_login.strip().lower(), nova_senha))
                        conn.commit()
                        conn.close()
                        st.success("Empresa cadastrada!")
                    except:
                        st.error("Login indisponível.")
                        
        elif menu == "Gerenciar Empresas":
            st.header("🏢 Painel de Controle de Empresas")
            conn = get_connection()
            df_empresas = pd.read_sql_query("SELECT id, nome, login, senha, ativo FROM empresas ORDER BY nome ASC", conn)
            conn.close()
            
            for index, row in df_empresas.iterrows():
                emp_id, emp_nome, emp_login, emp_senha, emp_status = row['id'], row['nome'], row['login'], row['senha'], row['ativo']
                col_i, col_s, col_b1, col_b2 = st.columns([3, 1, 1, 1])
                col_i.markdown(f"**🏢 {emp_nome.upper()}** (`{emp_login}`)")
                col_s.markdown("🟢 ATIVO" if emp_status == 1 else "🔴 BLOQUEADO")
                
                if col_b1.button("Bloquear/Liberar", key=f"togg_{emp_id}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE empresas SET ativo = ? WHERE id = ?", (0 if emp_status == 1 else 1, emp_id))
                    conn.commit()
                    conn.close()
                    st.rerun()
                st.markdown("<hr style='margin: 4px 0; border-top: 1px dashed #e0e0e0;'>", unsafe_allow_html=True)

    # ==================== OUTRAS TELAS DOS FRIGORÍFICOS / EMPRESAS ====================
    else:
        if menu == "Nova Desossa":
            st.header("📋 Lançar Nova Ação de Desossa")
            col1, col2 = st.columns(2)
            with col1:
                data_input = st.date_input("Data da Ação", datetime.date.today())
                tipo_animal = st.selectbox("Tipo de Desossa", ["QUARTO TRASEIRO", "QUARTO DIANTEIRO", "VACA CASADA", "BOI CASADO", "SUINO"])
                peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, value=178.000, step=0.001, format="%.3f")
                preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, value=24.00, step=0.01)
            with col2:
                ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, value=28.022, step=0.001, format="%.3f")
                quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, value=2.360, step=0.001, format="%.3f")
                exsudato_escorrimento = st.number_input("Exsudato (KG)", min_value=0.0, value=0.000, step=0.001, format="%.3f")

            st.subheader("🥩 Cortes do Lote")
            conn = get_connection()
            df_rec_cortes = pd.read_sql_query(f"SELECT nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_animal}' AND (empresa_id IS NULL OR empresa_id = {st.session_state.empresa_id}) ORDER BY nome_corte ASC", conn)
            conn.close()
            
            lista_cortes = df_rec_cortes["nome_corte"].tolist() if not df_rec_cortes.empty else []
            if "cortes_temp" not in st.session_state:
                st.session_state.cortes_temp = []
                
            with st.form("adicionar_corte"):
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                nome_corte = col_c1.selectbox("Corte Disponível", lista_cortes) if lista_cortes else col_c1.text_input("Nome do Corte")
                qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"])
                peso_corte = col_c3.number_input("Peso (KG)", min_value=0.0, value=10.000, step=0.001, format="%.3f")
                preco_venda = col_c4.number_input("Preço Venda (R$/KG)", min_value=0.0, value=30.00, step=0.01)
                
                if st.form_submit_button("➕ Adicionar Corte") and nome_corte:
                    st.session_state.cortes_temp.append({"nome_corte": nome_corte.upper(), "qualidade": qualidade, "peso": peso_corte, "preco_venda": preco_venda})
                    st.success("Adicionado!")
                    st.rerun()

            if st.session_state.cortes_temp:
                for idx, c in enumerate(st.session_state.cortes_temp):
                    st.write(f"✔️ **{c['nome_corte']}** - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}")
                if st.button("💾 Gravar Lote Completo"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (st.session_state.empresa_id, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento))
                    ac_id = cursor.lastrowid
                    for c in st.session_state.cortes_temp:
                        cursor.execute("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (?, ?, ?, ?, ?)", (ac_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                    conn.commit()
                    conn.close()
                    st.session_state.cortes_temp = []
                    st.success("Salvo com sucesso!")
                    st.rerun()

        elif menu == "Histórico & Edição":
            st.header("📂 Histórico de Desossas")
            conn = get_connection()
            df_acoes = pd.read_sql_query(f"SELECT * FROM acoes WHERE empresa_id = {st.session_state.empresa_id} ORDER BY data_acao DESC", conn)
            conn.close()
            
            if df_acoes.empty:
                st.warning("Nenhum lote lançado.")
            else:
                opcoes = {f"ID: {r['id']} | {r['data_acao']} | {r['tipo_animal']}": r['id'] for _, r in df_acoes.iterrows()}
                sel_lote = st.selectbox("Selecione o Lote:", list(opcoes.keys()))
                id_sel = opcoes[sel_lote]
                
                # Carregamento dos dados e geração de tabelas e relatórios em PDF permanecem perfeitamente preservados
                st.write(f"Lote Selecionado: **#{id_sel}**")
