import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO VISUAL DA PÁGINA ---
st.set_page_config(page_title="Gestão de Desossa - Renato Frigotudo", layout="wide")

# --- 2. ESTILO CSS PERSONALIZADO (ALTO CONTRASTE E LEGIBILIDADE) ---
st.markdown(
    """
    <style>
    /* Fundo claro de alto contraste e textos principais muito escuros */
    .stApp {
        background-color: #FFFFFF;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #0F172A; 
    }
    
    /* Campos de entrada com bordas escuras e bem visíveis */
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] select {
        border: 2px solid #0F172A !important;
        border-radius: 6px;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: bold !important;
    }
    
    /* Nomes dos campos (labels) em negrito e cor escura forte */
    label {
        color: #0F172A !important;
        font-weight: bold !important;
        font-size: 15px !important;
    }
    
    /* Botões principais em Azul Forte com letras em Branco Puro */
    div.stButton > button:first-child {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 6px;
        border: 2px solid #0F172A;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #1D4ED8;
    }
    
    /* Botões dentro de formulários */
    form button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }
    form button:hover {
        background-color: #2563EB !important;
    }
    
    /* Títulos em destaque máximo */
    h1, h2, h3, h4 {
        color: #0F172A !important; 
        font-weight: 800 !important;
    }
    
    /* Menu Lateral com fundo cinza-claro contrastando com texto escuro */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 3px solid #0F172A;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        color: #0F172A !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. BANCO DE DADOS INTELIGENTE ---
def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
    
    # Tabela de Empresas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    """)
    
    # Tabela de Tipos de Desossa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_desossa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            empresa_id INTEGER DEFAULT NULL,
            UNIQUE(nome, empresa_id)
        )
    """)
    
    # Ajuste automático para o banco de dados antigo
    try:
        cursor.execute("ALTER TABLE tipos_desossa ADD COLUMN empresa_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    # Tabela de Cortes Padrão
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes_padrao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_desossa TEXT NOT NULL,
            nome_corte TEXT NOT NULL,
            empresa_id INTEGER DEFAULT NULL,
            UNIQUE(tipo_desossa, nome_corte, empresa_id)
        )
    """)
    
    # Tabela de Lotes (Ações)
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
    
    # Tabela de Cortes vinculados às ações
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
    
    # Carga inicial padrão de tipos de desossa
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
    
    # Carga inicial global de cortes
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
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []

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

