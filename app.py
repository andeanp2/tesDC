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
    
    # Create target tables if they do not exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS DC_DB.main.documents (
            doc_id VARCHAR,
            doc_type VARCHAR,
            doc_name VARCHAR,
            inserted_at TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS DC_DB.main.document_logs (
            doc_id VARCHAR,
            doc_type VARCHAR,
            doc_name VARCHAR,
            revision_no VARCHAR,
            issue_date DATE,
            revision_date DATE,
            next_revision_date DATE,
            days_due INTEGER,
            revision_description VARCHAR,
            distribution VARCHAR,
            revision_status VARCHAR,
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
        ["📊 Dashboard", "📝 Dokumen ", "📋 Log Document"],
        index=0
    )

# Menu conditional rendering
if menu == "📝 Dokumen ":
    st.markdown('<div class="main-header">Document Control Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Kelola dokumen secara efisien pada database DC_DB (Zona Waktu WIB)</div>', unsafe_allow_html=True)
    
    # Display Connection Warnings
    if connection_error:
        st.error("❌ Gagal terhubung ke MotherDuck.")
        st.warning("Pastikan token MotherDuck telah diatur pada Streamlit Secrets atau Environment Variable `MOTHERDUCK_TOKEN`.")
        with st.expander("Detail Error"):
            st.code(connection_error)

    # Empty Glass Card
    st.markdown('<div class="glass-card"></div>', unsafe_allow_html=True)
    
    # Define Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Input Dokumen", "🗃️ Daftar Dokumen", "✏️ Edit Dokumen"])
    
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🗃️ Daftar Dokumen Tersimpan")
        
        # Load and display recent entries from DB
        if conn:
            try:
                query_result = conn.execute("""
                    SELECT 
                        doc_id AS "Doc ID", 
                        doc_type AS "Doc Type", 
                        doc_name AS "Doc Name"
                    FROM DC_DB.main.documents 
                    ORDER BY inserted_at DESC
                """).df()
                
                if not query_result.empty:
                    st.markdown(f"Total Dokumen: **{len(query_result)}**")
                    
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
                    st.info("ℹ️ Belum ada data dokumen di database. Silakan gunakan tab **Input Dokumen** untuk menginput data pertama.")
            except Exception as e:
                st.error(f"Gagal mengambil data dari database: {e}")
        else:
            st.warning("⚠️ Hubungkan database MotherDuck untuk melihat isi data dokumen.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ✏️ Edit Dokumen")
        
        if conn:
            try:
                # Query for list of document IDs & Names
                df_edit = conn.execute("SELECT doc_id, doc_name FROM DC_DB.main.documents ORDER BY inserted_at DESC").df()
                if df_edit.empty:
                    st.info("ℹ️ Belum ada dokumen yang dapat diedit. Silakan gunakan tab **Input Dokumen** terlebih dahulu.")
                else:
                    # Create options list for selectbox
                    doc_options = [f"{row['doc_id']} - {row['doc_name']}" for _, row in df_edit.iterrows()]
                    selected_doc_option = st.selectbox("Pilih Dokumen yang Ingin Diedit:", doc_options)
                    
                    # Extract selected Doc_ID
                    selected_doc_id = selected_doc_option.split(" - ")[0]
                    
                    # Fetch details
                    selected_doc_details = conn.execute(
                        "SELECT doc_id, doc_type, doc_name FROM DC_DB.main.documents WHERE doc_id = ?",
                        (selected_doc_id,)
                    ).df().iloc[0]
                    
                    # Edit Form
                    with st.form("edit_document_form", clear_on_submit=False):
                        new_doc_id = st.text_input("Doc_ID (Read-only)", value=selected_doc_details['doc_id'], disabled=True)
                        new_doc_type = st.text_input("Doc_type", value=selected_doc_details['doc_type'])
                        new_doc_name = st.text_input("Doc_name", value=selected_doc_details['doc_name'])
                        
                        save_btn = st.form_submit_button("Simpan Perubahan", use_container_width=True)
                        
                        if save_btn:
                            if not new_doc_type.strip() or not new_doc_name.strip():
                                st.warning("Doc_type dan Doc_name wajib diisi!")
                            else:
                                # Update database
                                update_timestamp = datetime.now(WIB)
                                conn.execute("""
                                    UPDATE DC_DB.main.documents 
                                    SET doc_type = ?, doc_name = ?, inserted_at = ? 
                                    WHERE doc_id = ?
                                """, (new_doc_type.strip(), new_doc_name.strip(), update_timestamp, selected_doc_id))
                                
                                st.toast("🎉 Dokumen berhasil diperbarui!", icon="✅")
                                st.success(f"Dokumen '{selected_doc_id}' berhasil diperbarui!")
                                st.rerun()
            except Exception as e:
                st.error(f"Gagal memuat form edit: {e}")
        else:
            st.warning("⚠️ Hubungkan database MotherDuck untuk mengedit data dokumen.")
        st.markdown('</div>', unsafe_allow_html=True)



