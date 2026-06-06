import streamlit as st
import duckdb
import os
import pandas as pd
from datetime import datetime, timezone, timedelta

# Set page configuration with a premium icon and responsive layout
st.set_page_config(
    page_title="Document Control Portal",
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
    
    /* Badge styling in sidebar */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 10px;
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
    # 1. Check if token is explicitly provided by environment
    if "MOTHERDUCK_TOKEN" in st.secrets:
        token = st.secrets["MOTHERDUCK_TOKEN"]
        conn_str = f"md:?motherduck_token={token}"
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

# Establish connection first
conn = None
connection_error = None

try:
    conn = get_motherduck_connection()
except Exception as e:
    connection_error = str(e)

# Sidebar Navigation Layout
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/document.png", width=64)
    st.markdown("### Document Control Hub")
    st.write("Navigasi aplikasi:")
    
    # Sidebar Dropdown Menu
    menu = st.selectbox(
        "Pilih Menu:",
        ["📊 Dashboard", "📝 Tambah Dokumen Baru"],
        index=0
    )

# Menu conditional rendering
if menu == "📝 Tambah Dokumen Baru":
    st.markdown('<div class="main-header">Document Control Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Kelola dokumen secara efisien pada database DC_DB (Zona Waktu WIB)</div>', unsafe_allow_html=True)
    
    # Display Connection Warnings
    if connection_error:
        st.error("❌ Gagal terhubung ke MotherDuck.")
        st.warning("Pastikan token MotherDuck telah diatur pada Streamlit Secrets atau Environment Variable `MOTHERDUCK_TOKEN`.")
        with st.expander("Detail Error"):
            st.code(connection_error)

    # Page Position / Breadcrumb Card
    st.markdown(f'<div class="glass-card">  {menu}</div>', unsafe_allow_html=True)
    with st.form("document_input_form", clear_on_submit=True):
        st.markdown("### 📝 Tambah Dokumen Baru")
        
        doc_id = st.text_input(
            "Doc_ID",
            placeholder="Contoh: AWE-001",
            help="Masukkan ID unik dokumen"
        )
        
        doc_type = st.text_input(
            "Doc_type",
            placeholder="Contoh: Manual HACCP, Manual GMP ",
            help="Jenis atau kategori dokumen"
        )
        
        doc_name = st.text_input(
            "Doc_name",
            placeholder="Contoh: HACCP, PRP - GMP Guide",
            help="Nama atau judul lengkap dokumen"
        )
        
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
                    # Trigger page reload to refresh table immediately
                    st.rerun()
                except Exception as ex:
                    st.error(f"Gagal menyimpan data: {ex}")



elif menu == "📊 Dashboard":
    st.markdown('<div class="main-header">Document Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Analitik dan metrik dokumen pada database DC_DB</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="glass-card">📍 <b>Posisi Saat Ini:</b> {menu}</div>', unsafe_allow_html=True)
    
    if connection_error:
        st.error("❌ Gagal terhubung ke MotherDuck.")
        st.warning("Pastikan token MotherDuck telah diatur pada Streamlit Secrets atau Environment Variable `MOTHERDUCK_TOKEN`.")
        with st.expander("Detail Error"):
            st.code(connection_error)
    elif conn:
        try:
            # Query data for dashboard
            df_dash = conn.execute("""
                SELECT doc_id, doc_type, doc_name, inserted_at 
                FROM DC_DB.main.documents
            """).df()
            
            if df_dash.empty:
                st.info("ℹ️ Belum ada data dokumen di database. Silakan gunakan menu **Input Form** untuk memasukkan dokumen pertama Anda.")
            else:
                # Calculations
                total_docs = len(df_dash)
                unique_types = df_dash['doc_type'].nunique()
                
                # Get latest document information
                latest_doc = df_dash.sort_values(by='inserted_at', ascending=False).iloc[0]
                latest_doc_name = f"{latest_doc['doc_name']} ({latest_doc['doc_id']})"
                
                # Render Metrics in layout cards
                m_col1, m_col2, m_col3 = st.columns(3)
                
                with m_col1:
                    st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
                    st.metric("Total Dokumen", total_docs)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with m_col2:
                    st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
                    st.metric("Tipe Dokumen Unik", unique_types)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with m_col3:
                    st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
                    st.metric("Dokumen Terbaru", latest_doc['doc_id'], help=latest_doc_name)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Charts columns
                c_col1, c_col2 = st.columns([1, 1])
                
                with c_col1:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown("### 📊 Dokumen Berdasarkan Tipe")
                    type_counts = df_dash['doc_type'].value_counts().reset_index()
                    type_counts.columns = ['Tipe', 'Jumlah']
                    st.bar_chart(type_counts.set_index('Tipe'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with c_col2:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown("### 📈 Tren Aktivitas Input (WIB)")
                    # Group by insertion date
                    df_dash['inserted_date'] = pd.to_datetime(df_dash['inserted_at']).dt.date
                    activity = df_dash.groupby('inserted_date').size().reset_index(name='Jumlah Dokumen')
                    activity = activity.sort_values('inserted_date')
                    st.area_chart(activity.set_index('inserted_date'))
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Gagal memuat Dashboard: {e}")
