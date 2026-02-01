import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random
import os
import json
from datetime import datetime
from rag_agent import EVSmartFactoryAgent
from slide_generator import SlideGenerator
from feedback_manager import FeedbackManager

# === Page Configuration ===
st.set_page_config(
    page_title="AI-based Analytics Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS Styling ===
st.markdown("""
<style>
    .stMetric {
        background-color: #0E1117;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #303030;
    }
    div[data-testid="stChatInput"] {
        width: 80% !important;
        margin: auto !important;
        left: 0 !important;
        right: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# === Custom Avatars ===
USER_AVATAR = "https://api.dicebear.com/9.x/personas/svg?seed=Liam"
BOT_AVATAR = "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=Kingston"

# === 1. Initialize Agent ===
@st.cache_resource
def load_agent():
    return EVSmartFactoryAgent()

@st.cache_resource
def load_feedback_manager():
    return FeedbackManager()

try:
    agent = load_agent()
    feedback_manager = load_feedback_manager()
except Exception as e:
    st.error(f"Failed to load agent: {e}. Please check your API Key configuration.")
    st.stop()

# === 2. Sidebar ===
with st.sidebar:
    st.title("🏭 Factory Data Hub")
    st.markdown("---")

    # Data preview
    st.subheader("Data Sources")
    for name, df in agent.dfs.items():
        with st.expander(f"{name} ({len(df)} rows)"):
            st.dataframe(df.head(5))

    st.markdown("---")

    # Admin Area to view Feedback
    with st.expander("🔐 Admin: View Feedback"):
        feedback_data = feedback_manager.get_all_feedback()
        if feedback_data:
            st.dataframe(pd.DataFrame(feedback_data))
            if st.button("Clear Feedback Log"):
                feedback_manager.clear_log()
                st.rerun()
        else:
            st.text("No feedback collected yet.")

# === 3. Main Dashboard ===
st.title("⚡ Giga's EV Factory: AI-based Analytics System")
st.markdown("### Agentic RAG Reporting & Live Dashboard")

tab1, tab2 = st.tabs(["🤖 AI Analyst & Reporting (Chat)", "📊 Live Dashboard (Visuals)"])

# --- TAB 1: AI Analyst ---
with tab1:
    col_left, col_center, col_right = st.columns([1, 7, 1])

    with col_center:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # State variables for persistence
        if "last_query" not in st.session_state:
            st.session_state.last_query = None
        if "last_response_content" not in st.session_state:
            st.session_state.last_response_content = None
        if "last_plan" not in st.session_state:
            st.session_state.last_plan = None
        if "last_log_context" not in st.session_state:
            st.session_state.last_log_context = None
        if "last_csv_context" not in st.session_state:
            st.session_state.last_csv_context = None
        # Feedback state to prevent double voting
        if "feedback_given" not in st.session_state:
            st.session_state.feedback_given = False

        # Display chat history
        for message in st.session_state.messages:
            avatar_icon = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
            with st.chat_message(message["role"], avatar=avatar_icon):
                st.markdown(message["content"], unsafe_allow_html=True)

    # Handle User Input
    if prompt := st.chat_input("Ask about yield rates, battery issues, or production risks..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.last_query = prompt # Save query for feedback
        st.session_state.feedback_given = False # Reset feedback status for new query

        with col_center:
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(prompt, unsafe_allow_html=True)

        with col_center:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                message_placeholder = st.empty()
                full_response = ""

                # Define the simulated reasoning steps (Same as CLI version)
                thought_steps = [
                    "🔐 Authenticating with Secure Data Lake...",
                    "🔍 Retrieving Manufacturing Schemas...",
                    "📡 Querying Vehicle Telemetry DB...",
                    "🎫 Cross-referencing Quality Tickets...",
                    "📈 Running Correlation Analysis...",
                    "🚨 Detecting Anomalies in Sensor Data...",
                    "🧮 Calculating Yield Rates...",
                    "🧠 Optimizing Response Vector..."
                ]

                try:
                    # === Animation Phase: Simulate Chain of Thought ===
                    # Randomly select 3-5 steps to display
                    # This replaces st.spinner with a more "agentic" feel
                    selected_steps = random.sample(thought_steps, random.randint(3, 5))
                    for step in selected_steps:
                        message_placeholder.markdown(f"⚙️ *{step}*")
                        time.sleep(random.uniform(0.5, 0.8))

                    message_placeholder.markdown("⚡ *Finalizing Insights with Gemini...*")
                    # Execution
                    response_stream = agent.ask(prompt)

                    if response_stream:
                        for chunk in response_stream:
                            if hasattr(chunk, 'text') and chunk.text:
                                full_response += chunk.text
                                message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)

                        message_placeholder.markdown(full_response, unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})

                        # Save Context
                        st.session_state.last_response_content = full_response
                        if hasattr(agent, 'last_plan'):
                            st.session_state.last_plan = agent.last_plan
                        st.session_state.last_log_context = agent.last_log_context
                        st.session_state.last_csv_context = agent.last_csv_context

                        # Clear slide URL
                        if 'slide_url' in st.session_state:
                            del st.session_state['slide_url']

                except Exception as e:
                    st.error(f"Error: {e}")

    # === Post-Response Actions Area (Debug / Feedback / Export) ===
    if st.session_state.last_response_content:
        with col_center:
            st.markdown("---")

            # Only show if feedback hasn't been given yet for this interaction
            if not st.session_state.feedback_given:
                st.caption("Was this response helpful?")
                col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 5])

                with col_fb1:
                    if st.button("👍 Good"):
                        feedback_manager.save_feedback(st.session_state.last_query, st.session_state.last_response_content, "👍 Positive")
                        st.session_state.feedback_given = True
                        st.toast("Thanks for your feedback!", icon="✅")
                        st.rerun()

                with col_fb2:
                    if st.button("👎 Bad"):
                        feedback_manager.save_feedback(st.session_state.last_query, st.session_state.last_response_content, "👎 Negative")
                        st.session_state.feedback_given = True
                        st.toast("Thanks! We'll improve.", icon="🔧")
                        st.rerun()
            else:
                st.info("✅ Feedback received. Thank you!")

            # Debug Expander
            with st.expander("🧠 View Agent Thought Process (Debug)"):
                tab_plan, tab_log, tab_csv = st.tabs(["🧭 Planning", "📄 RAG Logs", "📊 CSV Stats"])

                with tab_plan:
                    if st.session_state.last_plan:
                        st.info(f"**Action:** {st.session_state.last_plan.get('action')}")
                        st.write(f"**Reasoning:** {st.session_state.last_plan.get('reason')}")
                    else:
                        st.text("No planning data.")

                with tab_log:
                    st.code(st.session_state.last_log_context or "No logs retrieved", language="text")

                with tab_csv:
                    st.text(st.session_state.last_csv_context or "No CSV data loaded")

            # Export Button
            st.markdown("#### Actions")
            col_btn, col_link = st.columns([1, 3])

            with col_btn:
                if st.button("📊 Export to Slides"):
                    with st.spinner("Generating Google Slide Deck..."):
                        try:
                            slider = SlideGenerator()
                            timestamp = time.strftime("%Y-%m-%d %H:%M")
                            deck_title = f"EV Manufacturer Weekly Report"
                            pid, url = slider.create_presentation(deck_title)

                            slider.add_summary_slide(
                                pid,
                                f"Analysis: {st.session_state.last_query}",
                                st.session_state.last_response_content
                            )

                            st.session_state['slide_url'] = url
                            st.success("Done!")

                        except Exception as e:
                            st.error(f"Failed: {e}")

            with col_link:
                if 'slide_url' in st.session_state:
                    st.markdown(f"👉 **[Click to Open Google Slides]({st.session_state['slide_url']})**")

# --- TAB 2: Live Dashboard ---
with tab2:
    st.markdown("#### Real-time KPI Overview")
    df_perf = agent.dfs.get('Performance', pd.DataFrame())
    df_mfg = agent.dfs.get('Manufacturing', pd.DataFrame())
    df_issues = agent.dfs.get('Issues', pd.DataFrame())

    # KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_soh = df_perf['Battery_SoH'].mean()
        st.metric("Avg Battery SoH", f"{avg_soh:.1f}%", delta="-1.2%" if avg_soh < 96 else "0.5%")
    with col2:
        # Calculate rework rate
        rework_rate = (len(df_mfg[df_mfg['Status'] == 'Rework_Needed']) / len(df_mfg)) * 100
        # Use inverse delta color because higher rework rate is bad
        st.metric("Rework Rate", f"{rework_rate:.1f}%", delta_color="inverse", delta=f"{rework_rate-5:.1f}% (vs Target)")
    with col3:
        total_issues = len(df_issues)
        critical_issues = len(df_issues[df_issues['Severity'] == 'Critical'])
        st.metric("Open Critical Issues", f"{critical_issues}", f"Total: {total_issues}")
    with col4:
        avg_build_time = df_mfg['Labor_Hours'].mean()
        st.metric("Avg Build Time", f"{avg_build_time:.1f} hrs")

    st.markdown("---")

    # Charts Section (Showcasing Plotly capabilities)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Battery Health by Firmware")
        # Box Plot: Ideal for visualizing distribution differences (e.g., v2.1.0 performance)
        fig_soh = px.box(df_perf, x="Firmware_Version", y="Battery_SoH",
                         color="Firmware_Version",
                         title="Impact of Firmware on Battery SoH")

        # Updated to use 'width="stretch"' instead of deprecated 'use_container_width=True'
        st.plotly_chart(fig_soh, width="stretch")

    with chart_col2:
        st.subheader("Issue Severity Distribution")
        # Pie Chart: Breakdown of quality issues
        fig_issues = px.pie(df_issues, names="Category",
                            title="Quality Issues Breakdown",
                            hole=0.4)

        st.plotly_chart(fig_issues, width="stretch")

    st.subheader("Production Timeline Analysis")
    # Scatter Plot: Correlation analysis between Manufacturing and Performance
    # Merging dataframes to find insights (e.g., Labor Hours vs. Battery Temp)
    merged_df = pd.merge(df_mfg, df_perf, on="VIN")

    fig_corr = px.scatter(merged_df, x="Labor_Hours", y="Battery_Temp_Avg",
                          color="Status",
                          size="System_Reboot_Count",
                          hover_data=["VIN", "Model"],
                          title="Correlation: Labor Hours vs. Battery Temp (Color=Status)",
                          # Custom color map: Red for Rework to highlight anomalies, Green for Success
                          color_discrete_map={
                              "Rework_Needed": "red",
                              "Success": "#00CC96"
                          })

    st.plotly_chart(fig_corr, width="stretch")