import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO VISUAL DA PÁGINA ---
st.set_page_config(page_title="Gestão de Desossa - Renato Frigotudo", layout="wide")

# --- 2. ESTILO CSS PERSONALIZADO (ALTO CONTRASTE) ---
# Atualizámos as cores para garantir maior legibilidade (Textos mais escuros, fundos mais limpos e botões destacados)
st.markdown(
    """
    <style>
    /* Fundo geral mais claro e limpo para contraste máximo com o texto */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #0F172A; /* Texto geral em cinza quase preto */
    }
    
    /* Inputs com bordas mais escuras e nítidas para facilitar a visualização */
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] select {
        border: 2px solid #1E3A8A !important;
        border-radius: 6px;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
    }
    
    /* Rótulos (labels) dos campos com contraste reforçado */
    label {
        color: #1E293B !important;
        font-weight: bold !important;
    }
    
    /* Botões principais com azul de alto contraste e texto em branco puro */
    div.stButton > button:first-child {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 6px;
        border: 2px solid #172554;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
        border-color: #1E40AF;
    }
    
    /* Botões dentro de formulários */
    form button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }
    form button:hover {
        background-color: #1D4ED8 !important;
    }
    
    /* Títulos em Azul Escuro extra forte para contraste imediato */
    h1, h2, h3, h4 {
        color: #0F172A !important; /* Quase preto para leitura perfeita */
        font-weight: 800 !important;
    }
    
    /* Customização do menu lateral (Sidebar) com fundo contrastante */
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 2px solid #E2E8F0;
    }
    
    /* Estilização de textos secundários dentro da barra lateral */
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        color: #1E293B !important;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. BANCO DE DADOS INTELIGENTE (COM ISOLAMENTO POR EMPRESA) ---
def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
    
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
        CREATE TABLE IF NOT EXISTS tipos_desossa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            empresa_id INTEGER DEFAULT NULL,
            UNIQUE(nome, empresa_id)
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
            exsudato_escorrimento REAL,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)
    
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
    
    cursor.execute("SELECT COUNT(*) FROM tipos_desossa")
    if cursor.fetchone()[0] == 0:
        tipos_iniciais = [
            ("QUARTO TRASEIRO", None), 
            ("QUARTO DIANTEIRO", None), 
            ("VACA CASADA", None), 
            ("BOI CASADO", None), 
            ("SUINO", None)
        ]
        cursor.executemany("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (?, ?)", tipos_iniciais)
    
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
        cursor.executemany("INSERT OR IGNORE INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", cortes_iniciais)
        
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("desossa_db.db")

def get_tipos_desossa(empresa_id):
    conn = get_connection()
    cursor = conn.cursor()
    if empresa_id == 0:
        cursor.execute("SELECT DISTINCT nome FROM tipos_desossa ORDER BY nome ASC")
    else:
        cursor.execute("SELECT DISTINCT nome FROM tipos_desossa WHERE empresa_id IS NULL OR empresa_id = ? ORDER BY nome ASC", (empresa_id,))
    tipos = [r[0] for r in cursor.fetchall()]
    conn.close()
    return tipos

# --- 4. CONTROLE DE ESTADOS DO FORMULÁRIO ---
def init_form_states():
    if "input_data" not in st.session_state:
        st.session_state.input_data = datetime.date.today()
    if "input_peso_bruto" not in st.session_state:
        st.session_state.input_peso_bruto = 0.0
    if "input_preco_animal" not in st.session_state:
        st.session_state.input_preco_animal = 0.0
    if "input_ossos" not in st.session_state:
        st.session_state.input_ossos = 0.0
    if "input_quebra" not in st.session_state:
        st.session_state.input_quebra = 0.0
    if "input_exsudato" not in st.session_state:
        st.session_state.input_exsudato = 0.0
    if "input_corte_nome_manual" not in st.session_state:
        st.session_state.input_corte_nome_manual = ""
    if "input_corte_peso" not in st.session_state:
        st.session_state.input_corte_peso = 0.0
    if "input_corte_preco" not in st.session_state:
        st.session_state.input_corte_preco = 0.0

def reset_form_states():
    st.session_state.input_data = datetime.date.today()
    st.session_state.input_peso_bruto = 0.0
    st.session_state.input_preco_animal = 0.0
    st.session_state.input_ossos = 0.0
    st.session_state.input_quebra = 0.0
    st.session_state.input_exsudato = 0.0
    st.session_state.input_corte_nome_manual = ""
    st.session_state.input_corte_peso = 0.0
    st.session_state.input_corte_preco = 0.0
    st.session_state.cortes_temp = []

# --- 5. CABEÇALHO ---
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
                <h1 style="margin: 0; color: #1E3A8A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 26px; font-weight: bold; letter-spacing: 1px;">
                    {nome_empresa.upper()}
                </h1>
                <p style="margin: 0; color: #334155; font-size: 15px; font-weight: bold;">
                    Rua Paraíso, nº 514 • Pompéu/MG
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 3px solid #1E3A8A;'>", unsafe_allow_html=True)

# --- 6. CONTROLE DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

init_form_states()

# --- 7. TELA DE ACESSO (LOGIN) ---
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
                        st.success(f"Login realizado como: {empresa_nome}!")
                        st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

else:
    # --- MENU LATERAL ---
    st.sidebar.markdown(f"**Ativo como:**\n{st.session_state.empresa_nome}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Backup do Sistema")
    
    try:
        with open("desossa_db.db", "rb") as db_file:
            db_bytes = db_file.read()
        st.sidebar.download_button(
            label="📥 Exportar Backup",
            data=db_bytes,
            file_name=f"backup_desossa_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mime="application/octet-stream"
        )
    except Exception as e:
        st.sidebar.error("Erro ao gerar backup.")
        
    backup_upload = st.sidebar.file_uploader("📤 Restaurar Backup (.db)", type=["db"])
    if backup_upload is not None:
        if st.sidebar.button("⚠️ Confirmar Restauração"):
            try:
                with open("desossa_db.db", "wb") as f:
                    f.write(backup_upload.getbuffer())
                st.sidebar.success("🎉 Sistema restaurado! Recarregando...")
                st.rerun()
            except Exception as e:
                st.sidebar.error("Erro ao restaurar arquivo.")
                
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.session_state.empresa_id = None
        st.session_state.empresa_nome = ""
        st.session_state.e_admin = False
        reset_form_states()
        st.rerun()

    if st.session_state.e_admin:
        exibir_cabecalho("PAINEL ADMINISTRATIVO")
    else:
        exibir_cabecalho(st.session_state.empresa_nome)
    
    if st.session_state.e_admin:
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes"])
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes"])

    # ==================== TELAS EXCLUSIVAS DO ADMINISTRADOR ====================
    if st.session_state.e_admin and menu != "Gerenciar Cadastro de Cortes":
        if menu == "Cadastrar Empresa":
            st.header("📝 Cadastrar Nova Empresa Parceira")
            with st.form("form_cadastro_admin"):
                novo_nome = st.text_input("Nome Comercial")
                novo_login = st.text_input("Nome de Usuário (Sem espaços)")
                nova_senha = st.text_input("Senha de Acesso", type="password")
                btn_salvar_cadastro = st.form_submit_button("💾 Salvar Novo Cadastro")
                
                if btn_salvar_cadastro:
                    if not novo_nome or not novo_login or not nova_senha:
                        st.error("Preencha todos os campos!")
                    else:
                        login_salvar = novo_login.strip().lower()
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO empresas (nome, login, senha, ativo) VALUES (?, ?, ?, 1)", (novo_nome, login_salvar, nova_senha))
                            conn.commit()
                            conn.close()
                            st.success(f"🎉 Empresa '{novo_nome}' cadastrada!")
                        except sqlite3.IntegrityError:
                            st.error("Este nome de usuário já existe.")
                            
        elif menu == "Gerenciar Empresas":
            st.header("🏢 Painel de Controle de Empresas")
            conn = get_connection()
            df_empresas = pd.read_sql_query("SELECT id, nome, login, senha, ativo FROM empresas ORDER BY nome ASC", conn)
            conn.close()
            
            if df_empresas.empty:
                st.warning("Não existem empresas parceiras cadastradas.")
            else:
                for index, row in df_empresas.iterrows():
                    emp_id = row['id']
                    emp_nome = row['nome']
                    emp_login = row['login']
                    emp_senha = row['senha']
                    emp_status = row['ativo']
                    
                    col_info_emp, col_status_badge, col_btn_action, col_btn_edit = st.columns([3, 1, 1, 1])
                    with col_info_emp:
                        st.markdown(f"**🏢 {emp_nome.upper()}** (Usuário: `{emp_login}`)")
                    with col_status_badge:
                        st.markdown("🟢 **ATIVO**" if emp_status == 1 else "🔴 **BLOQUEADO**")
                    
                    with col_btn_action:
                        if emp_status == 1:
                            if st.button("🚫 Bloquear", key=f"bloq_{emp_id}"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE empresas SET ativo = 0 WHERE id = ?", (emp_id,))
                                conn.commit()
                                conn.close()
                                st.success("Acesso suspenso!")
                                st.rerun()
                        else:
                            if st.button("✅ Ativar", key=f"ativ_{emp_id}"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE empresas SET ativo = 1 WHERE id = ?", (emp_id,))
                                conn.commit()
                                conn.close()
                                st.success("Acesso liberado!")
                                st.rerun()
                                
                    with col_btn_edit:
                        expandir_edicao = st.checkbox("✏️ Editar", key=f"expand_edit_{emp_id}")

                    if expandir_edicao:
                        with st.form(key=f"form_edicao_emp_{emp_id}"):
                            edit_nome = st.text_input("Nome Comercial", value=emp_nome)
                            edit_login = st.text_input("Nome de Usuário", value=emp_login)
                            edit_senha = st.text_input("Senha de Acesso", value=emp_senha)
                            if st.form_submit_button("💾 Confirmar Alterações"):
                                try:
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE empresas SET nome=?, login=?, senha=? WHERE id=?", (edit_nome, edit_login.strip().lower(), edit_senha, emp_id))
                                    conn.commit()
                                    conn.close()
                                    st.success("Dados alterados!")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Usuário já existe.")
                    st.markdown("<hr style='margin: 4px 0; border-top: 1px dashed #e0e0e0;'>", unsafe_allow_html=True)

    # ==================== GERENCIAR CADASTRO DE CORTES (ISOLADO) ====================
    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes")
        emp_id_ativo = st.session_state.empresa_id
        
        st.markdown("### ⚙️ Cadastro de Tipos de Desossa")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("#### ➕ Inserir Novo Tipo")
            with st.form("form_add_tipo_desossa"):
                novo_tipo_des_input = st.text_input("Nome do Tipo de Desossa (Ex: BOI CASADO ESPECIAL)")
                if st.form_submit_button("💾 Salvar Tipo") and novo_tipo_des_input:
                    tipo_fmt = novo_tipo_des_input.strip().upper()
                    db_id_dono = None if st.session_state.e_admin else emp_id_ativo
                    
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (?, ?)", (tipo_fmt, db_id_dono))
                        conn.commit()
                        conn.close()
                        st.success(f"Tipo '{tipo_fmt}' inserido!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Este tipo de desossa já está cadastrado.")
                        
        with col_t2:
            st.markdown("#### ✏️ Alterar / 🗑️ Excluir Tipo")
            lista_tipos_gerenciáveis = get_tipos_desossa(emp_id_ativo)
            
            if lista_tipos_gerenciáveis:
                tipo_gerenciar_sel = st.selectbox("Selecione o Tipo", lista_tipos_gerenciáveis, key="tipo_ger_sel")
                
                col_btn_alt, col_btn_exc = st.columns(2)
                with col_btn_alt:
                    alterar_tipo_chk = st.checkbox("✏️ Alterar Nome", key="chk_alt_tipo")
                with col_btn_exc:
                    if st.button("🗑️ Excluir Tipo", key="btn_del_tipo"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if st.session_state.e_admin:
                            cursor.execute("DELETE FROM tipos_desossa WHERE nome = ? AND empresa_id IS NULL", (tipo_gerenciar_sel,))
                            cursor.execute("DELETE FROM cortes_padrao WHERE tipo_desossa = ? AND empresa_id IS NULL", (tipo_gerenciar_sel,))
                        else:
                            cursor.execute("DELETE FROM tipos_desossa WHERE nome = ? AND empresa_id = ?", (tipo_gerenciar_sel, emp_id_ativo))
                            cursor.execute("DELETE FROM cortes_padrao WHERE tipo_desossa = ? AND empresa_id = ?", (tipo_gerenciar_sel, emp_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success(f"Tipo '{tipo_gerenciar_sel}' e os cortes excluídos!")
                        st.rerun()
                        
                if alterar_tipo_chk:
                    with st.form("form_alterar_tipo_nome"):
                        novo_nome_tipo = st.text_input("Alterar Nome para:", value=tipo_gerenciar_sel)
                        if st.form_submit_button("Confirmar Alteração"):
                            if novo_nome_tipo:
                                novo_nome_fmt = novo_nome_tipo.strip().upper()
                                conn = get_connection()
                                cursor = conn.cursor()
                                if st.session_state.e_admin:
                                    cursor.execute("UPDATE tipos_desossa SET nome = ? WHERE nome = ? AND empresa_id IS NULL", (novo_nome_fmt, tipo_gerenciar_sel))
                                    cursor.execute("UPDATE cortes_padrao SET tipo_desossa = ? WHERE tipo_desossa = ? AND empresa_id IS NULL", (novo_nome_fmt, tipo_gerenciar_sel))
                                else:
                                    cursor.execute("UPDATE tipos_desossa SET nome = ? WHERE nome = ? AND empresa_id = ?", (novo_nome_fmt, tipo_gerenciar_sel, emp_id_ativo))
                                    cursor.execute("UPDATE cortes_padrao SET tipo_desossa = ? WHERE tipo_desossa = ? AND empresa_id = ?", (novo_nome_fmt, tipo_gerenciar_sel, emp_id_ativo))
                                conn.commit()
                                conn.close()
                                st.success("Nome atualizado!")
                                st.rerun()
            else:
                st.info("Nenhum tipo disponível.")

        st.markdown("---")
        
        st.markdown("### 🥩 Cadastro e Edição de Cortes")
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa", tipos_disponiveis, key="tipo_sel_cortes")
            dono_id = None if st.session_state.e_admin else emp_id_ativo
            
            st.markdown("#### ➕ Cadastrar Novo Corte")
            with st.form("cadastrar_corte_padrao_form"):
                novo_corte_nome = st.text_input("Nome do Corte")
                btn_cad_corte_p = st.form_submit_button("💾 Salvar Novo Corte")
                if btn_cad_corte_p and novo_corte_nome:
                    corte_nome_formatado = novo_corte_nome.strip().upper()
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (tipo_sel, corte_nome_formatado, dono_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Corte '{corte_nome_formatado}' adicionado!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.warning("Este corte já existe.")
            
            st.markdown("---")
            st.subheader(f"📋 Cadastro de Cortes para {tipo_sel}")
            
            conn = get_connection()
            if st.session_state.e_admin:
                df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id IS NULL ORDER BY nome_corte ASC", conn)
            else:
                df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id = {emp_id_ativo} ORDER BY nome_corte ASC", conn)
            conn.close()
            
            if df_padroes.empty:
                st.warning("Sem cortes cadastrados para este tipo.")
            else:
                for idx_p, row_p in df_padroes.iterrows():
                    c_id = row_p['id']
                    c_nome = row_p['nome_corte']
                    
                    col_txt_p, col_btn_edit_p, col_btn_del_p = st.columns([4, 1, 1])
                    with col_txt_p:
                        st.markdown(f"🔸 **{c_nome}**")
                    with col_btn_edit_p:
                        expandir_edit_corte = st.checkbox("✏️ Editar", key=f"exp_edit_corte_{c_id}")
                    with col_btn_del_p:
                        if st.button("🗑️ Excluir", key=f"del_p_corte_{c_id}"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM cortes_padrao WHERE id = ?", (c_id,))
                            conn.commit()
                            conn.close()
                            st.success("Excluído!")
                            st.rerun()
                            
                    if expandir_edit_corte:
                        with st.form(key=f"form_ed_corte_{c_id}"):
                            novo_nome_input = st.text_input("Atualizar Nome", value=c_nome)
                            if st.form_submit_button("Confirmar Alteração"):
                                if novo_nome_input:
                                    nome_ajustado = novo_nome_input.strip().upper()
                                    try:
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        cursor.execute("UPDATE cortes_padrao SET nome_corte = ? WHERE id = ?", (nome_ajustado, c_id))
                                        conn.commit()
                                        conn.close()
                                        st.success("Atualizado!")
                                        st.rerun()
                                    except sqlite3.IntegrityError:
                                        st.error("Corte duplicado!")
                    st.markdown("<hr style='margin: 2px 0; border-top: 1px dotted #cbd5e1;'>", unsafe_allow_html=True)
        else:
            st.warning("Cadastre um tipo de desossa primeiro.")

    # ==================== TELAS DAS EMPRESAS PARCEIRAS ====================
    else:
        emp_id_ativo = st.session_state.empresa_id
        
        # ==================== TELA: NOVA DESOSSA ====================
        if menu == "Nova Desossa":
            st.header("📋 Lançar Nova Ação de Desossa")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            if not tipos_empresa:
                st.warning("Cadastre os seus 'Tipos de Desossa' no menu 'Gerenciar Cadastro de Cortes' primeiro.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    data_input = st.date_input("Data da Ação", st.session_state.input_data, key="date_picker")
                    st.session_state.input_data = data_input
                    
                    tipo_animal = st.selectbox("Tipo de Desossa", tipos_empresa, key="tipo_animal_select")
                    peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, step=0.001, format="%.3f", key="input_peso_bruto")
                    preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, step=0.01, key="input_preco_animal")
                    
                with col2:
                    ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, step=0.001, format="%.3f", key="input_ossos")
                    quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, step=0.001, format="%.3f", key="input_quebra")
                    exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, step=0.001, format="%.3f", key="input_exsudato")

                st.subheader("🥩 Cortes do Lote")
                
                conn = get_connection()
                df_rec_cortes = pd.read_sql_query(f"""
                    SELECT nome_corte FROM cortes_padrao 
                    WHERE tipo_desossa = '{tipo_animal}' AND (empresa_id IS NULL OR empresa_id = {emp_id_ativo})
                    ORDER BY nome_corte ASC
                """, conn)
                conn.close()
                
                lista_cortes_disponiveis = df_rec_cortes["nome_corte"].tolist() if not df_rec_cortes.empty else []
                
                if "cortes_temp" not in st.session_state:
                    st.session_state.cortes_temp = []
                    
                with st.form("adicionar_corte"):
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    
                    if lista_cortes_disponiveis:
                        nome_corte = col_c1.selectbox("Corte Cadastrado", lista_cortes_disponiveis)
                    else:
                        nome_corte = col_c1.text_input("Nome do Corte Manual", key="input_corte_nome_manual")
                        
                    qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"])
                    peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, step=0.001, format="%.3f", key="input_corte_peso")
                    preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, step=0.01, key="input_corte_preco")
                    
                    submitted = st.form_submit_button("➕ Adicionar Corte")
                    if submitted and (nome_corte or (not lista_cortes_disponiveis and nome_corte != "")):
                        nome_format_corte = nome_corte.upper()
                        st.session_state.cortes_temp.append({
                            "nome_corte": nome_format_corte,
                            "qualidade": qualidade,
                            "peso": peso_corte,
                            "preco_venda": preco_venda
                        })
                        st.success(f"Adicionado!")
                        st.session_state.input_corte_nome_manual = ""
                        st.session_state.input_corte_peso = 0.0
                        st.session_state.input_corte_preco = 0.0
                        st.rerun()

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
                        st.error("Adicione pelo menos um corte antes de salvar!")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (emp_id_ativo, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento))
                        acao_id = cursor.lastrowid
                        
                        for c in st.session_state.cortes_temp:
                            cursor.execute("""
                                INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda)
                                VALUES (?, ?, ?, ?, ?)
                            """, (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                            
                        conn.commit()
                        conn.close()
                        
                        st.success("🎉 Lote de Desossa salvo com sucesso!")
                        reset_form_states()
                        st.rerun()

        # ==================== TELA: HISTÓRICO & EDIÇÃO ====================
        elif menu == "Histórico & Edição":
            st.header("📂 Histórico & Edição de Desossas")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            conn = get_connection()
            df_acoes = pd.read_sql_query(f"SELECT * FROM acoes WHERE empresa_id = {emp_id_ativo} ORDER BY data_acao DESC", conn)
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
                    
                if "lote_selecionado_id" not in st.session_state:
                    st.session_state.lote_selecionado_id = opcoes_map[opcoes_lista[0]]
                    
                label_inicial = [k for k, v in opcoes_map.items() if v == st.session_state.lote_selecionado_id]
                idx_default_sel = opcoes_lista.index(label_inicial[0]) if label_inicial else 0
                
                selecionado = st.selectbox("Selecione um lote para visualizar, editar ou exportar:", opcoes_lista, index=idx_default_sel)
                id_selecionado = opcoes_map[selecionado]
                st.session_state.lote_selecionado_id = id_selecionado
                
                acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
                conn = get_connection()
                df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
                conn.close()
                
                # --- EDICÃO DA CARCAÇA ---
                with st.expander("📝 EDITAR DADOS GERAIS DA CARCAÇA"):
                    col_ed1, col_ed2 = st.columns(2)
                    with col_ed1:
                        ed_data = st.date_input("Editar Data", datetime.datetime.strptime(acao_row["data_acao"], "%Y-%m-%d").date())
                        ed_tipo = st.selectbox("Editar Tipo", tipos_empresa, index=tipos_empresa.index(acao_row["tipo_animal"]) if acao_row["tipo_animal"] in tipos_empresa else 0)
                        ed_p_bruto = st.number_input("Editar Peso Bruto (KG)", value=float(acao_row["peso_bruto"]), step=0.001, format="%.3f")
                        ed_preco_animal = st.number_input("Editar Preço (R$/KG)", value=float(acao_row["preco_animal_kg"]), step=0.01)
                    with col_ed2:
                        ed_ossos = st.number_input("Editar Ossos/Muxiba (KG)", value=float(acao_row["ossos_muxiba"]), step=0.001, format="%.3f")
                        ed_quebra = st.number_input("Editar Quebra Não Identificada (KG)", value=float(acao_row["quebra_nao_identificada"]), step=0.001, format="%.3f")
                        ed_exsudato = st.number_input("Editar Exsudato/Escorrimento (KG)", value=float(acao_row["exsudato_escorrimento"]), step=0.001, format="%.3f")
                        
                    if st.button("💾 CONFIRMAR ATUALIZAÇÃO DA CARCAÇA"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE acoes 
                            SET data_acao = ?, tipo_animal = ?, peso_bruto = ?, preco_animal_kg = ?, ossos_muxiba = ?, quebra_nao_identificada = ?, exsudato_escorrimento = ?
                            WHERE id = ? AND empresa_id = ?
                        """, (str(ed_data), ed_tipo, ed_p_bruto, ed_preco_animal, ed_ossos, ed_quebra, ed_exsudato, id_selecionado, emp_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success("✅ Carcaça atualizada!")
                        st.rerun()

                # --- GERENCIAMENTO DE CORTES ---
                with st.expander("🥩 GERENCIAR CORTES INDIVIDUALMENTE"):
                    for i, corte_row in df_cortes.iterrows():
                        st.markdown(f"##### Corte: **{corte_row['nome_corte']}**")
                        col_c1, col_c2, col_c3, col_btn_salvar, col_btn_excluir = st.columns([2, 2, 2, 1, 1])
                        c_qual = col_c1.selectbox("Qualidade", ["OURO", "PRATA"], index=["OURO", "PRATA"].index(corte_row["qualidade"]), key=f"c_qual_{corte_row['id']}")
                        c_peso = col_c2.number_input("Peso (KG)", value=float(corte_row["peso"]), step=0.001, format="%.3f", key=f"c_peso_{corte_row['id']}")
                        c_preco = col_c3.number_input("Preço (R$/KG)", value=float(corte_row["preco_venda"]), step=0.01, key=f"c_preco_{corte_row['id']}")
                        
                        if col_btn_salvar.button("💾 Salvar", key=f"save_c_{corte_row['id']}"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE cortes SET qualidade = ?, peso = ?, preco_venda = ? WHERE id = ?", (c_qual, c_peso, c_preco, corte_row["id"]))
                            conn.commit()
                            conn.close()
                            st.success("Corte atualizado!")
                            st.rerun()
                            
                        if col_btn_excluir.button("🗑️ Excluir", key=f"del_c_{corte_row['id']}"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM cortes WHERE id = ?", (corte_row["id"],))
                            conn.commit()
                            conn.close()
                            st.warning("Corte removido!")
                            st.rerun()
                        st.markdown("---")

                # --- CÁLCULOS ---
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
                
                porc_ossos = (ossos_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_quebra = (quebra_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_exsudato = (exsudato_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_final = (peso_final / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_total_quebra = (total_quebra / p_bruto * 100) if p_bruto > 0 else 0.0

                # Apuração Geral
                st.subheader("📊 Apuração Geral do Lote")
                apuracao_data = {
                    "Apuração do Lote": ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NÃO IDENTIF", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"],
                    "Peso (KG)": [formatar_peso_visual(p_bruto), formatar_peso_visual(ossos_val), formatar_peso_visual(quebra_val), formatar_peso_visual(exsudato_val), formatar_peso_visual(peso_final), formatar_peso_visual(total_quebra)],
                    "R$": [f"R$ {valor_total_compra:.2f}", "-", "-", "-", f"R$ {valor_total_compra:.2f}", "-"],
                    "Porcentagem": ["100,00%", f"{porc_ossos:.2f}%", f"{porc_quebra:.2f}%", f"{porc_exsudato:.2f}%", f"{porc_final:.2f}%", f"{porc_total_quebra:.2f}%"]
                }
                st.table(pd.DataFrame(apuracao_data).set_index("Apuração do Lote"))

                # Indicadores
                total_vendas_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"] * df_cortes[df_cortes["qualidade"] == "OURO"]["preco_venda"])
                total_vendas_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"] * df_cortes[df_cortes["qualidade"] == "PRATA"]["preco_venda"])
                total_vendas_total = total_vendas_ouro + total_vendas_prata
                
                coeficiente = valor_total_compra / total_vendas_total if total_vendas_total > 0 else 0
                compra_ouro = total_vendas_ouro * coeficiente
                compra_prata = total_vendas_prata * coeficiente
                
                peso_desossado_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"])
                peso_desossado_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"])
                peso_desossado_total = peso_desossado_ouro + peso_desossado_prata
                
                custo_efetivo_total_ouro = 0
                custo_efetivo_total_prata = 0
                taxa_embalagem = 0.0 if tipo_animal_atual == "SUINO" else 0.0003
                
                for i, row_c in df_cortes.iterrows():
                    peso = row_c['peso']
                    p_venda = row_c['preco_venda']
                    p_custo_kg = p_venda * coeficiente
                    embalagem = taxa_embalagem * p_venda if i == 0 else taxa_embalagem * peso
                    custo_efetivo_kg = p_custo_kg + embalagem
                    custo_efetivo_total = peso * custo_efetivo_kg
                    
                    if row_c['qualidade'] == "OURO":
                        custo_efetivo_total_ouro += custo_efetivo_total
                    else:
                        custo_efetivo_total_prata += custo_efetivo_total
                        
                custo_efetivo_total_geral = custo_efetivo_total_ouro + custo_efetivo_total_prata
                margem_r_ouro = total_vendas_ouro - custo_efetivo_total_ouro
                margem_r_prata = total_vendas_prata - custo_efetivo_total_prata
                margem_r_total = total_vendas_total - custo_efetivo_total_geral
                
                margem_p_ouro = (margem_r_ouro / total_vendas_ouro) if total_vendas_ouro > 0 else 0
                margem_p_prata = (margem_r_prata / total_vendas_prata) if total_vendas_prata > 0 else 0
                st_margem_p_total = (margem_r_total / total_vendas_total) if total_vendas_total > 0 else 0
                
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
                
                # --- PALETA VERDE-LIMÃO (ALTO CONTRASTE) ---
                st.markdown(
                    """
                    <div style="background-color: #22C55E; padding: 10px; border-radius: 4px; margin-top: 20px; margin-bottom: 10px; color: #FFFFFF; font-weight: bold;">
                        <strong>🟩 Quadro de Indicadores (Fiel à Cor da Planilha - Contraste Otimizado)</strong>
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
                        f"{st_margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}",
                        f"R$ {p_medio_compra_com_total:.2f}", f"R$ {p_medio_venda_total:.2f}"
                    ]
                }
                st.table(pd.DataFrame(indicadores_data).set_index("INDICADORES"))
                
                # --- PALETA AMARELO-OURO (ALTO CONTRASTE) ---
                st.markdown(
                    """
                    <div style="background-color: #EAB308; padding: 10px; border-radius: 4px; margin-top: 20px; margin-bottom: 10px; color: #000000; font-weight: bold;">
                        <strong>🟨 Detalhes de Rendimento e Margens (Fiel à Cor da Planilha - Contraste Otimizado)</strong>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                df_cortes_calc = df_cortes.copy()
                df_cortes_calc["Valor Total Venda"] = df_cortes_calc["peso"] * df_cortes_calc["preco_venda"]
                df_cortes_calc["Preço de Custo / KG"] = df_cortes_calc["preco_venda"] * coeficiente
                df_cortes_calc["Preço de Custo Total"] = df_cortes_calc["Valor Total Venda"] * coeficiente
                df_cortes_calc["Lucro Bruto"] = df_cortes_calc["Valor Total Venda"] - df_cortes_calc["Preço de Custo Total"]
                df_cortes_calc["Rendimento %"] = (df_cortes_calc["peso"] / peso_final) * 100 if peso_final > 0 else 0
                
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
                
                df_com_total = pd.concat([df_final, linha_total], ignore_index=True)
                
                # --- Estilização com contraste de acessibilidade para Margem <= 0 ---
                def estilizar_margem_bruta(val):
                    try:
                        if isinstance(val, (int, float)) and val <= 0:
                            # Vermelho vivo com texto em preto para garantir que o contraste atinja o nível de acessibilidade
                            return 'background-color: #EF4444; color: #FFFFFF; font-weight: bold; border: 2px solid #991B1B;'
                    except:
                        pass
                    return ''

                st.dataframe(
                    df_com_total.style.format({
                        "Peso (KG)": "{:.3f}",
                        "Preço Venda (R$/KG)": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "Faturamento Total": "R$ {:.2f}",
                        "Custo por KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "Custo Total": "R$ {:.2f}",
                        "Margem Bruta (R$)": "R$ {:.2f}",
                        "Rendimento %": "{:.2f}%"
                    }).map(estilizar_margem_bruta, subset=["Margem Bruta (R$)"])
                )
                
                # ==================== PDF COM CONTRATE REFORÇADO ====================
                st.markdown("### 🖨️ Exportação de Relatórios")
                
                def gerar_pdf_lote():
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    
                    # Cabeçalho Principal do PDF em Azul de Alto Contraste
                    pdf.set_fill_color(30, 58, 138) # Azul Forte (#1E3A8A)
                    pdf.rect(10, 10, 190, 15, "F")
                    pdf.set_text_color(255, 255, 255) # Branco Puro
                    pdf.set_font("Arial", style="B", size=12)
                    nome_formatado = st.session_state.empresa_nome.upper().encode("latin1", "replace").decode("latin1")
                    pdf.set_xy(10, 13.5)
                    pdf.cell(190, 8, nome_formatado, ln=1, align="C")
                    
                    pdf.set_text_color(15, 23, 42) # Cinza escuro (#0F172A)
                    pdf.set_font("Arial", size=9)
                    endereco_txt = "Rua Paraiso, n. 514 - Pompeu/MG".encode("latin1", "replace").decode("latin1")
                    pdf.set_xy(10, 27)
                    pdf.cell(190, 6, endereco_txt, ln=1, align="C")
                    
                    pdf.set_draw_color(30, 58, 138)
                    pdf.set_line_width(0.8)
                    pdf.line(10, 35, 200, 35)
                    
                    pdf.set_xy(10, 40)
                    pdf.set_font("Arial", style="B", size=11)
                    pdf.set_text_color(15, 23, 42)
                    pdf.cell(190, 8, f"LOTE #{id_selecionado} - {tipo_animal_atual} | Data: {data_br}", ln=1)
                    pdf.ln(2)
                    
                    # Apuração Geral
                    pdf.set_fill_color(226, 232, 240) # Fundo mais contrastante
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.cell(190, 7, "APURACAO GERAL DO LOTE", ln=1, fill=True, align="C")
                    pdf.set_font("Arial", size=8)
                    pdf.cell(65, 6, "Item de Apuracao", border=1, fill=True)
                    pdf.cell(40, 6, "Peso (KG)", border=1, align="C", fill=True)
                    pdf.cell(45, 6, "R$", border=1, align="C", fill=True)
                    pdf.cell(40, 6, "Porcentagem", border=1, align="C", fill=True)
                    pdf.ln()
                    
                    itens_apuracao = ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NAO IDENTIF.", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"]
                    pesos_txt = [formatar_peso_visual(p_bruto), formatar_peso_visual(ossos_val), formatar_peso_visual(quebra_val), formatar_peso_visual(exsudato_val), formatar_peso_visual(peso_final), formatar_peso_visual(total_quebra)]
                    valores_txt = [f"R$ {valor_total_compra:.2f}", "-", "-", "-", f"R$ {valor_total_compra:.2f}", "-"]
                    porcentagens_txt = ["100.00%", f"{porc_ossos:.2f}%", f"{porc_quebra:.2f}%", f"{porc_exsudato:.2f}%", f"{porc_final:.2f}%", f"{porc_total_quebra:.2f}%"]
                    
                    for idx_item in range(len(itens_apuracao)):
                        pdf.cell(65, 5, itens_apuracao[idx_item], border=1)
                        pdf.cell(40, 5, pesos_txt[idx_item], border=1, align="C")
                        pdf.cell(45, 5, valores_txt[idx_item], border=1, align="C")
                        pdf.cell(40, 5, porcentagens_txt[idx_item], border=1, align="C")
                        pdf.ln()
                    
                    pdf.ln(4)
                    
                    # Indicadores
                    pdf.set_fill_color(34, 197, 94) # Verde-folha forte (#22C55E)
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.set_text_color(255, 255, 255) # Texto em branco para contraste perfeito com fundo verde
                    pdf.cell(190, 7, "QUADRO DE INDICADORES", ln=1, fill=True, align="C")
                    pdf.set_text_color(15, 23, 42) # Volta para cor escura
                    pdf.set_font("Arial", size=8)
                    pdf.cell(70, 6, "INDICADOR", border=1, fill=True)
                    pdf.cell(40, 6, "OURO", border=1, align="C", fill=True)
                    pdf.cell(40, 6, "PRATA", border=1, align="C", fill=True)
                    pdf.cell(40, 6, "TOTAL", border=1, align="C", fill=True)
                    pdf.ln()
                    
                    indicadores_nomes = [
                        "Compra Sem Custos Var.", "Faturamento Venda", "Peso Desossado (KG)",
                        "COEFICIENTE", "Custo Efetivo Total", "Margem de Contrib. R$",
                        "Margem de Contrib. %", "Markup %", "P. Med. Compra S/ Var.",
                        "P. Med. Compra C/ Var.", "P. Med. Venda/KG"
                    ]
                    valores_ouro = [f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f}", f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_ouro:.2f}", f"R$ {margem_r_ouro:.2f}", f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}", f"R$ {p_medio_compra_com_ouro:.2f}", f"R$ {p_medio_venda_ouro:.2f}"]
                    valores_prata = [f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f}", f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_prata:.2f}", f"R$ {margem_r_prata:.2f}", f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}", f"R$ {p_medio_compra_com_prata:.2f}", f"R$ {p_medio_venda_prata:.2f}"]
                    valores_totais = [f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f}", f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_geral:.2f}", f"R$ {margem_r_total:.2f}", f"{st_margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}", f"R$ {p_medio_compra_com_total:.2f}", f"R$ {p_medio_venda_total:.2f}"]
                    
                    for idx_ind, nome in enumerate(indicadores_nomes):
                        pdf.cell(70, 5, nome, border=1)
                        pdf.cell(40, 5, valores_ouro[idx_ind], border=1, align="C")
                        pdf.cell(40, 5, valores_prata[idx_ind], border=1, align="C")
                        pdf.cell(40, 5, valores_totais[idx_ind], border=1, align="C")
                        pdf.ln()
                    
                    pdf.ln(4)
                    
                    # Detalhamento de Cortes
                    pdf.set_fill_color(234, 179, 8) # Amarelo escuro forte (#EAB308)
                    pdf.set_font("Arial", style="B", size=9)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(190, 8, "DETALHAMENTO DE CORTES E MARGENS", ln=1, fill=True, align="C")
                    pdf.set_font("Arial", size=7)
                    
                    pdf.cell(35, 6, "Corte", border=1, fill=True)
                    pdf.cell(15, 6, "Qualidade", border=1, align="C", fill=True)
                    pdf.cell(15, 6, "Peso (KG)", border=1, align="C", fill=True)
                    pdf.cell(20, 6, "P. Venda (KG)", border=1, align="C", fill=True)
                    pdf.cell(20, 6, "Fat. Total", border=1, align="C", fill=True)
                    pdf.cell(18, 6, "Custo/KG", border=1, align="C", fill=True)
                    pdf.cell(22, 6, "Custo Total", border=1, align="C", fill=True)
                    pdf.cell(25, 6, "Margem Bruta", border=1, align="C", fill=True)
                    pdf.cell(20, 6, "Rend. %", border=1, align="C", fill=True)
                    pdf.ln()
                    
                    for _, r_corte in df_final.iterrows():
                        marg_val = r_corte["Margem Bruta (R$)"]
                        pdf.cell(35, 5, str(r_corte["Corte"]), border=1)
                        pdf.cell(15, 5, str(r_corte["Qualidade"]), border=1, align="C")
                        pdf.cell(15, 5, f"{r_corte['Peso (KG)']:.3f}", border=1, align="C")
                        pdf.cell(20, 5, f"R$ {r_corte['Preço Venda (R$/KG)']:.2f}", border=1, align="C")
                        pdf.cell(20, 5, f"R$ {r_corte['Faturamento Total']:.2f}", border=1, align="C")
                        pdf.cell(18, 5, f"R$ {r_corte['Custo por KG']:.2f}", border=1, align="C")
                        pdf.cell(22, 5, f"R$ {r_corte['Custo Total']:.2f}", border=1, align="C")
                        
                        # DESTAQUE CONDICIONAL DE ALTO CONTRASTE NO PDF (Vermelho puro com texto em branco)
                        if marg_val <= 0:
                            pdf.set_fill_color(239, 68, 68) # Vermelho vibrante (#EF4444)
                            pdf.set_text_color(255, 255, 255) # Texto em Branco Puro para legibilidade máxima
                            pdf.cell(25, 5, f"R$ {marg_val:.2f}", border=1, align="C", fill=True)
                            pdf.set_text_color(15, 23, 42) # Reseta para o cinza escuro original
                        else:
                            pdf.cell(25, 5, f"R$ {marg_val:.2f}", border=1, align="C")
                            
                        pdf.cell(20, 5, f"{r_corte['Rendimento %']:.2f}%", border=1, align="C")
                        pdf.ln()
                    
                    # Linha de Totais no PDF
                    pdf.set_font("Arial", style="B", size=7)
                    pdf.cell(35, 6, "TOTAL SOMA", border=1, fill=True)
                    pdf.cell(15, 6, "", border=1, fill=True)
                    pdf.cell(15, 6, f"{total_peso:.3f}", border=1, align="C", fill=True)
                    pdf.cell(20, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(20, 6, f"R$ {total_faturamento:.2f}", border=1, align="C", fill=True)
                    pdf.cell(18, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(22, 6, f"R$ {total_custo_total:.2f}", border=1, align="C", fill=True)
                    
                    if total_margem_bruta <= 0:
                        pdf.set_fill_color(239, 68, 68)
                        pdf.set_text_color(255, 255, 255)
                        pdf.cell(25, 6, f"R$ {total_margem_bruta:.2f}", border=1, align="C", fill=True)
                        pdf.set_text_color(15, 23, 42)
                    else:
                        pdf.cell(25, 6, f"R$ {total_margem_bruta:.2f}", border=1, align="C", fill=True)
                        
                    pdf.cell(20, 6, f"{total_rendimento:.2f}%", border=1, align="C", fill=True)
                    
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
                    cursor.execute(f"DELETE FROM acoes WHERE id = {id_selecionado} AND empresa_id = {emp_id_ativo}")
                    conn.commit()
                    conn.close()
                    st.success("Registro completo deletado com sucesso!")
                    st.rerun()