elif menu == "📊 Dashboard":
    st.markdown('<div class="main-header">Document Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Analitik dan metrik dokumen pada database DC_DB</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card"></div>', unsafe_allow_html=True)
    
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
                st.info("ℹ️ Belum ada data dokumen di database. Silakan gunakan menu **Tambah Dokumen Baru** untuk memasukkan dokumen pertama Anda.")
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

elif menu == "📋 Log Document":
    st.markdown('<div class="main-header">Document Revision Logs</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader-text">Catat riwayat revisi dan status dokumen pada database DC_DB</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card"></div>', unsafe_allow_html=True)
    
    if connection_error:
        st.error("❌ Gagal terhubung ke MotherDuck.")
        st.warning("Pastikan token MotherDuck telah diatur pada Streamlit Secrets atau Environment Variable `MOTHERDUCK_TOKEN`.")
        with st.expander("Detail Error"):
            st.code(connection_error)
    elif conn:
        try:
            # Fetch doc_id, doc_type, and doc_name from documents table
            df_docs = conn.execute("SELECT doc_id, doc_type, doc_name FROM DC_DB.main.documents ORDER BY doc_id").df()
            
            if df_docs.empty:
                st.warning("⚠️ Belum ada dokumen di database. Silakan masuk ke menu **📝 Dokumen** untuk menambahkan dokumen terlebih dahulu.")
            else:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("### 📋 Log Document Baru")
                
                # Doc ID selection (Placed outside the form to trigger immediate rerun on value change)
                doc_ids = df_docs['doc_id'].tolist()
                selected_doc_id = st.selectbox("Pilih Doc ID:", doc_ids, help="Pilih Doc ID dari dokumen yang terdaftar")
                
                # Find details for the selected doc ID
                selected_row = df_docs[df_docs['doc_id'] == selected_doc_id].iloc[0]
                doc_type_val = selected_row['doc_type']
                doc_name_val = selected_row['doc_name']
                
                # Form for revision log inputs
                with st.form("log_document_form", clear_on_submit=True):
                    # Auto-filled read-only fields
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.text_input("Document Type", value=doc_type_val, disabled=True, help="Otomatis terisi berdasarkan Doc ID")
                    with col_t2:
                        st.text_input("Document Name", value=doc_name_val, disabled=True, help="Otomatis terisi berdasarkan Doc ID")
                    
                    revision_no = st.text_input("Revision No. ", placeholder="Contoh: Rev. 00, Rev. 01")
                    
                    col_d1, col_d2, col_d3 = st.columns(3)
                    with col_d1:
                        issue_date = st.date_input("Issue Date", value=datetime.now(WIB).date())
                    with col_d2:
                        revision_date = st.date_input("Revision Date", value=datetime.now(WIB).date())
                    with col_d3:
                        next_revision_date = st.date_input("Date of Next Revision", value=datetime.now(WIB).date() + timedelta(days=365))
                    
                    # Calculate Days until Due/Days Overdue dynamically
                    today = datetime.now(WIB).date()
                    days_due = (next_revision_date - today).days
                    if days_due >= 0:
                        due_status_text = f"⏳ {days_due} hari lagi sebelum jatuh tempo (Due)"
                    else:
                        due_status_text = f"⚠️ Telah jatuh tempo selama {-days_due} hari (Overdue)"
                    st.info(f"💡 Days until Due / Days Overdue: **{due_status_text}**")
                    
                    revision_description = st.text_area("Revision Description", placeholder="Masukkan deskripsi perubahan...")
                    distribution = st.text_input("Distribution", placeholder="Contoh: QC, QA, Production, HSE")
                    revision_status = st.selectbox("Revision Status", ["open", "closed"])
                    
                    submit_log_btn = st.form_submit_button("Simpan Log Dokumen", use_container_width=True)
                    
                    if submit_log_btn:
                        if not revision_no.strip() or not revision_description.strip() or not distribution.strip():
                            st.warning("Mohon lengkapi semua field input!")
                        else:
                            try:
                                log_timestamp = datetime.now(WIB)
                                # Insert data into document_logs table
                                conn.execute("""
                                    INSERT INTO DC_DB.main.document_logs (
                                        doc_id, doc_type, doc_name, revision_no, 
                                        issue_date, revision_date, next_revision_date, 
                                        days_due, revision_description, distribution, 
                                        revision_status, inserted_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    selected_doc_id, doc_type_val, doc_name_val, revision_no.strip(),
                                    issue_date, revision_date, next_revision_date,
                                    days_due, revision_description.strip(), distribution.strip(),
                                    revision_status, log_timestamp
                                ))
                                st.toast("🎉 Log dokumen berhasil disimpan!", icon="✅")
                                st.success("Log dokumen baru berhasil ditambahkan!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Gagal menyimpan log: {ex}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Show all revision logs
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("### 🗃️ Daftar Log Revisi Dokumen")
                
                query_logs = conn.execute("""
                    SELECT 
                        doc_id AS "Doc ID",
                        doc_type AS "Document Type",
                        doc_name AS "Document Name",
                        revision_no AS "Revision No.",
                        issue_date AS "Issue Date",
                        revision_date AS "Revision Date",
                        next_revision_date AS "Date of Next Revision",
                        days_due AS "Days until Due/Days Overdue",
                        revision_description AS "Revision Description",
                        distribution AS "Distribution",
                        revision_status AS "Revision Status"
                    FROM DC_DB.main.document_logs
                    ORDER BY inserted_at DESC
                """).df()
                
                if not query_logs.empty:
                    st.markdown(f"Total Log: **{len(query_logs)}**")
                    
                    # Format date columns to string
                    query_logs['Issue Date'] = pd.to_datetime(query_logs['Issue Date']).dt.strftime('%Y-%m-%d')
                    query_logs['Revision Date'] = pd.to_datetime(query_logs['Revision Date']).dt.strftime('%Y-%m-%d')
                    query_logs['Date of Next Revision'] = pd.to_datetime(query_logs['Date of Next Revision']).dt.strftime('%Y-%m-%d')
                    
                    # Search bar
                    search_log = st.text_input("🔍 Cari Log (Doc ID, Deskripsi, Status, dll):", placeholder="Ketik kata kunci pencarian...")
                    if search_log:
                        filtered_logs = query_logs[
                            query_logs['Doc ID'].str.contains(search_log, case=False, na=False) |
                            query_logs['Document Type'].str.contains(search_log, case=False, na=False) |
                            query_logs['Document Name'].str.contains(search_log, case=False, na=False) |
                            query_logs['Revision Description'].str.contains(search_log, case=False, na=False) |
                            query_logs['Revision Status'].str.contains(search_log, case=False, na=False)
                        ]
                    else:
                        filtered_logs = query_logs
                        
                    st.dataframe(filtered_logs, use_container_width=True)
                else:
                    st.info("ℹ️ Belum ada log revisi untuk dokumen yang tersimpan.")
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Gagal memuat data log dokumen: {e}")
