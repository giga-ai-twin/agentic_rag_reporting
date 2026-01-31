import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random
from rag_agent import EVSmartFactoryAgent # Import our custom agent class
from slide_generator import SlideGenerator # For slide generation features

# === Page Configuration ===
st.set_page_config(
    page_title="AI-based Analytics Dashboard",
    page_icon="🏭",
    layout="wide", # Use wide layout for better dashboard visualization
    initial_sidebar_state="expanded"
)

# === CSS Styling (Global & Component Specific) ===
st.markdown("""
<style>
    /* Style for metric cards to give a tech-dashboard look */
    .stMetric {
        background-color: #0E1117;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #303030;
    }

    /* [CSS Hack] Center the chat input and fix it to the bottom.
       By default, st.chat_input is full-width. This overrides it to be 60% width and centered.
       The !important flag is necessary to override Streamlit's default shadow DOM styles. */
    div[data-testid="stChatInput"] {
        width: 80% !important;
        margin: auto !important;
        left: 0 !important;
        right: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# === Custom Avatar Icons (SVG Data URIs) ===
# Icon for user: Pinkish (#FF4B8B) background
USER_AVATAR = "https://api.dicebear.com/9.x/personas/svg?seed=Liam"


# Icon for bot: Tech Green (#00CC96) background
BOT_AVATAR = "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=Kingston"

# === 1. Initialize Agent (Cached for Performance) ===
@st.cache_resource
def load_agent():
    """
    Initializes and caches the EVSmartFactoryAgent instance.
    This prevents reloading the model and data on every interaction (button click/input).
    """
    return EVSmartFactoryAgent()

try:
    agent = load_agent()
except Exception as e:
    st.error(f"Failed to load agent: {e}. Please check your API Key configuration.")
    st.stop()

# === 2. Sidebar: Data Preview ===
with st.sidebar:
    st.title("🏭 Factory Data Hub")
    st.markdown("---")

    # Display dataset information
    st.subheader("Data Sources")
    for name, df in agent.dfs.items():
        with st.expander(f"{name} ({len(df)} rows)"):
            st.dataframe(df.head(5))

    st.markdown("---")
    st.info("💡 **Pro Tip:** This dashboard connects to live CSV data. The AI Agent has full access to these datasets for RAG analysis.")

# === 3. Main Dashboard Interface ===

st.title("⚡ Giga's EV Factory: AI-based Analytics System")
st.markdown("### Agentic RAG Reporting & Live Dashboard")

# Tab Layout: Chat Interface vs. Visual Dashboard
tab1, tab2 = st.tabs(["🤖 AI Analyst & Reporting (Chat)", "📊 Live Dashboard (Visuals)"])

# --- TAB 1: AI Analyst (Chat Interface) ---
with tab1:
    # Use columns to center the chat history view (1:3:1 ratio)
    # The chat input is handled separately by the CSS above to ensure it stays fixed at the bottom.
    col_left, col_center, col_right = st.columns([1, 7, 1])

    with col_center:
        # Initialize chat history in session state
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Initialize state for last response details (to survive reruns)
        if "last_response_content" not in st.session_state:
            st.session_state.last_response_content = None
        if "last_log_context" not in st.session_state:
            st.session_state.last_log_context = None
        if "last_csv_context" not in st.session_state:
            st.session_state.last_csv_context = None

        # Display chat history
        for message in st.session_state.messages:
            # Select avatar based on role
            avatar_icon = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
            with st.chat_message(message["role"], avatar=avatar_icon):
                st.markdown(message["content"])

    # Handle user input
    # Note: st.chat_input is placed outside columns to utilize the CSS 'fixed bottom' positioning
    if prompt := st.chat_input("Ask about yield rates, battery issues, or production risks..."):

        # 1. Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Manually specify 'col_center' to keep the message alignment consistent
        with col_center:
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(prompt)

        # 2. Display Assistant Response (with simulated reasoning animation)
        with col_center:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                # Create a placeholder for dynamic updates (Thinking -> Streaming Response)
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
                        # Display the thinking step with italic style
                        message_placeholder.markdown(f"⚙️ *{step}*")
                        # Add a small random delay to make it readable
                        time.sleep(random.uniform(0.5, 0.8))

                    # Final transition status
                    message_placeholder.markdown("⚡ *Finalizing Insights with Gemini...*")

                    # === Execution Phase: Call the API ===
                    response_stream = agent.ask(prompt)

                    # === Streaming Phase: Replace thought process with real answer ===
                    if response_stream:
                        for chunk in response_stream:
                            if chunk.text:
                                full_response += chunk.text
                                # Overwrite the placeholder with the accumulating response
                                message_placeholder.markdown(full_response + "▌")

                        # Final update without cursor
                        message_placeholder.markdown(full_response)

                        # Save full response to history
                        st.session_state.messages.append({"role": "assistant", "content": full_response})

                        # Save context to Session State so it survives button clicks
                        st.session_state.last_response_content = full_response
                        st.session_state.last_log_context = agent.last_log_context
                        st.session_state.last_csv_context = agent.last_csv_context

                        # Reset slide URL on new query
                        if 'slide_url' in st.session_state:
                            del st.session_state['slide_url']

                except Exception as e:
                    st.error(f"Error generating response: {e}")

    if st.session_state.last_response_content:
        with col_center:
            st.markdown("---")

            # Source viewer for debugging (optional)
            with st.expander("🔍 View Retrieved Context (Debug)"):
                tab_log, tab_csv = st.tabs(["📄 RAG Logs (Unstructured)", "📊 CSV Stats (Structured)"])

                with tab_log:
                    # Displays a log snippet that the Agent just captured.
                    st.code(agent.last_log_context, language="text")
                    if "No logs available" in agent.last_log_context:
                        st.caption("⚠️ No relevant logs found for this query.")
                    else:
                        st.caption("✅ Dynamic content retrieved from LlamaIndex.")

                with tab_csv:
                    # Display CSV statistical summary
                    st.text(agent.last_csv_context)
                    st.caption("✅ Static context from Pandas DataFrames.")

        # === Slide Generation Section ===
        st.markdown("---")
        col_btn, col_link = st.columns([1, 3])
        with col_btn:
            if st.button("📊 Export to Slides"):
                with st.spinner("Generating Google Slide Deck..."):
                    try:
                        # 1. Initialize generator
                        slider = SlideGenerator()
                        timestamp = time.strftime("%Y-%m-%d %H:%M")

                        # 2. Create a slide
                        deck_title = f"EV Factory Incident Report - {timestamp}"
                        pid, url = slider.create_presentation(deck_title)

                        # 3. Add a new content page (using what the Agent just said)
                        #    Treat the Agent's response as Bullet points.
                        slider.add_summary_slide(pid, f"Analysis summary", st.session_state.last_response_content)

                        st.success("Done!")
                        st.session_state['slide_url'] = url # Store it to avoid it disappearing during reorganization

                    except Exception as e:
                        st.error(f"Failed to generate slides: {e}")
                        st.info("Did you add 'service_account.json' to the root folder?")

        with col_link:
            if 'slide_url' in st.session_state:
                st.markdown(f"👉 **[Click to Open Google Slides]({st.session_state['slide_url']})**")

# --- TAB 2: Live Dashboard (Automated Visualization) ---
with tab2:
    st.markdown("#### Real-time KPI Overview")

    # Retrieve dataframes from the agent instance for visualization
    df_perf = agent.dfs['Performance']
    df_mfg = agent.dfs['Manufacturing']
    df_issues = agent.dfs['Issues']

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