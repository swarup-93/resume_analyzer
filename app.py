import streamlit as st
from utils.analyzer import extract_text, analyze_text
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(page_title="Resume Analyzer", page_icon="📄")
st.title("📄 Resume Analyzer with ATS Score & Feedback")

# Step 1: File upload
uploaded_file = st.file_uploader("Upload your Resume (.pdf or .txt)", type=["pdf", "txt"])

if uploaded_file:
    st.success("✅ Resume uploaded successfully!")

    # Step 2: Analyze Resume button
    if st.button("🔍 Analyze Resume"):
        try:
            # Step 3: Extract text
            resume_text = extract_text(uploaded_file)

            # Step 4: Analyze text using ATS logic
            ats_score, feedback, breakdown, suggestions = analyze_text(resume_text, file_type=uploaded_file.type.split('/')[-1])

            # If it's an error message (blank file)
            if ats_score == 0 and len(feedback) == 1 and "Error" in feedback[0]:
                st.error(feedback[0])
            else:
                # Step 5: Display ATS Score
                st.markdown(f"### 📊 ATS Score: **{ats_score}/100**")
                st.progress(ats_score / 100)  # Normalize score to be between 0 and 1

                # Step 6: Show Pie Chart for Score Breakdown
                st.markdown("### 🧁 ATS Score Breakdown")
                fig = go.Figure(data=[go.Pie(
                    labels=list(breakdown.keys()),
                    values=list(breakdown.values()),
                    hole=0.4,
                    textinfo='label+percent',
                    insidetextorientation='radial'
                )])
                fig.update_traces(pull=[0.05]*len(breakdown), marker=dict(line=dict(color='#000000', width=1)))
                fig.update_layout(
                    showlegend=True,
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)

                # Step 7: Show Feedback
                st.markdown("### 📌 Detailed Feedback")
                for item in feedback:
                    if "✅" in item:
                        st.success(item)
                    elif "❌" in item:
                        st.error(item)
                    else:
                        st.warning(item)

                # Step 8: Show AI Suggestions
                st.markdown("### Improvement Suggestions")
                for suggestion in suggestions:
                    st.info(suggestion)

                # Step 9: Downloadable feedback
                def generate_feedback_file(feedback_list, score, suggestions_list):
                    content = f"ATS Score: {score}/100\n\nDetailed Feedback:\n" + "\n".join(feedback_list)
                    content += "\n\nAI-Powered Suggestions:\n" + "\n".join(suggestions_list)
                    return content

                feedback_txt = generate_feedback_file(feedback, ats_score, suggestions)

                st.download_button("📥 Download Feedback Report", feedback_txt, file_name="resume_feedback.txt")
        except Exception as e:
            st.error(f"❌ Error analyzing resume: {str(e)}")

current_year = datetime.now().year

st.markdown(
    f"""
    <hr style="margin-top: 50px;">
    <div style='text-align: center; font-size: 13px; color: gray;'>
        © {current_year} Swarup Dhavan. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)