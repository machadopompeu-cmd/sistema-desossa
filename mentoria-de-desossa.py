import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
from fpdf import FPDF

# =========================================================================
# 1. CONFIGURAÇÃO VISUAL E PALETA DE CORES (BOTÕES EM #A3A3A3)
# =========================================================================
st.set_page_config(page_title="Gestão de Desossa - Renato Frigotudo & Associados", layout="wide")

st.markdown(
    """
    <style>
    /* Fundo geral da aplicação */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #0F172A; 
    }
    
    /* Inputs, seletores e caixas de texto */
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] select {
        border: 1px solid #94A3B8 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stNumberInput"] input:focus {
        border-color: #A3A3A3 !important;
        box-shadow: 0 0 0 2px rgba(163, 163, 163, 0.3) !important;
    }
    
    /* Labels e títulos dos campos */
    label {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    
    /* ESTILIZAÇÃO DE TODOS OS BOTÕES NA COR #A3A3A3 */
    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border-radius: 8px !important;
        border: 1px solid #737373 !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #8C8C8C !important;
        color: #0F172A !important;
        border-color: #525252 !important;
    }
    
    /* Botões dentro de formulários */
    form button,
    div.stFormSubmitButton > button {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border-radius: 8px !important;
        border: 1px solid #737373 !important;
        font-weight: 700 !important;
    }
    form button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #8C8C8C !important;
        color: #0F172A !important;
    }
    
    /* Títulos */
    h1, h2, h3, h4 {
        color: #0F172A !important; 
        font-weight: 800 !important;
    }
    
    /* SIDEBAR (MENU LATERAL) */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 2px solid #1E293B;
    }
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Botões na Barra Lateral */
    section[data-testid="stSidebar"] div.stButton > button,
    section[data-testid="stSidebar"] div.stDownloadButton > button,
    section[data-testid="stSidebar"] a {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border: 1px solid #737373 !important;
        width: 100% !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover,
    section[data-testid="stSidebar"] div.stDownloadButton > button:hover {
        background-color: #8C8C8C !important;
        color: #0F172A !important;
    }
    
    /* Caixa de Dropzone/Upload no Menu Lateral */
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #1E293B !important;
        border: 2px dashed #A3A3A3 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] div {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* CORREÇÃO VISUAL PARA O BOTÃO DE UPLOAD */
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button,
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button *,
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] a,
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] a * {
        color: #0F172A !important;
        fill: #0F172A !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# 2. ESTRUTURA DO BANCO DE DADOS (SQLITE AUTOMÁTICO)
# =========================================================================
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
    
    try:
        cursor.execute("ALTER TABLE tipos_desossa ADD COLUMN empresa_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

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
            p_cartao REAL DEFAULT 0.0,
            p_impostos REAL DEFAULT 0.0,
            p_embalagens REAL DEFAULT 0.0,
            p_comissao REAL DEFAULT 0.0,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)
    
    novas_colunas = [
        ("p_cartao", "REAL DEFAULT 0.0"),
        ("p_impostos", "REAL DEFAULT 0.0"),
        ("p_embalagens", "REAL DEFAULT 0.0"),
        ("p_comissao", "REAL DEFAULT 0.0")
    ]
    for col_nome, col_def in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE acoes ADD COLUMN {col_nome} {col_def}")
        except sqlite3.OperationalError:
            pass

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
            ("QUARTO TRASEIRO", None), ("QUARTO DIANTEIRO", None), 
            ("VACA CASADA", None), ("BOI CASADO", None), ("SUINO", None)
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

# =========================================================================
# 3. CONTROLE DE ESTADOS DO FORMULÁRIO
# =========================================================================
def init_form_states():
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []

def reset_form_states():
    st.session_state.form_version += 1
    st.session_state.cortes_temp = []

# =========================================================================
# 4. ELEMENTOS VISUAIS DE CABEÇALHO DA APLICAÇÃO
# =========================================================================
def exibir_cabecalho(nome_empresa_usuaria=None):
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo_renato.png"):
            st.image("logo_renato.png", width=110)
        else:
            st.markdown("### 🍖 [LOGO]")
    with col_info:
        cabecalho_principal = "RENATO FRIGOTUDO & ASSOCIADOS"
        subtitulo_empresa = nome_empresa_usuaria.upper() if nome_empresa_usuaria else "PORTAL DE ACESSO"

        st.markdown(
            f"""
            <div style="padding-top: 5px;">
                <h1 style="margin: 0; color: #1E3A8A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 28px; font-weight: 800; letter-spacing: 1px;">
                    {cabecalho_principal}
                </h1>
                <h3 style="margin: 4px 0 0 0; color: #0F172A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: 700;">
                    🏢 Empresa Usuária: {subtitulo_empresa}
                </h3>
                <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px; font-weight: 500;">
                    Rua Paraíso, nº 514 • Pompéu/MG
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 3px solid #1E3A8A;'>", unsafe_allow_html=True)

# =========================================================================
# 5. GERENCIAMENTO DE SESSÃO E LOGIN
# =========================================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

init_form_states()

if not st.session_state.logado:
    exibir_cabecalho(nome_empresa_usuaria=None)
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
    # --- BARRA LATERAL ---
    st.sidebar.markdown(f"**🏢 Empresa Usuária:**\n`{st.session_state.empresa_nome.upper()}`")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Backup do Sistema")
    
    try:
        with open("desossa_db.db", "rb") as db_file:
            db_bytes = db_file.read()
        st.sidebar.download_button(
            label="📥 Exportar Backup (.db)",
            data=db_bytes,
            file_name=f"backup_desossa_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mime="application/octet-stream"
        )
    except Exception as e:
        st.sidebar.error("Erro ao gerar backup.")
        
    backup_upload = st.sidebar.file_uploader("📤 Restaurar Backup (.db)", type=["db"], key="file_uploader_backup")
    if backup_upload is not None:
        if st.sidebar.button("⚠️ Confirmar Restauração"):
            try:
                with open("desossa_db.db", "wb") as f:
                    f.write(backup_upload.getbuffer())
                st.sidebar.success("🎉 Sistema restaurado! Recarregando...")
                st.rerun()
            except Exception as f_err:
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
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes", "Importar Cortes (CSV)"])
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes"])

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    # =========================================================================
    # 6. TELAS EXCLUSIVAS DO ADMINISTRADOR
    # =========================================================================
    if st.session_state.e_admin and menu != "Gerenciar Cadastro de Cortes":
        
        if menu == "Importar Cortes (CSV)":
            st.header("📥 Importação Massiva de Cortes (CSV)")
            
            conn = get_connection()
            df_empresas_list = pd.read_sql_query("SELECT id, nome FROM empresas ORDER BY nome ASC", conn)
            conn.close()
            
            if df_empresas_list.empty:
                st.warning("⚠️ Cadastre primeiro uma empresa parceira no menu para poder importar cortes para ela.")
            else:
                emp_options = {row['nome']: row['id'] for _, row in df_empresas_list.iterrows()}
                emp_options["Cortes Globais (Sistema)"] = None
                
                selected_emp_name = st.selectbox("1. Selecione a Empresa de Destino", list(emp_options.keys()))
                target_emp_id = emp_options[selected_emp_name]
                
                tipos_empresa_destino = get_tipos_desossa(target_emp_id if target_emp_id is not None else 0)
                
                if not tipos_empresa_destino:
                    st.warning("⚠️ Esta empresa não possui tipos de desossa cadastrados. Crie pelo menos um tipo antes de importar.")
                else:
                    selected_tipo_desossa = st.selectbox("2. Selecione o Tipo de Desossa", tipos_empresa_destino)
                    
                    st.markdown("### 📄 Instruções do arquivo CSV")
                    uploaded_csv = st.file_uploader("3. Selecione o arquivo CSV para Importar", type=["csv"], key=f"csv_uploader_{st.session_state.uploader_key}")
                    
                    if uploaded_csv is not None:
                        try:
                            # LEITURA ROBUSTA SEM SUPOSIÇÃO DE SEPARADOR EQUIVOCADA
                            df_imported = None
                            encodings_to_try = ["latin-1", "utf-8-sig", "utf-8", "cp1252"]
                            
                            for enc in encodings_to_try:
                                try:
                                    uploaded_csv.seek(0)
                                    df_imported = pd.read_csv(uploaded_csv, encoding=enc, sep=";")
                                    if len(df_imported.columns) == 1:
                                        uploaded_csv.seek(0)
                                        df_imported = pd.read_csv(uploaded_csv, encoding=enc)
                                    break
                                except Exception:
                                    continue
                            
                            if df_imported is None:
                                uploaded_csv.seek(0)
                                df_imported = pd.read_csv(uploaded_csv, encoding="latin-1")
                            
                            # Limpa os cabeçalhos
                            col_map_imp = {col: str(col).strip().lower().replace(" ", "_").replace("\ufeff", "") for col in df_imported.columns}
                            df_imported.rename(columns=col_map_imp, inplace=True)
                            
                            # Mapeia colunas similares
                            for c_var in ["nom_corte", "corte", "nome"]:
                                if c_var in df_imported.columns and "nome_corte" not in df_imported.columns:
                                    df_imported.rename(columns={c_var: "nome_corte"}, inplace=True)
                                    break

                            if "nome_corte" not in df_imported.columns:
                                st.error("❌ Erro: O arquivo CSV não possui a coluna 'nome_corte'.")
                            else:
                                df_imported['nome_corte'] = df_imported['nome_corte'].dropna().astype(str).str.strip().str.upper()
                                df_imported = df_imported[df_imported['nome_corte'] != ""]
                                st.dataframe(df_imported)
                                
                                if st.button("🚀 Confirmar e Importar para o Banco de Dados"):
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    sucessos = 0
                                    duplicados = 0
                                    for _, row in df_imported.iterrows():
                                        corte_nome = row['nome_corte']
                                        try:
                                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (selected_tipo_desossa, corte_nome, target_emp_id))
                                            sucessos += 1
                                        except sqlite3.IntegrityError:
                                            duplicados += 1
                                    conn.commit()
                                    conn.close()
                                    st.success(f"🎉 Importação concluída! Adicionados: {sucessos} | Duplicados ignorados: {duplicados}")
                                    st.session_state.uploader_key += 1
                                    st.rerun()
                        except Exception as e_csv:
                            st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e_csv}")
        
        elif menu == "Cadastrar Empresa":
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
                                st.rerun()
                        else:
                            if st.button("✅ Ativar", key=f"ativ_{emp_id}"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE empresas SET ativo = 1 WHERE id = ?", (emp_id,))
                                conn.commit()
                                conn.close()
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

    # =========================================================================
    # 7. TELA GLOBAL: GERENCIAR CADASTRO DE CORTES
    # =========================================================================
    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes")
        emp_id_ativo = st.session_state.empresa_id
        
        st.markdown("### ⚙️ Cadastro de Tipos de Desossa")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("#### ➕ Inserir Novo Tipo")
            with st.form("form_add_tipo_desossa"):
                novo_tipo_des_input = st.text_input("Nome do Tipo de Desossa")
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
                    alterar_tipo_chk = st.checkbox("✏️ Alterar Nome")
                with col_btn_exc:
                    if st.button("🗑️ Excluir Tipo"):
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
                                st.rerun()

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
            
            if not df_padroes.empty:
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
                                        st.rerun()
                                    except sqlite3.IntegrityError:
                                        st.error("Corte duplicado!")
                    st.markdown("<hr style='margin: 2px 0; border-top: 1px dotted #cbd5e1;'>", unsafe_allow_html=True)

    # =========================================================================
    # 8. TELAS OPERACIONAIS DAS EMPRESAS PARCEIRAS
    # =========================================================================
    else:
        emp_id_ativo = st.session_state.empresa_id
        v_form = st.session_state.form_version
        
        # --- TELA: NOVA DESOSSA ---
        if menu == "Nova Desossa":
            st.header("📋 Lançar Nova Ação de Desossa")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            if not tipos_empresa:
                st.warning("Cadastre os seus 'Tipos de Desossa' no menu 'Gerenciar Cadastro de Cortes' primeiro.")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("##### 📦 Parâmetros Gerais")
                    data_input = st.date_input("Data da Ação", datetime.date.today(), key=f"date_picker_{v_form}")
                    tipo_animal = st.selectbox("Tipo de Desossa", tipos_empresa, key=f"tipo_animal_select_{v_form}")
                    peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_peso_bruto_{v_form}")
                    preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, step=0.01, key=f"input_preco_animal_{v_form}")
                    
                with col2:
                    st.markdown("##### ⚖️ Rendimento e Perdas")
                    ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_ossos_{v_form}")
                    quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_quebra_{v_form}")
                    exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_exsudato_{v_form}")

                with col3:
                    st.markdown("##### 📊 Custos Variáveis (%)")
                    p_cartao = st.number_input("Taxas de Cartão (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_cartao_{v_form}")
                    p_impostos = st.number_input("Impostos (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_impostos_{v_form}")
                    p_embalagens = st.number_input("Embalagens (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_embalagens_{v_form}")
                    p_comissao = st.number_input("Comissão (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_comissao_{v_form}")

                st.markdown("---")
                st.subheader("🥩 Cortes do Lote (Digitação Manual ou Upload por Arquivo)")
                
                # --- UPLOAD EM MASSA DE CORTES (CSV / CFC / EXCEL) ---
                with st.expander("📥 Importar Cortes de Arquivo (CSV / CFC / Excel)", expanded=False):
                    st.info("O arquivo para lote deve conter as colunas: **nome_corte**, **qualidade**, **peso**, **preço_de_venda** (ou preco_venda).")
                    file_cortes = st.file_uploader("Selecione o arquivo de cortes (.csv, .cfc, .xlsx)", type=["csv", "cfc", "xlsx", "xls"], key=f"file_cortes_lote_{v_form}")
                    
                    if file_cortes is not None:
                        try:
                            file_name = file_cortes.name.lower()
                            if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                                df_uploaded_cortes = pd.read_excel(file_cortes)
                            else:
                                df_uploaded_cortes = None
                                for enc in ["latin-1", "utf-8-sig", "utf-8", "cp1252"]:
                                    try:
                                        file_cortes.seek(0)
                                        df_uploaded_cortes = pd.read_csv(file_cortes, encoding=enc, sep=";")
                                        if len(df_uploaded_cortes.columns) == 1:
                                            file_cortes.seek(0)
                                            df_uploaded_cortes = pd.read_csv(file_cortes, encoding=enc)
                                        break
                                    except Exception:
                                        continue
                                if df_uploaded_cortes is None:
                                    file_cortes.seek(0)
                                    df_uploaded_cortes = pd.read_csv(file_cortes, encoding="latin-1")
                            
                            col_map = {col: str(col).strip().lower().replace(" ", "_").replace("\ufeff", "") for col in df_uploaded_cortes.columns}
                            df_uploaded_cortes.rename(columns=col_map, inplace=True)
                            
                            if "nom_corte" in df_uploaded_cortes.columns and "nome_corte" not in df_uploaded_cortes.columns:
                                df_uploaded_cortes.rename(columns={"nom_corte": "nome_corte"}, inplace=True)
                            
                            preco_col = None
                            for p_c in ["preco_de_venda", "preço_de_venda", "preco_venda", "preço_venda"]:
                                if p_c in df_uploaded_cortes.columns:
                                    preco_col = p_c
                                    break
                            
                            if "nome_corte" in df_uploaded_cortes.columns and "qualidade" in df_uploaded_cortes.columns and "peso" in df_uploaded_cortes.columns and preco_col:
                                if st.button("🚀 Confirmar e Carregar Cortes para este Lote", key=f"btn_confirm_file_cortes_{v_form}"):
                                    qtd_adicionada = 0
                                    for _, r_corte in df_uploaded_cortes.iterrows():
                                        n_corte = str(r_corte["nome_corte"]).strip().upper()
                                        q_corte = str(r_corte["qualidade"]).strip().upper()
                                        
                                        peso_raw = str(r_corte["peso"]).replace(",", ".").strip()
                                        p_corte = float(peso_raw) if peso_raw != "" else 0.0
                                        
                                        preco_raw = str(r_corte[preco_col]).upper().replace("R$", "").replace(",", ".").strip()
                                        pv_corte = float(preco_raw) if preco_raw != "" else 0.0
                                        
                                        if n_corte != "" and p_corte > 0:
                                            st.session_state.cortes_temp.append({
                                                "nome_corte": n_corte,
                                                "qualidade": "OURO" if "OURO" in q_corte else "PRATA",
                                                "peso": p_corte,
                                                "preco_venda": pv_corte
                                            })
                                            qtd_adicionada += 1
                                    st.success(f"🎉 {qtd_adicionada} cortes importados com sucesso para a lista!")
                                    st.rerun()
                            else:
                                st.error("❌ O arquivo não possui as colunas obrigatórias: nome_corte, qualidade, peso, preço_de_venda.")
                        except Exception as e_file:
                            st.error(f"❌ Erro ao ler o arquivo de cortes: {e_file}")

                # --- DIGITAÇÃO MANUAL DE CORTES ---
                conn = get_connection()
                df_rec_cortes = pd.read_sql_query(f"SELECT nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_animal}' AND (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) ORDER BY nome_corte ASC", conn)
                conn.close()
                
                lista_cortes_disponiveis = df_rec_cortes["nome_corte"].tolist() if not df_rec_cortes.empty else []
                
                with st.form(f"adicionar_corte_{v_form}"):
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    if lista_cortes_disponiveis:
                        nome_corte = col_c1.selectbox("Corte Cadastrado", lista_cortes_disponiveis)
                    else:
                        nome_corte = col_c1.text_input("Nome do Corte Manual", key=f"input_corte_nome_manual_{v_form}")
                        
                    qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"])
                    peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_corte_peso_{v_form}")
                    preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, step=0.01, key=f"input_corte_preco_{v_form}")
                    
                    submitted = st.form_submit_button("➕ Adicionar Corte Manualmente")
                    if submitted and nome_corte != "":
                        name_fmt_c = nome_corte.upper()
                        st.session_state.cortes_temp.append({
                            "nome_corte": name_fmt_c,
                            "qualidade": qualidade,
                            "peso": peso_corte,
                            "preco_venda": preco_venda
                        })
                        st.success(f"Corte '{name_fmt_c}' adicionado!")
                        st.rerun()

                if st.session_state.cortes_temp:
                    st.markdown("##### 📋 Gerenciar Cortes do Lote Adicionados:")
                    for idx, c in enumerate(st.session_state.cortes_temp):
                        col_ver, col_btn = st.columns([5, 1])
                        col_ver.write(f"**{c['nome_corte']}** ({c['qualidade']}) - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}/KG")
                        if col_btn.button("❌ Remover", key=f"rem_temp_{idx}_{v_form}"):
                            st.session_state.cortes_temp.pop(idx)
                            st.rerun()

                if st.button("💾 Salvar Ação no Banco de Dados", key=f"btn_salvar_db_{v_form}"):
                    if not st.session_state.cortes_temp:
                        st.error("Adicione pelo menos um corte antes de salvar!")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (emp_id_ativo, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao))
                        acao_id = cursor.lastrowid
                        
                        for c in st.session_state.cortes_temp:
                            cursor.execute("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (?, ?, ?, ?, ?)", (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Lote de Desossa salvo com sucesso!")
                        reset_form_states()
                        st.rerun()

        # --- TELA: HISTÓRICO & EDIÇÃO ---
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
                
                tx_cartao = acao_row["p_cartao"] if "p_cartao" in acao_row and acao_row["p_cartao"] is not None else 0.0
                tx_impostos = acao_row["p_impostos"] if "p_impostos" in acao_row and acao_row["p_impostos"] is not None else 0.0
                tx_embalagens = acao_row["p_embalagens"] if "p_embalagens" in acao_row and acao_row["p_embalagens"] is not None else 0.0
                tx_comissao = acao_row["p_comissao"] if "p_comissao" in acao_row and acao_row["p_comissao"] is not None else 0.0

                with st.expander("📝 EDITAR DADOS GERAIS, RENDIMENTO E CUSTOS VARIÁVEIS"):
                    col_ed1, col_ed2, col_ed3 = st.columns(3)
                    with col_ed1:
                        st.markdown("**Dados Operacionais**")
                        ed_data = st.date_input("Editar Data", datetime.datetime.strptime(acao_row["data_acao"], "%Y-%m-%d").date())
                        ed_tipo = st.selectbox("Editar Tipo", tipos_empresa, index=tipos_empresa.index(acao_row["tipo_animal"]) if acao_row["tipo_animal"] in tipos_empresa else 0)
                        ed_p_bruto = st.number_input("Editar Peso Bruto (KG)", value=float(acao_row["peso_bruto"]), step=0.001, format="%.3f")
                        ed_preco_animal = st.number_input("Editar Preço (R$/KG)", value=float(acao_row["preco_animal_kg"]), step=0.01)
                    with col_ed2:
                        st.markdown("**Pesos de Perdas**")
                        ed_ossos = st.number_input("Editar Ossos/Muxiba (KG)", value=float(acao_row["ossos_muxiba"]), step=0.001, format="%.3f")
                        ed_quebra = st.number_input("Editar Quebra Não Identificada (KG)", value=float(acao_row["quebra_nao_identificada"]), step=0.001, format="%.3f")
                        ed_exsudato = st.number_input("Editar Exsudato/Escorrimento (KG)", value=float(acao_row["exsudato_escorrimento"]), step=0.001, format="%.3f")
                    with col_ed3:
                        st.markdown("**Percentuais de Custos Variáveis**")
                        ed_p_cartao = st.number_input("Editar Taxa Cartão (%)", value=float(tx_cartao), step=0.01)
                        ed_p_impostos = st.number_input("Editar Impostos (%)", value=float(tx_impostos), step=0.01)
                        ed_p_embalagens = st.number_input("Editar Embalagens (%)", value=float(tx_embalagens), step=0.01)
                        ed_p_comissao = st.number_input("Editar Comissão (%)", value=float(tx_comissao), step=0.01)
                        
                    if st.button("💾 CONFIRMAR ATUALIZAÇÃO DO LOTE"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE acoes 
                            SET data_acao = ?, tipo_animal = ?, peso_bruto = ?, preco_animal_kg = ?, ossos_muxiba = ?, quebra_nao_identificada = ?, exsudato_escorrimento = ?,
                                p_cartao = ?, p_impostos = ?, p_embalagens = ?, p_comissao = ?
                            WHERE id = ? AND empresa_id = ?
                        """, (str(ed_data), ed_tipo, ed_p_bruto, ed_preco_animal, ed_ossos, ed_quebra, ed_exsudato, ed_p_cartao, ed_p_impostos, ed_p_embalagens, ed_p_comissao, id_selecionado, emp_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success("✅ Lote atualizado com sucesso!")
                        st.rerun()

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
                            st.rerun()
                        st.markdown("---")

                # Bloco Matemático de Apuração Geral
                p_bruto = acao_row["peso_bruto"]
                p_comp_kg = acao_row["preco_animal_kg"]
                valor_total_compra = p_bruto * p_comp_kg
                tipo_animal_atual = acao_row["tipo_animal"]
                
                ossos_val = acao_row["ossos_muxiba"] if acao_row["ossos_muxiba"] else 0.0
                quebra_val = acao_row["quebra_nao_identificada"] if acao_row["quebra_nao_identificada"] else 0.0
                exsudato_val = acao_row["exsudato_escorrimento"] if acao_row["exsudato_escorrimento"] else 0.0
                
                peso_final = p_bruto - ossos_val - quebra_val - exsudato_val
                total_quebra = ossos_val + quebra_val + exsudato_val
                
                porc_ossos = (ossos_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_quebra = (quebra_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_exsudato = (exsudato_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_final = (peso_final / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_total_quebra = (total_quebra / p_bruto * 100) if p_bruto > 0 else 0.0

                st.subheader("📊 Apuração Geral do Lote")
                apuracao_data = {
                    "Apuração do Lote": ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NÃO IDENTIF", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"],
                    "Peso (KG)": [f"{p_bruto:.3f}", f"{ossos_val:.3f}", f"{quebra_val:.3f}", f"{exsudato_val:.3f}", f"{peso_final:.3f}", f"{total_quebra:.3f}"],
                    "R$": [f"R$ {valor_total_compra:.2f}", "-", "-", "-", f"R$ {valor_total_compra:.2f}", "-"],
                    "Porcentagem": ["100,00%", f"{porc_ossos:.2f}%", f"{porc_quebra:.2f}%", f"{porc_exsudato:.2f}%", f"{porc_final:.2f}%", f"{porc_total_quebra:.2f}%"]
                }
                st.table(pd.DataFrame(apuracao_data).set_index("Apuração do Lote"))

                # Lógica Financeira dos Indicadores
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
                
                for idx_c, row_c in df_cortes.iterrows():
                    peso = row_c['peso']
                    p_venda = row_c['preco_venda']
                    p_custo_kg = p_venda * coeficiente
                    
                    v_cartao_kg = p_venda * (tx_cartao / 100)
                    v_impostos_kg = p_venda * (tx_impostos / 100)
                    v_embalagens_kg = p_venda * (tx_embalagens / 100)
                    v_comissao_kg = p_venda * (tx_comissao / 100)
                    
                    custo_efetivo_kg = p_custo_kg + v_cartao_kg + v_impostos_kg + v_embalagens_kg + v_comissao_kg
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
                
                st.markdown(
                    f"""
                    <div style="background-color: #1E3A8A; padding: 12px; border-radius: 6px; margin-top: 20px; margin-bottom: 10px; color: #FFFFFF; font-weight: bold;">
                        <strong>🟩 Quadro de Indicadores (Taxas Aplicadas: Cartão {tx_cartao}% | Impostos {tx_impostos}% | Embalagens {tx_embalagens}% | Comissão {tx_comissao}%)</strong>
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
                        f"{margem_p_prata*100:.2f}%", f"{markup_p_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}",
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
                
                st.markdown(
                    """
                    <div style="background-color: #334155; padding: 10px; border-radius: 6px; margin-top: 20px; margin-bottom: 10px; color: #FFFFFF; font-weight: bold;">
                        <strong>🟨 Detalhes de Rendimento, Margens e Custos Variáveis por Linha (Fiel ao Modelo Excel)</strong>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                linhas_detalhes = []
                for idx_l, row_l in df_cortes.iterrows():
                    peso = row_l["peso"]
                    p_venda = row_l["preco_venda"]
                    p_custo_kg = p_venda * coeficiente
                    preco_custo_total_linha = peso * p_custo_kg
                    fat_linha = peso * p_venda
                    lucro_bruto = fat_linha - preco_custo_total_linha
                    pct_cortes = peso / peso_final if peso_final > 0 else 0.0
                    
                    v_cartao = p_venda * (tx_cartao / 100)
                    v_impostos = p_venda * (tx_impostos / 100)
                    v_embalagem = p_venda * (tx_embalagens / 100)
                    v_comissao = p_venda * (tx_comissao / 100)
                    
                    custo_efetivo_kg = p_custo_kg + v_cartao + v_impostos + v_embalagem + v_comissao
                    custo_efetivo_total = peso * custo_efetivo_kg
                    
                    linhas_detalhes.append({
                        "Corte/Código": row_l["nome_corte"],
                        "Qualidade": row_l["qualidade"],
                        "Peso /KG": peso,
                        "PREÇO CUSTO/KG": p_custo_kg,
                        "PREÇO/CUSTO": preco_custo_total_linha,
                        "PREÇO VENDA/KG": p_venda,
                        "VALOR TOTAL DE VENDAS": fat_linha,
                        "LUCRO BRUTO": lucro_bruto,
                        "PERCENTUAL/CORTES": pct_cortes,
                        "TAXAS DE CARTÃO": v_cartao,
                        "IMPOSTOS": v_impostos,
                        "EMBALAGENS": v_embalagem,
                        "COMISSÃO": v_comissao,
                        "CUSTO EFETIVO/KG": custo_efetivo_kg,
                        "CUSTO EFETIVO TOTAL": custo_efetivo_total
                    })
                    
                df_final = pd.DataFrame(linhas_detalhes)
                
                total_peso = df_final["Peso /KG"].sum()
                total_preco_custo = df_final["PREÇO/CUSTO"].sum()
                total_faturamento = df_final["VALOR TOTAL DE VENDAS"].sum()
                total_lucro_bruto = df_final["LUCRO BRUTO"].sum()
                total_pct_cortes = df_final["PERCENTUAL/CORTES"].sum()
                total_custo_efetivo_total = df_final["CUSTO EFETIVO TOTAL"].sum()
                
                linha_total = pd.DataFrame([{
                    "Corte/Código": "TOTAL SOMA",
                    "Qualidade": "",
                    "Peso /KG": total_peso,
                    "PREÇO CUSTO/KG": None,
                    "PREÇO/CUSTO": total_preco_custo,
                    "PREÇO VENDA/KG": None,
                    "VALOR TOTAL DE VENDAS": total_faturamento,
                    "LUCRO BRUTO": total_lucro_bruto,
                    "PERCENTUAL/CORTES": total_pct_cortes,
                    "TAXAS DE CARTÃO": None,
                    "IMPOSTOS": None,
                    "EMBALAGENS": None,
                    "COMISSÃO": None,
                    "CUSTO EFETIVO/KG": None,
                    "CUSTO EFETIVO TOTAL": total_custo_efetivo_total
                }])
                
                df_com_total = pd.concat([df_final, linha_total], ignore_index=True)
                
                st.dataframe(
                    df_com_total.style.format({
                        "Peso /KG": "{:.3f}",
                        "PREÇO CUSTO/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "PREÇO/CUSTO": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "PREÇO VENDA/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "VALOR TOTAL DE VENDAS": "R$ {:.2f}",
                        "LUCRO BRUTO": "R$ {:.2f}",
                        "PERCENTUAL/CORTES": lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "-",
                        "TAXAS DE CARTÃO": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "IMPOSTOS": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "EMBALAGENS": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "COMISSÃO": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "CUSTO EFETIVO/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "CUSTO EFETIVO TOTAL": "R$ {:.2f}"
                    })
                )
                
                # --- EXPORTAÇÃO DO RELATÓRIO PDF (ENDEREÇO REMOVIDO) ---
                st.markdown("### 🖨️ Exportação de Relatórios em PDF")
                
                def gerar_pdf_lote():
                    pdf = FPDF(orientation='L', unit='mm', format='A4')
                    pdf.add_page()
                    pdf.set_font("Arial", size=10)
                    
                    # 1. Cabeçalho Principal (RENATO FRIGOTUDO & ASSOCIADOS)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.rect(10, 10, 277, 14, "F")
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", style="B", size=13)
                    pdf.set_xy(10, 13)
                    pdf.cell(277, 8, "RENATO FRIGOTUDO & ASSOCIADOS", ln=1, align="C")
                    
                    # 2. Nome da Empresa Usuária (sem a linha do endereço)
                    pdf.set_text_color(15, 23, 42)
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.set_xy(10, 26)
                    nome_emp_pdf = f"Empresa Usuaria: {st.session_state.empresa_nome.upper()}".encode("latin1", "replace").decode("latin1")
                    pdf.cell(277, 6, nome_emp_pdf, ln=1, align="C")
                    
                    # Linha Divisória Ajustada
                    pdf.set_draw_color(30, 58, 138)
                    pdf.set_line_width(0.8)
                    pdf.line(10, 34, 287, 34)
                    
                    pdf.set_xy(10, 37)
                    pdf.set_font("Arial", style="B", size=9)
                    pdf.cell(277, 6, f"LOTE #{id_selecionado} - {tipo_animal_atual} | Data: {data_br} | Taxas: Cartao {tx_cartao}% | Impostos {tx_impostos}% | Embalagens {tx_embalagens}% | Comissao {tx_comissao}%", ln=1)
                    pdf.ln(2)

                    # 3. TABELA APURAÇÃO GERAL DO LOTE
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", style="B", size=8)
                    pdf.cell(277, 5, " APURACAO GERAL DO LOTE", border=1, ln=1, fill=True)
                    
                    pdf.set_fill_color(241, 245, 249)
                    pdf.set_text_color(15, 23, 42)
                    pdf.set_font("Arial", style="B", size=7.5)
                    pdf.cell(117, 4.5, "Apuracao do Lote", border=1, fill=True)
                    pdf.cell(50, 4.5, "Peso (KG)", border=1, align="C", fill=True)
                    pdf.cell(60, 4.5, "R$", border=1, align="C", fill=True)
                    pdf.cell(50, 4.5, "Porcentagem", border=1, align="C", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", size=7)
                    rows_apuracao_pdf = [
                        ("PESO BRUTO/KG", f"{p_bruto:.3f}", f"R$ {valor_total_compra:.2f}", "100.00%"),
                        ("OSSOS/MUXIBA", f"{ossos_val:.3f}", "-", f"{porc_ossos:.2f}%"),
                        ("QUEBRA NAO IDENTIF", f"{quebra_val:.3f}", "-", f"{porc_quebra:.2f}%"),
                        ("ESCORRIMENTO", f"{exsudato_val:.3f}", "-", f"{porc_exsudato:.2f}%"),
                        ("Peso Final", f"{peso_final:.3f}", f"R$ {valor_total_compra:.2f}", f"{porc_final:.2f}%"),
                        ("TOTAL DE QUEBRA", f"{total_quebra:.3f}", "-", f"{porc_total_quebra:.2f}%")
                    ]

                    for rotulo, p_kg, v_rs, pct_val in rows_apuracao_pdf:
                        pdf.cell(117, 4.5, rotulo, border=1)
                        pdf.cell(50, 4.5, p_kg, border=1, align="C")
                        pdf.cell(60, 4.5, v_rs, border=1, align="C")
                        pdf.cell(50, 4.5, pct_val, border=1, align="C")
                        pdf.ln()

                    pdf.ln(4)
                    
                    # 4. Tabela de Cortes com as 15 Colunas
                    pdf.set_fill_color(234, 179, 8)
                    pdf.set_text_color(15, 23, 42)
                    pdf.set_font("Arial", style="B", size=7)
                    
                    headers_excel = [
                        "Corte/Codigo", "Qual.", "Peso/KG", "P.Custo/KG", "P./Custo", "P.Venda/KG", 
                        "Total Vendas", "Lucro Bruto", "% Cortes", "Cartao", "Impostos", "Embal.", 
                        "Comissao", "C.Efet/KG", "C.Efet Total"
                    ]
                    widths_excel = [28, 12, 16, 21, 19, 21, 23, 19, 16, 17, 15, 15, 15, 20, 20]
                    
                    for text_h, w_h in zip(headers_excel, widths_excel):
                        pdf.cell(w_h, 6, text_h, border=1, align="C", fill=True)
                    pdf.ln()
                    
                    pdf.set_font("Arial", size=6.5)
                    for _, r in df_final.iterrows():
                        pdf.cell(28, 5, str(r["Corte/Código"])[:18], border=1)
                        pdf.cell(12, 5, str(r["Qualidade"]), border=1, align="C")
                        pdf.cell(16, 5, f"{r['Peso /KG']:.3f}", border=1, align="C")
                        pdf.cell(21, 5, f"R$ {r['PREÇO CUSTO/KG']:.2f}", border=1, align="C")
                        pdf.cell(19, 5, f"R$ {r['PREÇO/CUSTO']:.2f}", border=1, align="C")
                        pdf.cell(21, 5, f"R$ {r['PREÇO VENDA/KG']:.2f}", border=1, align="C")
                        pdf.cell(23, 5, f"R$ {r['VALOR TOTAL DE VENDAS']:.2f}", border=1, align="C")
                        pdf.cell(19, 5, f"R$ {r['LUCRO BRUTO']:.2f}", border=1, align="C")
                        pdf.cell(16, 5, f"{r['PERCENTUAL/CORTES']*100:.1f}%", border=1, align="C")
                        pdf.cell(17, 5, f"R$ {r['TAXAS DE CARTÃO']:.2f}", border=1, align="C")
                        pdf.cell(15, 5, f"R$ {r['IMPOSTOS']:.2f}", border=1, align="C")
                        pdf.cell(15, 5, f"R$ {r['EMBALAGENS']:.2f}", border=1, align="C")
                        pdf.cell(15, 5, f"R$ {r['COMISSÃO']:.2f}", border=1, align="C")
                        pdf.cell(20, 5, f"R$ {r['CUSTO EFETIVO/KG']:.2f}", border=1, align="C")
                        pdf.cell(20, 5, f"R$ {r['CUSTO EFETIVO TOTAL']:.2f}", border=1, align="C")
                        pdf.ln()
                        
                    pdf.set_font("Arial", style="B", size=7)
                    pdf.cell(28, 6, "TOTAL SOMA", border=1, fill=True)
                    pdf.cell(12, 6, "", border=1, fill=True)
                    pdf.cell(16, 6, f"{total_peso:.3f}", border=1, align="C", fill=True)
                    pdf.cell(21, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(19, 6, f"R$ {total_preco_custo:.2f}", border=1, align="C", fill=True)
                    pdf.cell(21, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(23, 6, f"R$ {total_faturamento:.2f}", border=1, align="C", fill=True)
                    pdf.cell(19, 6, f"R$ {total_lucro_bruto:.2f}", border=1, align="C", fill=True)
                    pdf.cell(16, 6, f"{total_pct_cortes*100:.1f}%", border=1, align="C", fill=True)
                    pdf.cell(17, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(15, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(15, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(15, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(20, 6, "-", border=1, align="C", fill=True)
                    pdf.cell(20, 6, f"R$ {total_custo_efetivo_total:.2f}", border=1, align="C", fill=True)
                    pdf.ln(6)
                    
                    # 5. Quadro de Indicadores
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", style="B", size=8)
                    pdf.cell(277, 5, " QUADRO DE INDICADORES DO LOTE", border=1, ln=1, fill=True)
                    
                    pdf.set_fill_color(241, 245, 249)
                    pdf.set_text_color(15, 23, 42)
                    pdf.cell(117, 5, "INDICADORES", border=1, fill=True)
                    pdf.cell(40, 5, "OURO", border=1, align="C", fill=True)
                    pdf.cell(40, 5, "PRATA", border=1, align="C", fill=True)
                    pdf.cell(40, 5, "TOTAL", border=1, align="C", fill=True)
                    pdf.ln()
                    
                    pdf.set_font("Arial", size=7.5)
                    rows_indicadores = [
                        ("PRECO TOTAL / Compra Sem Custos Variaveis", f"R$ {compra_ouro:.2f}", f"R$ {compra_prata:.2f}", f"R$ {valor_total_compra:.2f}"),
                        ("PRECO TOTAL / Venda", f"R$ {total_vendas_ouro:.2f}", f"R$ {total_vendas_prata:.2f}", f"R$ {total_vendas_total:.2f}"),
                        ("Peso Desossado (KG)", f"{peso_desossado_ouro:.3f}", f"{peso_desossado_prata:.3f}", f"{peso_desossado_total:.3f}"),
                        ("COEFICIENTE", f"{coeficiente:.6f}", f"{coeficiente:.6f}", f"{coeficiente:.6f}"),
                        ("Custo Efetivo Total", f"R$ {custo_efetivo_total_ouro:.2f}", f"R$ {custo_efetivo_total_prata:.2f}", f"R$ {custo_efetivo_total_geral:.2f}"),
                        ("Margem de Contribuicao R$", f"R$ {margem_r_ouro:.2f}", f"R$ {margem_r_prata:.2f}", f"R$ {margem_r_total:.2f}"),
                        ("Margem de Contribuicao %", f"{margem_p_ouro*100:.2f}%", f"{margem_p_prata*100:.2f}%", f"{st_margem_p_total*100:.2f}%"),
                        ("Markup", f"{markup_ouro*100:.2f}%", f"{markup_prata*100:.2f}%", f"{markup_total*100:.2f}%"),
                        ("Preco medio de Compra/KG SEM-Custo Variavel", f"R$ {p_medio_compra_ouro:.2f}", f"R$ {p_medio_compra_prata:.2f}", f"R$ {p_medio_compra_total:.2f}"),
                        ("Preco medio de Compra/KG COM-Custo Variavel", f"R$ {p_medio_compra_com_ouro:.2f}", f"R$ {p_medio_compra_com_prata:.2f}", f"R$ {p_medio_compra_com_total:.2f}"),
                        ("Preco medio de Venda/KG", f"R$ {p_medio_venda_ouro:.2f}", f"R$ {p_medio_venda_prata:.2f}", f"R$ {p_medio_venda_total:.2f}")
                    ]
                    
                    for label_ind, v_ouro, v_prata, v_tot in rows_indicadores:
                        pdf.cell(117, 4.5, label_ind, border=1)
                        pdf.cell(40, 4.5, v_ouro, border=1, align="C")
                        pdf.cell(40, 4.5, v_prata, border=1, align="C")
                        pdf.cell(40, 4.5, v_tot, border=1, align="C")
                        pdf.ln()
                        
                    return pdf.output(dest="S").encode("latin1")
                
                pdf_bytes = gerar_pdf_lote()
                st.download_button(
                    label="📄 Descarregar Relatório Completo (15 Colunas) em PDF",
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
                    st.success("Lote excluído!")
                    st.rerun()
