# Add this at the very top of your app.py file
import streamlit as st
import sys
import subprocess

# Install required packages
required_packages = ['matplotlib', 'seaborn', 'pandas']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Now import what you need from these packages
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import time
import re

# Set page configuration
st.set_page_config(
    page_title="Survey Results Query Demo",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .subheader {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .results-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .highlight-text {
        background-color: #f0f7ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #4c78a8;
        margin-bottom: 10px;
    }
    .status-complete {
        color: white;
        background-color: #28a745;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .status-pending {
        color: white;
        background-color: #ffc107;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .status-missing {
        color: white;
        background-color: #dc3545;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Store Survey Results Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Ask questions about store visits and compliance</div>', unsafe_allow_html=True)

# Load data
@st.cache_data
def load_survey_data():
    try:
        df = pd.read_csv("SurveyResultsExtractShort.csv", encoding='cp1252')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Process the data
@st.cache_data
def process_data(df):
    # Clean column names (remove whitespace)
    df.columns = [col.strip() for col in df.columns]
    
    # Convert date columns if needed
    if 'Activity Date' in df.columns:
        try:
            df['Activity Date'] = pd.to_datetime(df['Activity Date'], errors='coerce')
        except:
            pass
    
    return df

# Get data
survey_data = load_survey_data()
if not survey_data.empty:
    survey_data = process_data(survey_data)

# Input for natural language query
query = st.text_input(
    "Ask a question about the survey results:",
    placeholder="Example: 'How many stores have not been visited?' or 'Which stores didn't have a flyer?'",
    key="query_input"
)

# Example queries
with st.expander("Example queries you can ask"):
    st.write("- \"How many stores have not been visited?\"")
    st.write("- \"Which stores didn't have a flyer?\"")
    st.write("- \"Summarize the comments about the flyer\"")

# Process query button
if st.button("Ask", key="process_button") or query:
    if query and not survey_data.empty:
        with st.spinner("Processing query..."):
            # Add a small delay to simulate processing
            time.sleep(0.8)
            
            # Convert query to lowercase for easier matching
            query_lower = query.lower()
            
            # Query 1: Stores not visited (Status = "Not Completed")
            if any(keyword in query_lower for keyword in ["not visited", "not been visited", "unvisited"]):
                if "Status" in survey_data.columns:
                    # Filter for not completed stores
                    not_visited = survey_data[survey_data["Status"].str.lower().str.contains("not completed", na=False)]
                    
                    # Display results
                    st.subheader("Stores Not Visited")
                    
                    # Display metrics
                    total_stores = len(survey_data)
                    not_visited_count = len(not_visited)
                    visit_rate = ((total_stores - not_visited_count) / total_stores) * 100
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Not Visited", f"{not_visited_count} of {total_stores}")
                    with col2:
                        st.metric("Completion Rate", f"{visit_rate:.1f}%")
                        
                    # Progress bar
                    st.progress((total_stores - not_visited_count) / total_stores)
                    
                    # Display table of not visited stores
                    if not not_visited.empty:
                        display_df = not_visited[["Site Code", "Site Name", "Status", "Banner Name"]].copy()
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.success("All stores have been visited!")
                else:
                    st.error("Cannot find status information in the survey data.")
            
            # Query 2: Stores without flyers
            elif any(keyword in query_lower for keyword in ["flyer", "didn't have", "without flyer", "no flyer"]):
                if "Where you able to find the flyer?" in survey_data.columns:
                    flyer_col = "Where you able to find the flyer?"
                    
                    # Filter for stores where flyer was not found
                    no_flyer = survey_data[survey_data[flyer_col].str.lower().str.contains("no", na=False)]
                    
                    st.subheader("Stores Without Flyers")
                    
                    # Display metrics
                    total_responses = len(survey_data.dropna(subset=[flyer_col]))
                    no_flyer_count = len(no_flyer)
                    flyer_rate = ((total_responses - no_flyer_count) / total_responses) * 100 if total_responses > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("No Flyer", f"{no_flyer_count} of {total_responses}")
                    with col2:
                        st.metric("Flyer Availability Rate", f"{flyer_rate:.1f}%")
                    
                    # Display chart
                    flyer_counts = survey_data[flyer_col].value_counts()
                    fig, ax = plt.subplots(figsize=(8, 6))
                    flyer_counts.plot.pie(autopct='%1.1f%%', ax=ax)
                    ax.set_title("Flyer Availability")
                    ax.set_ylabel("")
                    st.pyplot(fig)
                    
                    # Display table of stores without flyers
                    if not no_flyer.empty:
                        display_df = no_flyer[["Site Code", "Site Name", "Banner Name", "Status"]].copy()
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.success("All stores have flyers!")
                else:
                    st.error("Cannot find flyer information in the survey data.")
            
            # Query 3: Summarize flyer comments
            elif any(keyword in query_lower for keyword in ["comment", "summarize"]) and "flyer" in query_lower:
                comment_col = "Provide notes and what was discussed with the store staff if the flyer was not found."
                if comment_col in survey_data.columns:
                    # Filter for non-empty comments
                    flyer_comments = survey_data[~survey_data[comment_col].isna()]
                    flyer_comments = flyer_comments[flyer_comments[comment_col].str.strip() != ""]
                    
                    st.subheader("Flyer Comments Summary")
                    
                    # Display metrics
                    total_comments = len(flyer_comments)
                    total_stores = len(survey_data)
                    
                    st.metric("Stores with Flyer Comments", f"{total_comments} of {total_stores}")
                    
                    if not flyer_comments.empty:
                        # Try to identify common words/themes in comments
                        all_comments = " ".join(flyer_comments[comment_col].fillna("").str.lower())
                        common_words = ["flyer", "not", "found", "store", "the", "and", "was", "for", "with", "have", "had"]
                        words = [word for word in re.findall(r'\b\w+\b', all_comments) if word not in common_words and len(word) > 3]
                        word_counts = Counter(words).most_common(10)
                        
                        if word_counts:
                            # Display common themes
                            st.subheader("Common Themes in Flyer Comments")
                            theme_data = pd.DataFrame(word_counts, columns=["Term", "Frequency"])
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            sns.barplot(x="Frequency", y="Term", data=theme_data, ax=ax)
                            ax.set_title("Frequently Mentioned Terms in Flyer Comments")
                            st.pyplot(fig)
                        
                        # Display all comments
                        st.subheader("All Flyer Comments")
                        for _, row in flyer_comments.iterrows():
                            st.markdown(f"""
                            <div class="highlight-text">
                                <strong>{row['Site Name']} (Code: {row['Site Code']})</strong><br>
                                {row[comment_col]}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No comments found regarding flyers.")
                else:
                    st.error("Cannot find flyer comment information in the survey data.")
            
            # Default response if no query matches
            else:
                st.warning("""
                I couldn't understand your question. Please try one of the following:
                - "How many stores have not been visited?"
                - "Which stores didn't have a flyer?"
                - "Summarize the comments about the flyer"
                """)
    
    elif survey_data.empty:
        st.error("Survey data could not be loaded. Please check the file and try again.")
    else:
        st.info("Please enter a query above.")

# Footer
st.markdown("---")
st.caption("Store Survey Results Analysis | Created for demonstration purposes")
