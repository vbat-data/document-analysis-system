"""Streamlit dashboard for the Document Analysis System.

Thin client that talks to the FastAPI backend over HTTP.
Run the API first:  uvicorn src.main:app --reload
Then run this app:  streamlit run dashboard/app.py
"""
import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 300
MAX_FILE_SIZE_MB = 50

st.set_page_config(
    page_title="Document Analysis System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------
def api_health() -> dict[str, Any] | None:
    """Check API health. Returns None on error."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def api_upload(file_name: str, file_bytes: bytes) -> dict[str, Any] | None:
    """Upload a document for analysis."""
    try:
        files = {"file": (file_name, file_bytes, "application/octet-stream")}
        r = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            st.error(f"API error {r.status_code}: {r.text}")
            return None
        return r.json()
    except requests.RequestException as exc:
        st.error(f"Connection error: {exc}")
        return None


def api_list_documents(limit: int = 100) -> list[dict[str, Any]]:
    """Get list of processed documents."""
    try:
        r = requests.get(
            f"{API_URL}/documents",
            params={"limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return []


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
DOC_TYPE_EMOJI = {
    "contract": "📜",
    "invoice": "🧾",
    "act": "📋",
    "unknown": "❓",
}


def render_health_badge() -> None:
    """Show API connection status in the sidebar."""
    health = api_health()
    with st.sidebar:
        st.markdown("### 🔌 Состояние API")
        if health:
            st.success(f"Подключено · v{health['version']}")
            if health["models_loaded"]:
                st.info("🧠 ML-модель загружена")
            else:
                st.caption("🧠 ML-модель загрузится при первом запросе")
        else:
            st.error(f"Нет связи с {API_URL}")
            st.caption("Запустите: `uvicorn src.main:app --reload`")


def render_upload_tab() -> None:
    """Tab 1: upload and analyze a document."""
    st.markdown("### 📥 Загрузить документ")
    st.caption("Поддерживаются PDF, DOCX, XLSX · максимум 50 МБ")

    uploaded = st.file_uploader(
        "Выберите файл",
        type=["pdf", "docx", "xlsx"],
        label_visibility="collapsed",
    )

    if not uploaded:
        st.info("👆 Загрузите файл, чтобы запустить анализ")
        return

    file_bytes = uploaded.read()
    size_mb = len(file_bytes) / (1024 * 1024)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Файл:** `{uploaded.name}` · {size_mb:.2f} МБ")
    with col2:
        analyze_clicked = st.button("🔍 Анализировать", type="primary", use_container_width=True)

    if size_mb > MAX_FILE_SIZE_MB:
        st.error(f"Файл превышает {MAX_FILE_SIZE_MB} МБ")
        return

    if not analyze_clicked:
        return

    with st.spinner("Анализируем..."):
        result = api_upload(uploaded.name, file_bytes)

    if not result:
        return

    st.success(f"✅ Готово за {result['processing_time_sec']:.2f} сек")

    # -- Summary ------------------------------------------------------------
    doc_type = result["document_type"]
    emoji = DOC_TYPE_EMOJI.get(doc_type, "📄")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ID", result["document_id"])
    col2.metric("Тип", f"{emoji} {doc_type}")
    col3.metric("Сущностей", len(result["entities"]))
    col4.metric("Статус", "✅ Валиден" if result["validation"]["is_valid"] else "⚠️ Невалиден")

    st.divider()

    # -- Entities table -----------------------------------------------------
    st.markdown("#### 🔍 Извлечённые сущности")
    if result["entities"]:
        df = pd.DataFrame(result["entities"])
        df.columns = ["Тип", "Значение", "Уверенность"]
        df["Уверенность"] = df["Уверенность"].apply(lambda x: f"{x:.2%}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Сущности не найдены")

    # -- Validation ---------------------------------------------------------
    st.markdown("#### ✅ Результаты валидации")
    validation = result["validation"]

    if validation["is_valid"]:
        st.success("Документ прошёл все бизнес-правила")
    else:
        st.error(f"Отсутствуют обязательные поля: **{', '.join(validation['missing_fields'])}**")

    if validation["warnings"]:
        for warning in validation["warnings"]:
            st.warning(f"⚠️ {warning}")

    # -- Raw JSON -----------------------------------------------------------
    with st.expander("🗂 Сырой ответ API (JSON)"):
        st.json(result)


def render_documents_tab() -> None:
    """Tab 2: list of processed documents."""
    st.markdown("### 📚 Обработанные документы")

    if st.button("🔄 Обновить список"):
        st.rerun()

    documents = api_list_documents(limit=100)

    if not documents:
        st.info("Список пуст. Загрузите первый документ на вкладке выше.")
        return

    df = pd.DataFrame(documents)
    df["document_type"] = df["document_type"].apply(
        lambda t: f"{DOC_TYPE_EMOJI.get(t, '📄')} {t}"
    )
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    df.columns = ["ID", "Файл", "Тип", "Создан"]

    st.caption(f"Всего: {len(df)}")
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_stats_tab() -> None:
    """Tab 3: statistics."""
    st.markdown("### 📊 Статистика")

    documents = api_list_documents(limit=500)

    if not documents:
        st.info("Пока нет данных для статистики.")
        return

    df = pd.DataFrame(documents)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Распределение по типам**")
        type_counts = df["document_type"].value_counts()
        st.bar_chart(type_counts)

    with col2:
        st.markdown("**По датам**")
        df["date"] = pd.to_datetime(df["created_at"]).dt.date
        date_counts = df.groupby("date").size()
        st.line_chart(date_counts)

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего документов", len(df))
    col2.metric("Уникальных типов", df["document_type"].nunique())
    col3.metric("Самый частый тип", df["document_type"].mode()[0])


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
def main() -> None:
    st.title("📄 Document Analysis System")
    st.caption("AI-система анализа документов закупок · FastAPI + RuBERT + Streamlit")

    render_health_badge()

    tab1, tab2, tab3 = st.tabs(["📥 Загрузка", "📚 Документы", "📊 Статистика"])
    with tab1:
        render_upload_tab()
    with tab2:
        render_documents_tab()
    with tab3:
        render_stats_tab()


if __name__ == "__main__":
    main()