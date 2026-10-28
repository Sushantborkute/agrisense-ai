
import os
import html
import pyodbc
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="AgriSense AI | Farm Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM DESIGN
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --forest: #163D2B;
    --green: #28784B;
    --lime: #B9E769;
    --canvas: #F5F7F2;
    --ink: #17291F;
    --muted: #718075;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: var(--canvas);
    color: var(--ink);
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background: var(--forest);
}

[data-testid="stSidebar"] * {
    color: #F4F8F2;
}

.brand {
    font-family: 'Manrope', sans-serif;
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -0.8px;
    color: white;
}

.brand span {
    color: var(--lime);
}

.side-caption {
    color: #C4D5C7;
    font-size: 12px;
    line-height: 1.6;
}

.hero {
    background: linear-gradient(115deg, #163D2B 0%, #246542 70%, #347A4D 100%);
    padding: 28px 32px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 8px 25px rgba(22,61,43,0.10);
}

.hero h1 {
    color: white;
    font-family: 'Manrope', sans-serif;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0 0 8px 0;
}

.hero p {
    color: #DCEBDD;
    margin: 0;
    font-size: 14px;
}

.eyebrow {
    color: var(--lime);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.kpi {
    background: white;
    border: 1px solid #E5EBE2;
    border-radius: 16px;
    padding: 20px;
    min-height: 125px;
    box-shadow: 0 3px 12px rgba(25,54,34,0.035);
}

.kpi-label {
    color: #718075;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 12px;
}

.kpi-value {
    color: #173E2B;
    font-family: 'Manrope', sans-serif;
    font-size: 30px;
    font-weight: 800;
    line-height: 1.2;
}

.kpi-note {
    color: #718075;
    font-size: 11px;
    margin-top: 8px;
}

.section-title {
    font-family: 'Manrope', sans-serif;
    font-size: 20px;
    font-weight: 800;
    color: #193D2A;
    margin: 24px 0 4px 0;
}

.section-subtitle {
    color: #718075;
    font-size: 12px;
    margin-bottom: 14px;
}

.status-low {
    background: #FFF2E9;
    border: 1px solid #F3D4BF;
    border-radius: 12px;
    padding: 13px 16px;
    color: #88451F;
    font-size: 13px;
    margin: 8px 0;
}

.status-ok {
    background: #EAF5E9;
    border: 1px solid #D1E8D0;
    border-radius: 12px;
    padding: 13px 16px;
    color: #24613B;
    font-size: 13px;
    margin: 8px 0;
}

div.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid #DCE5DA;
}

div.stButton > button[kind="primary"] {
    background: #28784B;
    color: white;
    border: none;
}

[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #E5EBE2;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 12px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #E5EBE2;
    border-radius: 12px;
    overflow: hidden;
}

footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# MICROSOFT FOUNDRY CONNECTION
# ============================================================
@st.cache_resource
def get_foundry_client():
    return OpenAI(
        base_url=os.environ["FOUNDRY_ENDPOINT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
    )


# ============================================================
# MICROSOFT FABRIC CONNECTION
# ============================================================
def get_fabric_connection():
    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={os.environ['FABRIC_SERVER']};"
        f"Database={os.environ['FABRIC_DATABASE']};"
        "Authentication=ActiveDirectoryInteractive;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string, timeout=30)


@st.cache_data(ttl=60)
def get_farm_data():
    connection = get_fabric_connection()

    try:
        readings = pd.read_sql_query(
            """
            SELECT
                timestamp,
                farm_id,
                zone_id,
                crop_type,
                soil_moisture_pct,
                soil_temperature_c,
                air_temperature_c,
                humidity_pct,
                rainfall_mm
            FROM dbo.farm_sensor_readings
            """,
            connection,
        )

        statuses = pd.read_sql_query(
            "SELECT * FROM dbo.farm_zone_status",
            connection,
        )

        return readings, statuses

    finally:
        connection.close()


# ============================================================
# REUSABLE KPI CARD
# ============================================================
def show_kpi(label, value, note, icon):
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">
                {icon} &nbsp; {html.escape(str(label))}
            </div>
            <div class="kpi-value">
                {html.escape(str(value))}
            </div>
            <div class="kpi-note">
                {html.escape(str(note))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown(
        '<div class="brand">🌱 Agri<span>Sense</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="side-caption">FARM INTELLIGENCE PLATFORM</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "AI Chatbot"],
        label_visibility="visible",
    )

    st.divider()

    st.markdown("**DATA CONNECTIONS**")
    st.markdown("🟢 Microsoft Fabric")
    st.markdown("🟢 Microsoft Foundry")

    st.markdown(
        """
        <div class="side-caption">
        Sensor data is retrieved from your Lakehouse.
        Cached readings may be up to 60 seconds old.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        """
        <div class="side-caption">
        AgriSense AI · Demo build<br>
        The 25% moisture threshold is illustrative and
        requires calibration for local crop and soil conditions.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DASHBOARD PAGE
# ============================================================
if page == "Dashboard":

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">FARM OPERATIONS · OVERVIEW</div>
            <h1>Farm Intelligence Dashboard</h1>
            <p>
            Monitor sensor conditions, identify low-moisture zones,
            and explore farm data in one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    refresh_col, info_col = st.columns([1, 4])

    with refresh_col:
        if st.button(
            "↻ Refresh data",
            type="primary",
            use_container_width=True,
        ):
            get_farm_data.clear()
            st.rerun()

    with info_col:
        st.caption(
            "Source: AgriSenseLakehouse · "
            "Low-moisture demo threshold: below 25%"
        )

    try:
        readings, statuses = get_farm_data()

        if readings.empty:
            st.warning("No sensor readings were returned from Fabric.")

        else:
            # Normalize numeric columns
            numeric_columns = [
                "soil_moisture_pct",
                "soil_temperature_c",
                "air_temperature_c",
                "humidity_pct",
                "rainfall_mm",
            ]

            for column in numeric_columns:
                readings[column] = pd.to_numeric(
                    readings[column],
                    errors="coerce",
                )

            # ------------------------------------------------
            # FARM AND CROP FILTERS
            # ------------------------------------------------
            st.markdown(
                '<div class="section-title">Explore your farms</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-subtitle">'
                'Select a farm and crop to update the dashboard.'
                '</div>',
                unsafe_allow_html=True,
            )

            filter1, filter2 = st.columns(2)

            with filter1:
                farm_options = ["All farms"] + sorted(
                    readings["farm_id"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                selected_farm = st.selectbox(
                    "Filter by farm",
                    farm_options,
                    key="dashboard_farm_filter",
                )

            with filter2:
                crop_options = ["All crops"] + sorted(
                    readings["crop_type"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                selected_crop = st.selectbox(
                    "Filter by crop",
                    crop_options,
                    key="dashboard_crop_filter",
                )

            # Apply both filters to a single DataFrame
            display_data = readings.copy()

            if selected_farm != "All farms":
                display_data = display_data[
                    display_data["farm_id"].astype(str) == selected_farm
                ]

            if selected_crop != "All crops":
                display_data = display_data[
                    display_data["crop_type"].astype(str) == selected_crop
                ]

            # ------------------------------------------------
            # FILTER-AWARE KPI CARDS
            # ------------------------------------------------
            if display_data.empty:
                st.info(
                    "No sensor records match these filters. "
                    "Try selecting a different farm or crop."
                )

            else:
                low_moisture_data = display_data[
                    display_data["soil_moisture_pct"] < 25
                ]

                average_moisture = display_data[
                    "soil_moisture_pct"
                ].mean()

                average_temperature = display_data[
                    "air_temperature_c"
                ].mean()

                farm_count = display_data["farm_id"].nunique()

                zone_count = display_data[
                    ["farm_id", "zone_id"]
                ].drop_duplicates().shape[0]

                st.markdown(
                    '<div class="section-title">At a glance</div>',
                    unsafe_allow_html=True,
                )

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    show_kpi(
                        "Farm zones",
                        zone_count,
                        f"{farm_count} farm(s) represented",
                        "🗺️",
                    )

                with c2:
                    show_kpi(
                        "Low-moisture zones",
                        len(low_moisture_data),
                        "Below 25% demo threshold",
                        "💧",
                    )

                with c3:
                    show_kpi(
                        "Average soil moisture",
                        (
                            f"{average_moisture:.1f}%"
                            if pd.notna(average_moisture)
                            else "N/A"
                        ),
                        "Across filtered records",
                        "🌱",
                    )

                with c4:
                    show_kpi(
                        "Average air temperature",
                        (
                            f"{average_temperature:.1f}°C"
                            if pd.notna(average_temperature)
                            else "N/A"
                        ),
                        "Across filtered records",
                        "🌡️",
                    )

                # ------------------------------------------------
                # CHART AND LOW-MOISTURE ZONES
                # ------------------------------------------------
                left, right = st.columns([1.6, 1])

                with left:
                    st.markdown(
                        '<div class="section-title">'
                        'Soil moisture by zone</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        '<div class="section-subtitle">'
                        'Orange bars indicate readings below the '
                        '25% demo threshold.</div>',
                        unsafe_allow_html=True,
                    )

                    chart_data = display_data.copy()

                    chart_data["Zone"] = (
                        chart_data["farm_id"].astype(str)
                        + " · "
                        + chart_data["zone_id"].astype(str)
                    )

                    chart_data["Moisture status"] = (
                        chart_data["soil_moisture_pct"].apply(
                            lambda value: (
                                "Below threshold"
                                if pd.notna(value) and value < 25
                                else "At/above threshold"
                            )
                        )
                    )

                    fig = px.bar(
                        chart_data.sort_values("soil_moisture_pct"),
                        x="soil_moisture_pct",
                        y="Zone",
                        color="Moisture status",
                        orientation="h",
                        color_discrete_map={
                            "Below threshold": "#D97745",
                            "At/above threshold": "#4B9665",
                        },
                        labels={
                            "soil_moisture_pct": "Soil moisture (%)",
                            "Zone": "",
                            "Moisture status": "Status",
                        },
                        hover_data=[
                            "crop_type",
                            "farm_id",
                            "zone_id",
                        ],
                    )

                    fig.add_vline(
                        x=25,
                        line_dash="dash",
                        line_color="#B45309",
                        annotation_text="25% demo threshold",
                        annotation_position="top",
                    )

                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(
                            family="DM Sans",
                            color="#314739",
                        ),
                        margin=dict(l=0, r=10, t=35, b=10),
                        height=max(340, len(chart_data) * 32),
                        legend=dict(
                            orientation="h",
                            y=1.12,
                            x=0,
                        ),
                        xaxis=dict(
                            showgrid=True,
                            gridcolor="#E9EEE6",
                        ),
                        yaxis=dict(
                            categoryorder="total ascending",
                        ),
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                    )

                with right:
                    st.markdown(
                        '<div class="section-title">'
                        'Zones to review</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        '<div class="section-subtitle">'
                        'Low-moisture readings within the selected filters.'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    if low_moisture_data.empty:
                        st.markdown(
                            '<div class="status-ok">'
                            '✓ No readings are below the 25% demo threshold '
                            'for these filters.</div>',
                            unsafe_allow_html=True,
                        )

                    else:
                        for _, row in low_moisture_data.sort_values(
                            "soil_moisture_pct"
                        ).iterrows():

                            st.markdown(
                                f"""
                                <div class="status-low">
                                    <b>{html.escape(str(row["farm_id"]))}
                                    · {html.escape(str(row["zone_id"]))}</b><br>
                                    {html.escape(str(row["crop_type"]))}
                                    · Soil moisture:
                                    <b>{row["soil_moisture_pct"]:.1f}%</b><br>
                                    <span style="font-size:11px">
                                    Review field conditions and irrigation needs.
                                    </span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                # ------------------------------------------------
                # FILTERED SENSOR TABLE
                # ------------------------------------------------
                st.markdown(
                    '<div class="section-title">Sensor readings</div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="section-subtitle">'
                    'The table reflects your selected farm and crop filters.'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.dataframe(
                    display_data,
                    use_container_width=True,
                    hide_index=True,
                )

                # Download filtered report
                csv_data = display_data.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="⬇ Download filtered sensor report (CSV)",
                    data=csv_data,
                    file_name="agrisense_farm_sensor_report.csv",
                    mime="text/csv",
                    use_container_width=False,
                )

                
                st.markdown(
                    '<div class="section-title">AI Farm Health Report</div>',
                    unsafe_allow_html=True,
                )

                st.caption(
                    "Generate a report using the current farm and crop filters."
                )

                if st.button(
                    "🌱 Generate AI farm report",
                    type="primary",
                    key="generate_farm_report",
                ):
                    with st.spinner("Analyzing the filtered farm data..."):
                        try:
                            report_context = {
                                "selected_farm": selected_farm,
                                "selected_crop": selected_crop,
                                "sensor_readings": display_data.to_dict(
                                    orient="records"
                                ),
                                "low_moisture_zones": low_moisture_data.to_dict(
                                    orient="records"
                                ),
                            }

                            report_response = get_foundry_client().responses.create(
                                model=os.getenv(
                                    "FOUNDRY_MODEL",
                                    "gpt-4.1-mini",
                                ),
                                input=(
                                    "Create a concise, professional agricultural "
                                    "farm health report from the supplied data. "
                                    "Use these headings: Overview, Key Findings, "
                                    "Zones Requiring Attention, Recommended Checks, "
                                    "and Limitations. Use only the supplied sensor "
                                    "values. Treat soil moisture below 25% as an "
                                    "illustrative demo threshold, not a universal "
                                    "agronomic rule. Recommend field inspection "
                                    "before irrigation decisions. Do not claim "
                                    "that any action has been performed.\n\n"
                                    f"Farm data:\n{report_context}"
                                ),
                            )

                            st.session_state["farm_health_report"] = (
                                report_response.output_text
                            )

                        except Exception as error:
                            st.error("Unable to generate the AI farm report.")
                            st.code(str(error))

                if st.session_state.get("farm_health_report"):
                    report_text = st.session_state["farm_health_report"]

                    st.markdown("#### Generated report")
                    st.markdown(report_text)

                    st.download_button(
                        "⬇ Download AI farm report",
                        data=report_text,
                        file_name="agrisense_farm_health_report.md",
                        mime="text/markdown",
                        key="download_farm_health_report",
                    )


                with st.expander("View zone status records"):
                    st.dataframe(
                        statuses,
                        use_container_width=True,
                        hide_index=True,
                    )

    except Exception as error:
        st.error("Unable to load dashboard data from Microsoft Fabric.")
        st.caption(
            "Check your Microsoft sign-in and Fabric permissions."
        )
        st.code(str(error))


# ============================================================
# AI CHATBOT PAGE
# ============================================================
else:
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">AGRICULTURAL AI ASSISTANT</div>
            <h1>Ask AgriSense AI</h1>
            <p>
            Explore your farm sensor readings and get explanations
            grounded in data retrieved from Microsoft Fabric.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Suggested questions**")

    example_columns = st.columns(3)

    examples = [
        "Which zones have soil moisture below 25%?",
        "Show the latest readings for FARM_01.",
        "What should I check for ZONE_03?",
    ]

    for column, example in zip(example_columns, examples):
        with column:
            if st.button(example, use_container_width=True):
                st.session_state.pending_prompt = example

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm AgriSense AI. I can explain the farm sensor "
                    "readings available in your Fabric Lakehouse. "
                    "What would you like to explore?"
                ),
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask about farms, zones, soil moisture, or temperature..."
    )

    if not prompt and "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Checking your farm data..."):
                try:
                    readings, statuses = get_farm_data()

                    context = (
                        "You are AgriSense AI, an agricultural sensor assistant. "
                        "Use the provided Microsoft Fabric records as the source "
                        "of truth. Do not invent sensor values. If the records "
                        "do not answer the question, say so. The below-25% "
                        "soil-moisture threshold is illustrative and must be "
                        "calibrated for local crop and soil conditions.\n\n"
                        f"Sensor readings:\n"
                        f"{readings.to_dict(orient='records')}\n\n"
                        f"Zone status:\n"
                        f"{statuses.to_dict(orient='records')}"
                    )

                    response = get_foundry_client().responses.create(
                        model=os.getenv(
                            "FOUNDRY_MODEL",
                            "gpt-4.1-mini",
                        ),
                        input=f"{context}\n\nUser question: {prompt}",
                    )

                    answer = response.output_text

                    st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                except Exception as error:
                    st.error(
                        "Unable to retrieve farm data or generate an answer."
                    )
                    st.code(str(error))
