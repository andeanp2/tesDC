import streamlit as st
import duckdb
import os
import pandas as pd
from datetime import datetime, timezone, timedelta

# Set page configuration with a premium icon and responsive layout
st.set_page_config(
    page_title="Document Control - DC_DB",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS for modern UI design (Dark/Light mode compliant)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Global Font Overrides */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Gradient Header */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.6rem;
        margin-bottom: 0.2rem;
        text-align: left;
    }
    
    .subheader-text {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* Light theme adjustment for glassmorphism card */
    @media (prefers-color-scheme: light) {
        .glass-card {
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(0, 0, 0, 0.08);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        }
        .subheader-text {
            color: #475569;
        }
    }
    
    /* Badge styling */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-connected {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-disconnected {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# WIB (Western Indonesian Time) Timezone Setup
WIB = timezone(timedelta(hours=7))

# Initialize MotherDuck connection
def get_motherduck_connection(token=None):
    """
    Establishes a connection to MotherDuck.
    Checks parameters, Streamlit Secrets, then OS Environment variables.
    """
    # 1. Check if token is explicitly provided by UI
    if token:
        conn_str = f"md:?motherduck_token={token}"
    # 2. Check if token exists in Streamlit Secrets
    elif "MOTHERDUCK_TOKEN" in st.secrets:
        token = st.secrets["MOTHERDUCK_TOKEN"]
        conn_str = f"md:?motherduck_token={token}"
    # 3. Check if token exists in environment variables
    elif os.environ.get("MOTHERDUCK_TOKEN"):
        token = os.environ.get("MOTHERDUCK_TOKEN")
        conn_str = f"md:?motherduck_token={token}"
    else:
        # Fallback (will raise error if not authenticated locally)
        conn_str = "md:"
    
    # Establish connection
    conn = duckdb.connect(conn_str)
    
    # Ensure database DC_DB exists and switch context to it
    conn.execute("CREATE DATABASE IF NOT EXISTS DC_DB;")
    
    # Create target table if it does not exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS DC_DB.main.documents (
            doc_id VARCHAR,
            doc_type VARCHAR,
            doc_name VARCHAR,
            inserted_at TIMESTAMP
        );
    """)
    
    return conn

# Sidebar - Configuration and Connection Status
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/database.png", width=64)
    st.markdown("### Database Configuration")
    st.write("Aplikasi ini terhubung ke database cloud **MotherDuck** (`DC_DB`).")
    
    # Token input interface if not set in environment
    md_token_placeholder = ""
    token_configured = False
    
    if "MOTHERDUCK_TOKEN" in st.secrets or os.environ.get("MOTHERDUCK_TOKEN"):
        token_configured = True
        st.markdown(
            '<div class="status-badge status-connected">● Token Terdeteksi (Env/Secrets)</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="status-badge status-disconnected">● Token Tidak Ditemukan</div>',
            unsafe_allow_html=True
        )
        st.info("Masukkan token MotherDuck Anda di bawah ini untuk menghubungkan database.")
        
    user_token = st.text_input(
        "MotherDuck Token",
        value="",
        type="password",
        help="Dapatkan token Anda dari dashboard MotherDuck (motherduck.com)",
        placeholder="Paste token md:... di sini"
    )
    
    # Active Connection Check
    active_token = user_token if user_token else None
    
    st.markdown("---")
    st.markdown("### Panduan Deploy Streamlit Online")
    st.markdown("""
    Agar aplikasi terhubung otomatis saat dideploy secara online, tambahkan secret pada dashboard Streamlit Cloud:
    
    ```toml
    # Di Streamlit Secrets
    MOTHERDUCK_TOKEN = "your_actual_token_here"
    ```
    """)

# Main Content Layout
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown('<div class="main-header">Document Form</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Input data dokumen baru ke MotherDuck DC_DB (Zona Waktu WIB)</div>', unsafe_allow_html=True)
    
    # Initialize connection status
    conn = None
    connection_error = None
    
    try:
        conn = get_motherduck_connection(active_token)
        st.success("✅ Terkoneksi dengan MotherDuck online!")
    except Exception as e:
        connection_error = str(e)
        st.error("❌ Gagal terhubung ke MotherDuck.")
        st.warning("Silakan periksa Token MotherDuck Anda di menu sidebar.")
        with st.expander("Detail Error"):
            st.code(connection_error)

    # Input Form
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("document_input_form", clear_on_submit=True):
        st.markdown("### 📝 Tambah Dokumen Baru")
        
        doc_id = st.text_input(
            "Doc_ID",
            placeholder="Contoh: DOC-2026-001",
            help="Masukkan ID unik dokumen"
        )
        
        doc_type = st.text_input(
            "Doc_type",
            placeholder="Contoh: SOP, WI, Form, Policy",
            help="Jenis atau kategori dokumen"
        )
        
        doc_name = st.text_input(
            "Doc_name",
            placeholder="Contoh: Standard Operating Procedure Penjualan",
            help="Nama atau judul lengkap dokumen"
        )
        
        # WIB timestamp preview
        current_wib = datetime.now(WIB)
        st.caption(f"🕒 Timestamp input (WIB): **{current_wib.strftime('%Y-%m-%d %H:%M:%S')}**")
        
        submit_btn = st.form_submit_button("Simpan Data Dokumen", use_container_width=True)
        
        if submit_btn:
            if not conn:
                st.error("Tidak dapat menyimpan data. Silakan hubungkan database terlebih dahulu.")
            elif not doc_id.strip() or not doc_type.strip() or not doc_name.strip():
                st.warning("Semua field input (Doc_ID, Doc_type, Doc_name) wajib diisi!")
            else:
                try:
                    # Calculate input timestamp in WIB
                    input_timestamp = datetime.now(WIB)
                    
                    # Insert data into MotherDuck table
                    conn.execute(
                        "INSERT INTO DC_DB.main.documents (doc_id, doc_type, doc_name, inserted_at) VALUES (?, ?, ?, ?)",
                        (doc_id.strip(), doc_type.strip(), doc_name.strip(), input_timestamp)
                    )
                    
                    st.toast("🎉 Data berhasil disimpan ke MotherDuck!", icon="✅")
                    st.success(f"Data '{doc_name}' berhasil ditambahkan ke database!")
                except Exception as ex:
                    st.error(f"Gagal menyimpan data: {ex}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="main-header">Database View</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Data dokumen tersimpan di DC_DB.main.documents</div>', unsafe_allow_html=True)
    
    # Load and display recent entries from DB
    if conn:
        try:
            # Query the table
            query_result = conn.execute("""
                SELECT 
                    doc_id AS "Doc ID", 
                    doc_type AS "Doc Type", 
                    doc_name AS "Doc Name", 
                    inserted_at AS "Timestamp (WIB)" 
                FROM DC_DB.main.documents 
                ORDER BY inserted_at DESC
            """).df()
            
            if not query_result.empty:
                st.markdown(f"Total Dokumen: **{len(query_result)}**")
                
                # Format timestamp column for display
                # Convert TIMESTAMP in duckdb to human readable format
                query_result['Timestamp (WIB)'] = pd.to_datetime(query_result['Timestamp (WIB)']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Search filter
                search_query = st.text_input("🔍 Cari dokumen (ID, Tipe, atau Nama):", placeholder="Ketik kata kunci...")
                if search_query:
                    filtered_df = query_result[
                        query_result['Doc ID'].str.contains(search_query, case=False, na=False) |
                        query_result['Doc Type'].str.contains(search_query, case=False, na=False) |
                        query_result['Doc Name'].str.contains(search_query, case=False, na=False)
                    ]
                else:
                    filtered_df = query_result
                
                # Render table
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=450
                )
            else:
                st.info("ℹ️ Belum ada data dokumen di database. Gunakan form di sebelah kiri untuk menginput data pertama.")
        except Exception as e:
            st.error(f"Gagal mengambil data dari database: {e}")
    else:
        st.warning("⚠️ Hubungkan database MotherDuck untuk melihat isi data dokumen.")
