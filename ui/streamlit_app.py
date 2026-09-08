import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import tempfile

from app.pipeline import process_documents

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Fact Knowledge Layer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- Global ---------- */
    .main {
        padding-top: 1.5rem;
    }

    #MainMenu, footer {visibility: hidden;}

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ---------- Header ---------- */
    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 60%, #a855f7 100%);
        border-radius: 20px;
        padding: 36px 40px;
        margin-bottom: 28px;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.25);
    }

    .hero-title {
        font-size: 38px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        font-size: 16px;
        color: rgba(255,255,255,0.88);
        margin-top: 8px;
        max-width: 720px;
        line-height: 1.5;
    }

    /* ---------- Section headers ---------- */
    .section-header {
        font-size: 22px;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 16px;
        color: #1f2937;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ---------- Metric cards ---------- */
    .metric-card {
        padding: 22px 16px;
        border-radius: 16px;
        border: 1px solid #eceef2;
        text-align: center;
        background: #ffffff;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
    }

    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #4338ca;
        margin: 0;
    }

    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 4px;
    }

    /* ---------- Document cards ---------- */
    .doc-card {
        padding: 16px 20px;
        border-radius: 14px;
        border: 1px solid #eceef2;
        background: #ffffff;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 4px rgba(15,23,42,0.03);
    }

    .doc-name {
        font-weight: 700;
        font-size: 15px;
        color: #1f2937;
    }

    .doc-meta {
        font-size: 13px;
        color: #6b7280;
        margin-top: 2px;
    }

    .pill {
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        background: #eef2ff;
        color: #4338ca;
        white-space: nowrap;
    }

    /* ---------- Evidence box ---------- */
    .evidence {
        background: #f8fafc;
        border-left: 4px solid #7c3aed;
        padding: 14px 16px;
        border-radius: 8px;
        font-size: 14px;
        color: #374151;
        font-style: italic;
        line-height: 1.5;
    }

    /* ---------- Confidence badge ---------- */
    .conf-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
    }

    .conf-high { background: #dcfce7; color: #166534; }
    .conf-mid  { background: #fef3c7; color: #92400e; }
    .conf-low  { background: #fee2e2; color: #991b1b; }

    /* ---------- Relationship badges ---------- */
    .rel-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
    }

    .rel-corroborates { background: #dcfce7; color: #166534; }
    .rel-reconciles   { background: #fef3c7; color: #92400e; }
    .rel-contradicts  { background: #fee2e2; color: #991b1b; }
    .rel-other        { background: #f1f5f9; color: #475569; }

    /* ---------- Upload box ---------- */
    section[data-testid="stFileUploaderDropzone"] {
        border-radius: 14px;
        border: 2px dashed #c7d2fe;
        background: #f8f9ff;
    }

    /* ---------- Buttons ---------- */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 700;
        padding: 0.6rem 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPERS
# ============================================================

def confidence_badge(value: float) -> str:
    """Return an HTML badge classed by confidence level."""
    if value >= 0.75:
        css_class = "conf-high"
    elif value >= 0.5:
        css_class = "conf-mid"
    else:
        css_class = "conf-low"
    return f'<span class="conf-badge {css_class}">{value:.2f}</span>'


REL_STYLE = {
    "CORROBORATES": ("🟢", "rel-corroborates"),
    "RECONCILES": ("🟡", "rel-reconciles"),
    "CONTRADICTS": ("🔴", "rel-contradicts"),
}


def rel_badge(relationship_type: str) -> str:
    icon, css_class = REL_STYLE.get(relationship_type, ("⚪", "rel-other"))
    return f'<span class="rel-badge {css_class}">{icon} {relationship_type}</span>'


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 🧠 Fact Knowledge Layer")
    st.caption("Document intelligence pipeline")

    st.markdown("---")
    st.markdown("#### How it works")
    st.markdown(
        """
        1. **Upload** one or more PDF documents
        2. **Analyze** to extract structured facts
        3. **Review** facts, evidence, and cross-document
           relationships
        """
    )

    st.markdown("---")

    if "analysis_result" in st.session_state:
        result = st.session_state["analysis_result"]
        st.markdown("#### Current session")
        st.write(f"📄 Documents: **{len(result.get('documents', []))}**")
        st.write(f"🧠 Facts: **{len(result.get('facts', []))}**")
        st.write(f"🔗 Relationships: **{len(result.get('relationships', []))}**")

        if st.button("🗑️ Clear results", use_container_width=True):
            del st.session_state["analysis_result"]
            st.rerun()


# ============================================================
# HERO HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🧠 Fact Knowledge Layer</div>
        <div class="hero-subtitle">
            Extract facts from documents, normalize them, trace them to
            evidence, and identify relationships across documents.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FILE UPLOAD
# ============================================================

upload_col, info_col = st.columns([3, 1])

with upload_col:
    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="You can select multiple PDF files at once."
    )

with info_col:
    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) ready")
    else:
        st.info("No files yet")


# ============================================================
# PROCESS DOCUMENTS
# ============================================================

if uploaded_files:

    with st.expander("📋 Selected files", expanded=False):
        for f in uploaded_files:
            st.write(f"• {f.name}  \u2014  {f.size / 1024:.1f} KB")

    if st.button(
        "🚀 Analyze Documents",
        type="primary",
        use_container_width=True
    ):

        temp_paths = []

        try:

            progress = st.progress(0, text="Preparing documents...")

            for i, uploaded_file in enumerate(uploaded_files):

                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf"
                )

                temp_file.write(uploaded_file.getbuffer())
                temp_file.close()

                temp_paths.append(temp_file.name)

                progress.progress(
                    int(((i + 1) / len(uploaded_files)) * 30),
                    text=f"Prepared {uploaded_file.name}"
                )

            with st.spinner("Extracting facts and analyzing relationships..."):
                progress.progress(60, text="Running extraction pipeline...")
                result = process_documents(temp_paths)
                progress.progress(100, text="Done!")

            st.session_state["analysis_result"] = result
            progress.empty()
            st.toast("Analysis complete!", icon="✅")
            st.rerun()

        except Exception as error:
            st.error(f"❌ Analysis failed: {error}")


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "analysis_result" in st.session_state:

    result = st.session_state["analysis_result"]

    documents = result.get("documents", [])
    facts = result.get("facts", [])
    relationships = result.get("relationships", [])

    # ========================================================
    # SUMMARY
    # ========================================================

    st.markdown('<div class="section-header">📊 Analysis Summary</div>', unsafe_allow_html=True)

    corroborated = sum(1 for r in relationships if r.relationship == "CORROBORATES")

    metrics = [
        ("Documents", len(documents)),
        ("Facts", len(facts)),
        ("Relationships", len(relationships)),
        ("Corroborated", corroborated),
    ]

    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <p class="metric-value">{value}</p>
                    <p class="metric-label">{label}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================================================
    # TABS
    # ========================================================

    tab_docs, tab_facts, tab_rels, tab_debug = st.tabs(
        ["📄 Documents", "🧠 Facts", "🔗 Relationships", "🔧 Debug"]
    )

    # ---------------- Documents tab ----------------
    with tab_docs:
        if not documents:
            st.info("No documents to display.")
        else:
            for document in documents:
                st.markdown(
                    f"""
                    <div class="doc-card">
                        <div>
                            <div class="doc-name">{document['document']}</div>
                            <div class="doc-meta">
                                Pages analyzed: {document['pages_processed']}
                            </div>
                        </div>
                        <div class="pill">{len(document['facts'])} facts</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # ---------------- Facts tab ----------------
    with tab_facts:
        if not facts:
            st.warning("No facts were extracted from the uploaded documents.")
        else:
            search = st.text_input(
                "🔍 Search facts",
                placeholder="Filter by subject, predicate, or value..."
            )

            filtered_facts = facts
            if search:
                q = search.lower()
                filtered_facts = [
                    f for f in facts
                    if q in f.subject.lower()
                    or q in f.predicate.lower()
                    or q in str(f.value_text).lower()
                ]

            st.caption(f"Showing {len(filtered_facts)} of {len(facts)} facts")

            for index, fact in enumerate(filtered_facts, start=1):

                header = f"{index}. **{fact.predicate}** — {fact.value_text}"

                with st.expander(header):

                    badge_html = confidence_badge(fact.confidence)
                    st.markdown(f"Confidence: {badge_html}", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Subject:**", fact.subject)
                        st.write("**Predicate:**", fact.predicate)
                        st.write("**Value:**", fact.value_text)
                        st.write("**Unit:**", fact.unit or "Not specified")

                    with col2:
                        normalized_value = (
                            fact.normalized_value
                            if fact.normalized_value is not None
                            else "Not available"
                        )
                        st.write("**Normalized value:**", normalized_value)

                        if fact.time:
                            st.write("**Time:**", fact.time.value or "Not specified")

                        st.write("**Scope:**", fact.scope or "Not specified")

                    st.markdown("**📌 Source Evidence**")
                    st.markdown(
                        f'<div class="evidence">{fact.source.text}</div>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"Source: {fact.source.document} | Page {fact.source.page}")

    # ---------------- Relationships tab ----------------
    with tab_rels:
        if not relationships:
            st.info("No relationships were found between the extracted facts.")
        else:
            for relationship in relationships:
                relationship_type = relationship.relationship
                badge_html = rel_badge(relationship_type)

                with st.expander(
                    f"{relationship_type} — Confidence {relationship.confidence:.2f}"
                ):
                    st.markdown(badge_html, unsafe_allow_html=True)
                    st.write("")
                    st.write("**Fact A:**", relationship.fact_a)
                    st.write("**Fact B:**", relationship.fact_b)
                    st.write("**Confidence:**", relationship.confidence)
                    st.write("**Reason:**", relationship.reason)

    # ---------------- Debug tab ----------------
    with tab_debug:
        st.write("Candidate pairs:", len(result.get("candidate_pairs", [])))
        st.write("Relationships:", len(relationships))
        st.json(
            {
                "documents": len(documents),
                "facts": len(facts),
                "relationships": len(relationships),
            }
        )

else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👆 Upload one or more PDF documents above to get started.")