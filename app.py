import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from math import radians, sin, cos, sqrt, atan2


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using the Haversine formula."""
    r = 6371  # Earth radius in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


@st.cache_data
def load_data():
    file_path = "data/healthcare_facility_mapping_demo.csv"
    return pd.read_csv(file_path)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Healthcare Workflow & Systems Mapping",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("Healthcare Workflow & Systems Mapping")

st.markdown("""
A lightweight digital health systems prototype for visualizing healthcare facility locations,
TB referral pathways, nearest-facility access, and operational bottlenecks in service coordination.
""")


# ============================================================
# LOAD AND PREPARE DATA
# ============================================================

df = load_data()

lat_col = "latitude"
lon_col = "longitude"
name_col = "facility_label"
category_col = "facility_category"

df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")


# ============================================================
# PROJECT CONTEXT
# ============================================================

st.header("1. Project Context")

st.markdown("""
This dashboard is based on a TB patient pathway and Hospital DOTS Linkage assessment.
It focuses on facility mapping, referral coordination, and bottleneck identification across
the TB care pathway.

The prototype demonstrates how simple geospatial and workflow analytics can support
healthcare service planning, patient referral decisions, and operational systems improvement.
""")


# ============================================================
# SUMMARY METRICS
# ============================================================

st.header("2. Facility Mapping Overview")

total_facilities = len(df)
facility_categories = df[category_col].nunique()
mapped_facilities = df[[lat_col, lon_col]].dropna().shape[0]

col1, col2, col3 = st.columns(3)

col1.metric("Total Facilities", total_facilities)
col2.metric("Facility Categories", facility_categories)
col3.metric("Mapped Facilities", mapped_facilities)


# ============================================================
# FACILITY CATEGORY DISTRIBUTION
# ============================================================

st.subheader("Facility Category Distribution")

category_counts = df[category_col].value_counts().reset_index()
category_counts.columns = ["Facility Category", "Count"]

st.bar_chart(
    category_counts,
    x="Facility Category",
    y="Count"
)


# ============================================================
# DATA PREVIEW
# ============================================================

with st.expander("View Dataset Preview"):
    st.dataframe(df.head(), use_container_width=True)


# ============================================================
# FACILITY MAP AND NEAREST FACILITY FINDER
# ============================================================

st.header("3. Healthcare Facility Map")

st.markdown("""
Use the filters and simulated patient location below to identify nearby healthcare facilities.
The latitude and longitude fields can later be replaced with mobile GPS input.
""")

st.subheader("Simulated Patient / Community Location")

loc_col1, loc_col2 = st.columns(2)

with loc_col1:
    user_lat = st.number_input(
        "Current Latitude",
        value=26.899400,
        format="%.6f"
    )

with loc_col2:
    user_lon = st.number_input(
        "Current Longitude",
        value=68.092100,
        format="%.6f"
    )

st.caption(
    "This simulates a patient, community worker, or field location. "
    "Future versions can connect this input to GPS/mobile device location."
)

selected_categories = st.multiselect(
    "Filter Facilities by Category",
    options=df[category_col].dropna().unique(),
    default=df[category_col].dropna().unique()
)

filtered_df = df[df[category_col].isin(selected_categories)]
map_df = filtered_df.dropna(subset=[lat_col, lon_col])

if map_df.empty:
    st.warning("Please select at least one facility category to display the map.")

else:
    map_df = map_df.copy()

    map_df["Distance_km"] = map_df.apply(
        lambda row: calculate_distance_km(
            user_lat,
            user_lon,
            row[lat_col],
            row[lon_col]
        ),
        axis=1
    )

    nearest_facility = map_df.sort_values("Distance_km").iloc[0]

    st.success(
        f"Nearest selected facility: {nearest_facility[name_col]} "
        f"({nearest_facility['Distance_km']:.2f} km away)"
    )

    map_center = [
        map_df[lat_col].mean(),
        map_df[lon_col].mean()
    ]

    facility_map = folium.Map(
        location=map_center,
        zoom_start=10
    )

    folium.Marker(
        location=[user_lat, user_lon],
        popup="Simulated Patient / Field Location",
        tooltip="Simulated Patient / Field Location",
        icon=folium.Icon(color="red", icon="user")
    ).add_to(facility_map)

    for _, row in map_df.iterrows():
        facility_name = row[name_col]
        category = row[category_col]

        popup_text = f"""
        <b>{facility_name}</b><br>
        Category: {category}<br>
        Latitude: {row[lat_col]}<br>
        Longitude: {row[lon_col]}<br>
        Distance from selected location: {row['Distance_km']:.2f} km
        """

        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=popup_text,
            tooltip=facility_name,
            icon=folium.Icon(color="blue", icon="plus-sign")
        ).add_to(facility_map)

    st_folium(facility_map, width=1200, height=600)

    with st.expander("View Facilities Sorted by Distance"):
        distance_table = map_df[
            [name_col, category_col, lat_col, lon_col, "Distance_km"]
        ].sort_values("Distance_km")

        st.dataframe(distance_table, use_container_width=True)


# ============================================================
# WORKFLOW ANALYSIS
# ============================================================

st.header("4. TB Patient Referral Workflow")

col1, col2 = st.columns(2)

with col1:
    st.subheader("AS-IS Workflow")
    st.markdown("""
    1. Patient develops TB symptoms  
    2. Patient visits GP / OPD / informal provider  
    3. TB suspicion may be missed or delayed  
    4. Patient is referred for diagnostic screening  
    5. Sample collection or testing may be delayed  
    6. Confirmed case is linked to BMU / treatment center  
    7. Follow-up depends on patient return and provider tracking  
    """)

with col2:
    st.subheader("TO-BE Workflow")
    st.markdown("""
    1. Patient symptoms identified early  
    2. Standardized screening at OPD / GP / pharmacy level  
    3. Digital referral or structured referral slip generated  
    4. Patient linked to nearest diagnostic facility  
    5. Test result tracked and communicated  
    6. Confirmed case registered at BMU / DOTS center  
    7. Follow-up reminders and community tracking reduce LTFU  
    """)


# ============================================================
# BOTTLENECK ANALYSIS
# ============================================================

st.header("5. Bottleneck Analysis and Systems Recommendations")

bottlenecks = {
    "Workflow Stage": [
        "Symptom Recognition",
        "Initial Care Seeking",
        "Diagnostic Referral",
        "Testing Completion",
        "Treatment Initiation",
        "Follow-up"
    ],
    "Operational Bottleneck": [
        "Low awareness and delayed recognition",
        "Use of informal providers or quacks",
        "Weak referral linkages between providers and labs",
        "Patients may not complete sputum testing",
        "Pre-treatment loss after diagnosis",
        "Relocation, non-compliance, and weak tracking"
    ],
    "Systems Recommendation": [
        "Community awareness and screening prompts",
        "Provider sensitization and standardized triage",
        "Referral slips, digital logging, and facility linkage",
        "Sample transport support and patient reminders",
        "Immediate registration and treatment counseling",
        "Follow-up reminders and community worker linkage"
    ]
}

bottleneck_df = pd.DataFrame(bottlenecks)

st.dataframe(bottleneck_df, use_container_width=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.subheader("Disclaimer & Ethical Use Statement")

st.caption("""
This prototype has been developed solely for educational, academic, and portfolio demonstration purposes.

The work is inspired by healthcare systems and TB patient pathway assessments conducted during the developer's academic and consultancy-related work as part of a master's-level healthcare management project experience.

All analyses, workflow representations, visualizations, and system concepts presented in this prototype have been abstracted, simplified, modified, or recreated for demonstration purposes only. No confidential patient information, personally identifiable information (PII), sensitive operational records, or restricted institutional datasets are included within this application.

The project does not represent an official operational system, institutional dashboard, or live healthcare implementation platform. Any facility mapping or workflow representation shown is intended only to demonstrate concepts related to healthcare systems mapping, referral coordination, operational bottleneck analysis, and digital health workflow visualization.

This repository should not be interpreted as an official product, endorsement, or representation of any healthcare institution, donor, implementing partner, university, or government entity.
""")

st.caption(
    "Prototype developed for portfolio demonstration purposes. "
    "The project illustrates healthcare workflow mapping, facility geospatial visualization, "
    "nearest-facility analysis, and referral systems thinking."
)