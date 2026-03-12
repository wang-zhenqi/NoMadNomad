"""Streamlit 入口：项目仪表板、需求分析、提案管理、看板."""

import streamlit as st


def main() -> None:
    """Streamlit 主入口."""
    st.set_page_config(
        page_title="NoMadNomad",
        page_icon="🧭",
        layout="wide",
    )
    st.title("NoMadNomad")
    st.caption("AI 驱动的自由职业者全流程项目管理")
    st.write("项目仪表板、需求分析、提案管理、看板将在此实现。")


if __name__ == "__main__":
    main()