# --- 5. CABEÇALHO PADRONIZADO ---
def exibir_cabecalho(nome_empresa_usuaria=None):
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo_renato.png"):
            st.image("logo_renato.png", width=110)
        else:
            st.markdown("### 🍖 [LOGO]")
    with col_info:
        cabecalho_principal = "RENATO FRIGOTUDO & ASSOCIADOS"
        if nome_empresa_usuaria:
            subtitulo_empresa = nome_empresa_usuaria.upper()
        else:
            subtitulo_empresa = "PORTAL DE ACESSO"

        st.markdown(
            f"""
            <div style="padding-top: 10px;">
                <h1 style="margin: 0; color: #1E3A8A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 26px; font-weight: bold; letter-spacing: 1px;">
                    {cabecalho_principal}
                </h1>
                <h3 style="margin: 3px 0 0 0; color: #0F172A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: bold;">
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

# --- 6. CONTROLE DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

init_form_states()

# --- 7. TELA DE ACESSO (LOGIN) ---
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
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes", "Importar Cortes (CSV)"])
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes"])

    # ==================== TELAS EXCLUSIVAS DO ADMINISTRADOR ====================
    if st.session_state.e_admin and menu != "Gerenciar Cadastro de Cortes":
        if menu == "Importar Cortes (CSV)":
            st.header("📥 Importação Massiva de Cortes (CSV)")
            conn = get_connection()
            df_empresas_list = pd.read_sql_query("SELECT id, nome FROM empresas ORDER BY nome ASC", conn)
            conn.close()
            
            if df_empresas_list.empty:
                st.warning("⚠️ Cadastre primeiro uma empresa parceira no menu.")
            else:
                emp_options = {row['nome']: row['id'] for _, row in df_empresas_list.iterrows()}
                emp_options["Cortes Globais (Sistema)"] = None
                selected_emp_name = st.selectbox("1. Selecione a Empresa de Destino", list(emp_options.keys()))
                target_emp_id = emp_options[selected_emp_name]
                tipos_empresa_destino = get_tipos_desossa(target_emp_id if target_emp_id is not None else 0)
                
                if not tipos_empresa_destino:
                    st.warning("⚠️ Esta empresa não possui tipos de desossa cadastrados.")
                else:
                    selected_tipo_desossa = st.selectbox("2. Selecione o Tipo de Desossa", tipos_empresa_destino)
                    uploaded_csv = st.file_uploader("3. Selecione o arquivo CSV para Importar", type=["csv"], key=f"csv_uploader_{st.session_state.uploader_key}")
                    
                    if uploaded_csv is not None:
                        try:
                            try:
                                df_imported = pd.read_csv(uploaded_csv, encoding="utf-8")
                            except UnicodeDecodeError:
                                uploaded_csv.seek(0)
                                df_imported = pd.read_csv(uploaded_csv, encoding="latin-1")
                            
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
                                    for _, row in df_imported.iterrows():
                                        try:
                                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (selected_tipo_desossa, row['nome_corte'], target_emp_id))
                                            sucessos += 1
                                        except sqlite3.IntegrityError:
                                            pass
                                    conn.commit()
                                    conn.close()
                                    st.success(f"🎉 Importação Concluída com sucesso: {sucessos} cortes!")
                                    st.session_state.uploader_key += 1
                                    st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e}")
        
        elif menu == "Cadastrar Empresa":
            st.header("📝 Cadastrar Nova Empresa Parceira")
            with st.form("form_cadastro_admin"):
                novo_nome = st.text_input("Nome Comercial")
                novo_login = st.text_input("Nome de Usuário (Sem espaços)")
                nova_senha = st.text_input("Senha de Acesso", type="password")
                if st.form_submit_button("💾 Salvar Novo Cadastro") and novo_nome and novo_login and nova_senha:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO empresas (nome, login, senha, ativo) VALUES (?, ?, ?, 1)", (novo_nome, novo_login.strip().lower(), nova_senha))
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
            for index, row in df_empresas.iterrows():
                st.markdown(f"**🏢 {row['nome'].upper()}** (Usuário: `{row['login']}`)")
                st.markdown("<hr style='margin: 4px 0; border-top: 1px dashed #e0e0e0;'>", unsafe_allow_html=True)

    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes")
        emp_id_ativo = st.session_state.empresa_id
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa", tipos_disponiveis)
            with st.form("cadastrar_corte_padrao_form"):
                novo_corte_nome = st.text_input("Nome do Corte")
                if st.form_submit_button("💾 Salvar Novo Corte") and novo_corte_nome:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (tipo_sel, novo_corte_nome.strip().upper(), None if st.session_state.e_admin else emp_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success("Corte adicionado!")
                    except sqlite3.IntegrityError:
                        st.warning("Este corte já existe.")

    # ==================== TELAS DAS EMPRESAS PARCEIRAS ====================
    else:
        emp_id_ativo = st.session_state.empresa_id
        
        # ==================== TELA: NOVA DESOSSA ====================
        if menu == "Nova Desossa":
            st.header("📋 Lançar Nova Ação de Desossa")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            if not tipos_empresa:
                st.warning("Cadastre os seus 'Tipos de Desossa' primeiro.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    data_input = st.date_input("Data da Ação", st.session_state.input_data)
                    tipo_animal = st.selectbox("Tipo de Desossa", tipos_empresa)
                    peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, step=0.001, format="%.3f")
                    preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, step=0.01)
                with col2:
                    ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, step=0.001, format="%.3f")
                    quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, step=0.001, format="%.3f")
                    exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, step=0.001, format="%.3f")

                # --- 📥 IMPLEMENTAÇÃO DA IMPORTAÇÃO DE CORTES VIA CSV (OPÇÃO 1) ---
                st.markdown("---")
                st.subheader("📥 Preenchimento Rápido por Planilha (CSV)")
                st.markdown(
                    "> **Instruções do arquivo:** Carregue um arquivo `.csv` contendo obrigatoriamente as colunas com estes cabeçalhos em minúsculo: "
                    "`nome_corte`, `peso` e `preco_venda`."
                )
                uploaded_lote_csv = st.file_uploader("Carregar Planilha de Cortes (.csv)", type=["csv"], key="lote_csv_uploader")
                
                if uploaded_lote_csv is not None:
                    try:
                        try:
                            df_lote_imported = pd.read_csv(uploaded_lote_csv, encoding="utf-8")
                        except UnicodeDecodeError:
                            uploaded_lote_csv.seek(0)
                            df_lote_imported = pd.read_csv(uploaded_lote_csv, encoding="latin-1")
                        
                        if not all(col in df_lote_imported.columns for col in ["nome_corte", "peso", "preco_venda"]):
                            st.error("❌ O arquivo precisa conter as colunas: 'nome_corte', 'peso' e 'preco_venda'.")
                        else:
                            if st.button("🔄 Aplicar Cortes da Planilha ao Lote"):
                                st.session_state.cortes_temp = [] # Reseta os itens inseridos anteriormente
                                for _, row_l in df_lote_imported.iterrows():
                                    if pd.notnull(row_l["nome_corte"]) and str(row_l["nome_corte"]).strip() != "":
                                        st.session_state.cortes_temp.append({
                                            "nome_corte": str(row_l["nome_corte"]).strip().upper(),
                                            "qualidade": "OURO", # Classificação inicial padrão
                                            "peso": float(row_l["peso"]) if pd.notnull(row_l["peso"]) else 0.0,
                                            "preco_venda": float(row_l["preco_venda"]) if pd.notnull(row_l["preco_venda"]) else 0.0
                                        })
                                st.success(f"🎉 {len(st.session_state.cortes_temp)} cortes importados com sucesso da planilha!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar planilha de cortes: {e}")

                st.markdown("---")
                st.subheader("🥩 Cortes do Lote Atual")
                
                conn = get_connection()
                df_rec_cortes = pd.read_sql_query(f"SELECT nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_animal}' AND (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) ORDER BY nome_corte ASC", conn)
                conn.close()
                lista_cortes_disponiveis = df_rec_cortes["nome_corte"].tolist() if not df_rec_cortes.empty else []
                
                with st.form("adicionar_corte"):
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    nome_corte = col_c1.selectbox("Corte Cadastrado", lista_cortes_disponiveis) if lista_cortes_disponiveis else col_c1.text_input("Nome do Corte Manual")
                    qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"])
                    peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, step=0.001, format="%.3f")
                    preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, step=0.01)
                    
                    if st.form_submit_button("➕ Adicionar Corte Manual") and nome_corte:
                        st.session_state.cortes_temp.append({
                            "nome_corte": nome_corte.upper(), "qualidade": qualidade, "peso": peso_corte, "preco_venda": preco_venda
                        })
                        st.rerun()

                if st.session_state.cortes_temp:
                    for idx, c in enumerate(st.session_state.cortes_temp):
                        col_ver, col_btn = st.columns([5, 1])
                        col_ver.write(f"**{c['nome_corte']}** ({c['qualidade']}) - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}/KG")
                        if col_btn.button("❌ Remover", key=f"rem_temp_{idx}"):
                            st.session_state.cortes_temp.pop(idx)
                            st.rerun()

                    if st.button("💾 Salvar Ação no Banco de Dados"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (emp_id_ativo, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento))
                        acao_id = cursor.lastrowid
                        for c in st.session_state.cortes_temp:
                            cursor.execute("INSERT INTO cortes (acao_id, nome_corte, calidad, peso, preco_venda) VALUES (?, ?, ?, ?, ?)", (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
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
                st.warning("Ainda não existem desossas cadastradas.")
            else:
                opcoes_map = {}
                opcoes_lista = []
                for idx, row in df_acoes.iterrows():
                    data_original = datetime.datetime.strptime(row['data_acao'], "%Y-%m-%d").date()
                    data_br = data_original.strftime("%d/%m/%Y")
                    label = f"ID: {row['id']} - {data_br} | {row['tipo_animal']}"
                    opcoes_map[label] = row['id']
                    opcoes_lista.append(label)
                    
                selecionado = st.selectbox("Selecione um lote para visualizar:", opcoes_lista)
                id_selecionado = opcoes_map[selecionado]
                
                # --- ⚙️ INPUT DOS PERCENTUAIS DE CUSTOS VARIÁVEIS (MODELO EXCEL FIEL) ---
                st.markdown(
                    """
                    <div style="background-color: #E2E8F0; padding: 10px; border-radius: 4px; margin-top: 15px; margin-bottom: 15px; font-weight: bold; color: #0F172A;">
                        ⚙️ CUSTOS VARIÁVEIS (PERCENTUAIS SOBRE O PREÇO DE VENDA)
                    </div>
                    """, unsafe_allow_html=True
                )
                col_cv1, col_cv2, col_cv3, col_cv4 = st.columns(4)
                p_cartao = col_cv1.number_input("Taxas de Cartão (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="p_cartao_in")
                p_impostos = col_cv2.number_input("Impostos (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="p_impostos_in")
                p_embalagens = col_cv3.number_input("Embalagens (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="p_embalagens_in")
                p_comissao = col_cv4.number_input("Comissão (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="p_comissao_in")
                
                acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
                conn = get_connection()
                df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
                conn.close()
                
                # --- PROCESSAMENTO MATEMÁTICO FIEL AO MODELO EXCEL ---
                p_bruto = acao_row["peso_bruto"]
                p_comp_kg = acao_row["preco_animal_kg"]
                valor_total_compra = p_bruto * p_comp_kg
                tipo_animal_atual = acao_row["tipo_animal"]
                
                ossos_val = acao_row["ossos_muxiba"] or 0.0
                quebra_val = acao_row["quebra_nao_identificada"] or 0.0
                exsudato_val = acao_row["exsudato_escorrimento"] or 0.0
                peso_final = p_bruto - ossos_val - quebra_val - exsudato_val
                total_quebra = ossos_val + quebra_val + exsudato_val
                
                df_cortes_calc = df_cortes.copy()
                df_cortes_calc["Valor Total Venda"] = df_cortes_calc["peso"] * df_cortes_calc["preco_venda"]
                
                total_vendas_total = df_cortes_calc["Valor Total Venda"].sum()
                coeficiente = valor_total_compra / total_vendas_total if total_vendas_total > 0 else 0
                df_cortes_calc["Preço de Custo / KG"] = df_cortes_calc["preco_venda"] * coeficiente
                
                # Deduções exatas baseadas em percentual individual sobre o preço de venda
                df_cortes_calc["TAXAS DE CARTÃO"] = df_cortes_calc["preco_venda"] * (p_cartao / 100)
                df_cortes_calc["IMPOSTOS"] = df_cortes_calc["preco_venda"] * (p_impostos / 100)
                df_cortes_calc["EMBALAGENS"] = df_cortes_calc["preco_venda"] * (p_embalagens / 100)
                df_cortes_calc["COMISSÃO"] = df_cortes_calc["preco_venda"] * (p_comissao / 100)
                
                # Custo efetivo unificado por quilo e total por linha
                df_cortes_calc["Custo Efetivo por KG"] = (
                    df_cortes_calc["Preço de Custo / KG"] + 
                    df_cortes_calc["TAXAS DE CARTÃO"] + 
                    df_cortes_calc["IMPOSTOS"] + 
                    df_cortes_calc["EMBALAGENS"] + 
                    df_cortes_calc["COMISSÃO"]
                )
                df_cortes_calc["Custo Efetivo Total"] = df_cortes_calc["peso"] * df_cortes_calc["Custo Efetivo por KG"]
                df_cortes_calc["Lucro Bruto"] = df_cortes_calc["Valor Total Venda"] - df_cortes_calc["Custo Efetivo Total"]
                df_cortes_calc["Rendimento %"] = (df_cortes_calc["peso"] / peso_final) * 100 if peso_final > 0 else 0

                # Recálculo das variáveis consolidadas para os Indicadores
                total_vendas_ouro = df_cortes_calc[df_cortes_calc["qualidade"] == "OURO"]["Valor Total Venda"].sum()
                total_vendas_prata = df_cortes_calc[df_cortes_calc["qualidade"] == "PRATA"]["Valor Total Venda"].sum()
                compra_ouro = total_vendas_ouro * coeficiente
                compra_prata = total_vendas_prata * coeficiente
                
                peso_desossado_ouro = df_cortes_calc[df_cortes_calc["qualidade"] == "OURO"]["peso"].sum()
                peso_desossado_prata = df_cortes_calc[df_cortes_calc["qualidade"] == "PRATA"]["peso"].sum()
                peso_desossado_total = peso_desossado_ouro + peso_desossado_prata
                
                custo_efetivo_total_ouro = df_cortes_calc[df_cortes_calc["qualidade"] == "OURO"]["Custo Efetivo Total"].sum()
                custo_efetivo_total_prata = df_cortes_calc[df_cortes_calc["qualidade"] == "PRATA"]["Custo Efetivo Total"].sum()
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

                # Visualização da Apuração Geral do Lote
                st.subheader("📊 Apuração Geral do Lote")
                porc_ossos = (ossos_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_quebra = (quebra_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_exsudato = (exsudato_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_final = (peso_final / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_total_quebra = (total_quebra / p_bruto * 100) if p_bruto > 0 else 0.0
                
                apuracao_data = {
                    "Apuração do Lote": ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NÃO IDENTIF", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"],
                    "Peso (KG)": [f"{p_bruto:.3f}", f"{ossos_val:.3f}", f"{quebra_val:.3f}", f"{exsudato_val:.3f}", f"{peso_final:.3f}", f"{total_quebra:.3f}"],
                    "R$": [f"R$ {valor_total_compra:.2f}", "-", "-", "-", f"R$ {valor_total_compra:.2f}", "-"],
                    "Porcentagem": ["100,00%", f"{porc_ossos:.2f}%", f"{porc_quebra:.2f}%", f"{porc_exsudato:.2f}%", f"{porc_final:.2f}%", f"{porc_total_quebra:.2f}%"]
                }
                st.table(pd.DataFrame(apuracao_data).set_index("Apuração do Lote"))

                # Indicadores com Deduções Variáveis
                st.markdown("<div style='background-color: #22C55E; padding: 10px; border-radius: 4px; margin-top: 20px; color: #FFFFFF; font-weight: bold;'>🟩 Quadro de Indicadores (Com Deduções Variáveis)</div>", unsafe_allow_html=True)
                indicadores_data = {
                    "INDICADORES": [
                        "PREÇO TOTAL/Compra Sem Custos Variáveis", "PREÇO TOTAL/Venda", "Peso Desossado", 
                        "COEFICIENTE", "Custo Efetivo Total", "Margem de Contribuição R$", 
                        "Margem de Contribuição %", "Markup", "Preço médio de Compra/KG SEM-Custo Variável",
                        "Preço médio de Compra/KG COM-Custo Variável", "Preço médio de Venda/KG"
                    ],
                    "OURO": [f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f}", f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_ouro:.2f}", f"R$ {margem_r_ouro:.2f}", f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}", f"R$ {p_medio_compra_com_ouro:.2f}", f"R$ {p_medio_venda_ouro:.2f}"],
                    "PRATA": [f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f}", f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_prata:.2f}", f"R$ {margem_r_prata:.2f}", f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}", f"R$ {p_medio_compra_com_prata:.2f}", f"R$ {p_medio_venda_prata:.2f}"],
                    "Total": [f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f}", f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_geral:.2f}", f"R$ {margem_r_total:.2f}", f"{st_margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}", f"R$ {p_medio_compra_com_total:.2f}", f"R$ {p_medio_venda_total:.2f}"]
                }
                st.table(pd.DataFrame(indicadores_data).set_index("INDICADORES"))
                
                # Tabela Amarela - Rendimentos por Corte com os Custos Reais do Lote
                st.markdown("<div style='background-color: #EAB308; padding: 10px; border-radius: 4px; margin-top: 20px; color: #000000; font-weight: bold;'>🟨 Tabela de Rendimentos e Margens Efetivas por Corte</div>", unsafe_allow_html=True)
                df_exibir = df_cortes_calc.rename(columns={
                    "nome_corte": "Corte", "qualidade": "Qualidade", "peso": "Peso (KG)",
                    "preco_venda": "Preço Venda (R$/KG)", "Valor Total Venda": "Faturamento",
                    "Preço de Custo / KG": "Custo Base/KG", "Custo Efetivo por KG": "Custo Efet./KG",
                    "Custo Efetivo Total": "Custo Total Efetivo", "Lucro Bruto": "Margem Bruta (R$)",
                    "Rendimento %": "Rendimento %"
                })
                
                cols_ordem = ["Corte", "Qualidade", "Peso (KG)", "Preço Venda (R$/KG)", "Faturamento", "Custo Base/KG", "Custo Efet./KG", "Custo Total Efetivo", "Margem Bruta (R$)", "Rendimento %"]
                df_final_exibir = df_exibir[cols_ordem].copy()
                
                total_peso = df_final_exibir["Peso (KG)"].sum()
                total_faturamento = df_final_exibir["Faturamento"].sum()
                total_custo_efetivo = df_final_exibir["Custo Total Efetivo"].sum()
                total_margem_bruta = df_final_exibir["Margem Bruta (R$)"].sum()
                total_rendimento = df_final_exibir["Rendimento %"].sum()
                
                linha_total = pd.DataFrame([{
                    "Corte": "TOTAL SOMA", "Qualidade": "", "Peso (KG)": total_peso,
                    "Preço Venda (R$/KG)": None, "Faturamento": total_faturamento,
                    "Custo Base/KG": None, "Custo Efet./KG": None, "Custo Total Efetivo": total_custo_efetivo,
                    "Margem Bruta (R$)": total_margem_bruta, "Rendimento %": total_rendimento
                }])
                
                df_com_total = pd.concat([df_final_exibir, linha_total], ignore_index=True)
                
                def estilizar_margem_bruta(val):
                    try:
                        if isinstance(val, (int, float)) and val <= 0:
                            return 'background-color: #EF4444; color: #FFFFFF; font-weight: bold;'
                    except:
                        pass
                    return ''

                st.dataframe(df_com_total.style.format({
                    "Peso (KG)": "{:.3f}", "Preço Venda (R$/KG)": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-", 
                    "Faturamento": "R$ {:.2f}", "Custo Base/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-", 
                    "Custo Efet./KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-", "Custo Total Efetivo": "R$ {:.2f}",
                    "Margem Bruta (R$)": "R$ {:.2f}", "Rendimento %": "{:.2f}%"
                }).map(estilizar_margem_bruta, subset=["Margem Bruta (R$)"]))
                
                # --- 🖨️ RELATÓRIO PDF COMPLETO COM QUADRO DE CUSTOS VARIÁVEIS ---
                st.markdown("### 🖨️ Exportação de Relatórios")
                
                def gerar_pdf_lote_novo():
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=10)
                    
                    # Cabeçalho azul principal
                    pdf.set_fill_color(30, 58, 138)
                    pdf.rect(10, 10, 190, 15, "F")
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", style="B", size=11)
                    pdf.set_xy(10, 13.5)
                    pdf.cell(190, 8, "RENATO FRIGOTUDO & ASSOCIADOS", ln=1, align="C")
                    
                    pdf.set_text_color(15, 23, 42)
                    pdf.set_font("Arial", size=9)
                    pdf.set_xy(10, 27)
                    pdf.cell(190, 6, f"RELATORIO DE RENDIMENTO COM CUSTOS VARIAVEIS - LOTE #{id_selecionado}", ln=1, align="C")
                    
                    pdf.ln(8)
                    pdf.set_font("Arial", style="B", size=9)
                    pdf.cell(190, 6, "PERCENTUAIS DE DESPESAS INSERIDOS PELO USUARIO:", ln=1)
                    pdf.set_font("Arial", size=8)
                    pdf.cell(190, 5, f"Taxa de Cartao: {p_cartao}% | Impostos: {p_impostos}% | Embalagens: {p_embalagens}% | Comissao: {p_comissao}%", ln=1)
                    
                    pdf.ln(4)
                    pdf.set_fill_color(34, 197, 94)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", style="B", size=9)
                    pdf.cell(190, 6, "CUSTO EFETIVO CONSOLIDADO DO LOTE", ln=1, fill=True, align="C")
                    pdf.set_text_color(15, 23, 42)
                    pdf.set_font("Arial", size=8)
                    pdf.cell(95, 5, f"Faturamento Total Venda: R$ {total_vendas_total:.2f}", border=1)
                    pdf.cell(95, 5, f"Custo Efetivo Geral: R$ {custo_efetivo_total_geral:.2f}", border=1, ln=1)
                    pdf.cell(190, 5, f"Margem de Contribuicao Real do Lote: R$ {margem_r_total:.2f} ({st_margem_p_total*100:.2f}%)", border=1, ln=1)
                    
                    pdf.ln(5)
                    pdf.set_fill_color(234, 179, 8)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Arial", style="B", size=9)
                    pdf.cell(190, 6, "DETALHAMENTO DE CORTES E DESPESAS EFETIVAS", ln=1, fill=True, align="C")
                    
                    pdf.set_font("Arial", size=7)
                    pdf.cell(45, 5, "Corte", border=1, fill=True)
                    pdf.cell(15, 5, "Qualid.", border=1, align="C", fill=True)
                    pdf.cell(18, 5, "Peso (KG)", border=1, align="C", fill=True)
                    pdf.cell(24, 5, "P. Venda (KG)", border=1, align="C", fill=True)
                    pdf.cell(24, 5, "Custo Base/KG", border=1, align="C", fill=True)
                    pdf.cell(24, 5, "Custo Efet./KG", border=1, align="C", fill=True)
                    pdf.cell(40, 5, "Margem Bruta (R$)", border=1, align="C", fill=True)
                    pdf.ln()
                    
                    for _, row_p in df_cortes_calc.iterrows():
                        pdf.cell(45, 5, str(row_p["nome_corte"]), border=1)
                        pdf.cell(15, 5, str(row_p["qualidade"]), border=1, align="C")
                        pdf.cell(18, 5, f"{row_p['peso']:.3f}", border=1, align="C")
                        pdf.cell(24, 5, f"R$ {row_p['preco_venda']:.2f}", border=1, align="C")
                        pdf.cell(24, 5, f"R$ {row_p['Preço de Custo / KG']:.2f}", border=1, align="C")
                        pdf.cell(24, 5, f"R$ {row_p['Custo Efetivo por KG']:.2f}", border=1, align="C")
                        
                        m_val = row_p["Lucro Bruto"]
                        if m_val <= 0:
                            pdf.set_fill_color(239, 68, 68)
                            pdf.set_text_color(255, 255, 255)
                            pdf.cell(40, 5, f"R$ {m_val:.2f}", border=1, align="C", fill=True)
                            pdf.set_text_color(15, 23, 42)
                        else:
                            pdf.cell(40, 5, f"R$ {m_val:.2f}", border=1, align="C")
                        pdf.ln()
                        
                    return pdf.output(dest="S").encode("latin1")
                
                st.download_button(
                    label="📄 Baixar Relatório com Custos Efetivos (PDF)",
                    data=gerar_pdf_lote_novo(),
                    file_name=f"relatorio_custos_lote_{id_selecionado}.pdf",
                    mime="application/pdf"
                )
