import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import azure.cognitiveservices.speech as speechsdk
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# ==========================================================
# 🔐 AZURE CONFIG
# ==========================================================

AZURE_SPEECH_KEY = "key"
AZURE_SPEECH_REGION = "koreacentral"

AZURE_LANG_KEY = "key"
AZURE_LANG_ENDPOINT = "https://endpoint.azure.com/"

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="AI Feedback Analyzer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================================
#  CSS
# ==========================================================

st.markdown("""
<style>

/* Main App */
html, body, [class*="css"]{
    background: radial-gradient(circle at top left,#0f172a,#020617 55%);
    color:white;
    font-family: Inter, sans-serif;
}

/* Center App */
.block-container{
    max-width:1200px;
    padding-top:2rem;
    padding-bottom:2rem;
}

/* Remove Streamlit Top Space */
header{visibility:hidden;}
footer{visibility:hidden;}

/* Hero Section */
.hero{
    text-align:center;
    padding:40px 30px;
    border-radius:28px;
    background:rgba(255,255,255,0.05);
    border:1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(18px);
    box-shadow:0 20px 40px rgba(0,0,0,0.35);
    margin-bottom:28px;
}

.hero h1{
    font-size:52px;
    margin:0;
    color:#38bdf8;
    font-weight:800;
    letter-spacing:-1px;
}

.hero p{
    margin-top:14px;
    font-size:18px;
    color:#cbd5e1;
}

/* Glass Cards */
.card{
    background:rgba(255,255,255,0.04);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:24px;
    padding:28px;
    box-shadow:0 18px 32px rgba(0,0,0,0.28);
    transition:all .25s ease;
    margin-bottom:22px;
}

.card:hover{
    transform:translateY(-4px);
    box-shadow:0 22px 38px rgba(56,189,248,.18);
}

/* Textarea */
textarea, .stTextArea textarea{
    border-radius:18px !important;
    padding:18px !important;
    font-size:17px !important;
    background:rgba(255,255,255,0.05) !important;
    color:white !important;
    border:1px solid rgba(255,255,255,0.08) !important;
}

textarea:focus{
    border:1px solid #38bdf8 !important;
    box-shadow:0 0 0 3px rgba(56,189,248,.22);
}

/* Buttons */
.stButton > button{
    width:100%;
    height:54px;
    border:none;
    border-radius:16px;
    font-size:17px;
    font-weight:700;
    color:white;
    background:linear-gradient(90deg,#0ea5e9,#2563eb);
    box-shadow:0 12px 22px rgba(37,99,235,.35);
    transition:all .25s ease;
}

.stButton > button:hover{
    transform:translateY(-3px);
    box-shadow:0 18px 30px rgba(56,189,248,.45);
}

/* Metrics */
[data-testid="metric-container"]{
    background:rgba(255,255,255,0.05);
    border:1px solid rgba(255,255,255,0.08);
    padding:20px;
    border-radius:22px;
    box-shadow:0 14px 26px rgba(0,0,0,.18);
}

/* Headings */
h2,h3{
    color:white;
}

/* Footer */
.footerx{
    text-align:center;
    color:#94a3b8;
    padding-top:30px;
    font-size:14px;
}

/* Responsive */
@media(max-width:768px){
.hero h1{font-size:34px;}
.hero p{font-size:15px;}
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# CLIENT
# ==========================================================

@st.cache_resource
def get_client():
    return TextAnalyticsClient(
        endpoint=AZURE_LANG_ENDPOINT,
        credential=AzureKeyCredential(AZURE_LANG_KEY)
    )

client = get_client()

# ==========================================================
# FUNCTIONS
# ==========================================================

def analyze_sentiment(text):
    response = client.analyze_sentiment(documents=[text])[0]

    return {
        "sentiment": response.sentiment.upper(),
        "positive": round(response.confidence_scores.positive * 100, 2),
        "neutral": round(response.confidence_scores.neutral * 100, 2),
        "negative": round(response.confidence_scores.negative * 100, 2),
    }


def speech_input():
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )

    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    return ""


def overall_score(result):
    if result["sentiment"] == "POSITIVE":
        return max(85, result["positive"])
    elif result["sentiment"] == "NEGATIVE":
        return min(35, 100 - result["negative"])
    else:
        return 60


def gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "/100"},
        title={'text': "Overall Review Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#38bdf8"},
            'steps': [
                {'range': [0, 40], 'color': "#7f1d1d"},
                {'range': [40, 70], 'color': "#854d0e"},
                {'range': [70, 100], 'color': "#14532d"}
            ]
        }
    ))

    fig.update_layout(
        height=340,
        margin=dict(l=10,r=10,t=40,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white"
    )
    return fig


# ==========================================================
# HERO HEADER
# ==========================================================

st.markdown("""
<div class="hero">
<h1>🎙️ AI Customer Feedback Analyzer</h1>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# INPUT SECTION CENTERED
# ==========================================================


st.subheader("✍️ Enter Customer Review")

text = st.text_area(
    "",
    height=220,
    placeholder="Example: Product quality is excellent but delivery was slow..."
)

b1, b2 = st.columns(2, gap="medium")

with b1:
    if st.button("🎤 Speak Review"):
        with st.spinner("Listening..."):
            spoken = speech_input()
            text = spoken
            st.success("Voice captured successfully")

with b2:
    analyze = st.button("🔍 Analyze Now")

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================================
# ANALYSIS
# ==========================================================

if analyze:

    if text.strip() == "":
        st.warning("Please enter customer feedback first.")
    else:

        with st.spinner("Running Azure AI analysis..."):
            result = analyze_sentiment(text)

        score = overall_score(result)

        st.markdown("## 📊 Insights Dashboard")

        # Metrics
        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Overall", result["sentiment"])
        c2.metric("Positive", f'{result["positive"]}%')
        c3.metric("Neutral", f'{result["neutral"]}%')
        c4.metric("Negative", f'{result["negative"]}%')

        # Charts
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.plotly_chart(gauge_chart(score), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            df = pd.DataFrame({
                "Sentiment":["Positive","Neutral","Negative"],
                "Score":[
                    result["positive"],
                    result["neutral"],
                    result["negative"]
                ]
            })

            fig = px.bar(
                df,
                x="Sentiment",
                y="Score",
                text="Score",
                color="Sentiment",
                height=340
            )

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.02)",
                font_color="white"
            )

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Smart Insights
        st.markdown("## 🧠 AI Action Center")

        i1,i2,i3 = st.columns(3)

        if result["sentiment"] == "POSITIVE":
            mood = "😊 Happy"
            action = "Upsell / Ask Review"
            urgency = "Low"
        elif result["sentiment"] == "NEGATIVE":
            mood = "😠 Unhappy"
            action = "Immediate Support"
            urgency = "High"
        else:
            mood = "😐 Mixed"
            action = "Need Follow-up"
            urgency = "Medium"

        i1.metric("Customer Mood", mood)
        i2.metric("Recommended Action", action)
        i3.metric("Urgency Level", urgency)

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("""
<div class="footerx">
⚡ Powered by Microsoft Azure Cognitive Services • Premium SaaS UI
</div>
""", unsafe_allow_html=True)