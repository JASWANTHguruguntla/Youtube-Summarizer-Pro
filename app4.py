import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Constants ---
DEFAULT_PROMPT = """
You are a YouTube video summarizer. Given a transcript, generate a structured summary with:
- Key points (bullet points)
- Important examples (if any)
- Actionable insights (if applicable)
Keep the summary under 250 words. Transcript:
"""

# --- Helper Functions ---
def extract_video_id(url: str) -> str:
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "embed/" in url:
        return url.split("embed/")[1].split("?")[0]
    return None

@st.cache_data(show_spinner=False)
def extract_transcript_details(youtube_video_url: str) -> str:
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            st.error("❌ Invalid YouTube URL. Please check the link format.")
            return None

        # Setup Webshare Proxy
        proxy_config = WebshareProxyConfig(
            proxy_username="jaswanthg",  # Replace with your actual Webshare username
            proxy_password="jashu7896"   # Replace with your actual Webshare password
        )

        ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)

        transcript = ytt_api.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])

    except (TranscriptsDisabled, NoTranscriptFound):
        st.error("🔇 No transcript available for this video.")
        return None
    except Exception as e:
        st.error(f"⚠️ Error fetching transcript: {str(e)}")
        return None

@st.cache_data(show_spinner=False)
def generate_gemini_content(transcript_text: str, prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"⚠️ Gemini API error: {str(e)}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="YouTube Summarizer Pro", page_icon="📝")

with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("🔑 Google API Key", 
                          value=os.getenv("GOOGLE_API_KEY", ""),
                          type="password",
                          help="Overrides .env if provided")
    
    if api_key:
        genai.configure(api_key=api_key)
    
    summary_length = st.selectbox(
        "📏 Summary Length",
        ["Short (100 words)", "Medium (250 words)", "Detailed (500 words)"],
        index=1
    )
    
    st.markdown("---")
    st.markdown("🛠️ Made with [Gemini](https://ai.google.dev/) & [Streamlit](https://streamlit.io/)")

st.title("🎬 YouTube Video Summarizer Pro")
st.caption("Transform long videos into concise notes with AI")

youtube_link = st.text_input(
    "🔗 Paste YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Supports regular links and youtu.be shortcuts"
)

prompt = DEFAULT_PROMPT
if summary_length == "Short (100 words)":
    prompt = prompt.replace("250 words", "100 words")
elif summary_length == "Detailed (500 words)":
    prompt = prompt.replace("250 words", "500 words")

if youtube_link:
    video_id = extract_video_id(youtube_link)
    if video_id:
        try:
            st.image(
                f"http://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                use_container_width=True,
                caption="Video Thumbnail"
            )
        except:
            st.image(
                f"http://img.youtube.com/vi/{video_id}/0.jpg",
                use_column_width=True,
                caption="Video Thumbnail (Fallback)"
            )

if st.button("✨ Generate Summary", type="primary"):
    if not youtube_link:
        st.warning("Please enter a YouTube URL")
    else:
        with st.status("🔍 Processing video...", expanded=True) as status:
            st.write("📜 Fetching transcript...")
            transcript_text = extract_transcript_details(youtube_link)

            if transcript_text:
                st.write("🧠 Generating AI summary...")
                summary = generate_gemini_content(transcript_text, prompt)

                status.update(label="✅ Processing complete!", state="complete")

                if summary:
                    st.subheader("📋 Summary")
                    st.markdown(summary)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download Summary",
                            data=summary,
                            file_name="youtube_summary.txt",
                            mime="text/plain"
                        )
                    with col2:
                        if st.button("🔄 Generate Again"):
                            st.cache_data.clear()
                            st.rerun()

st.markdown("---")
st.caption("💡 Tip: For long videos (>30 mins), the transcript might be truncated due to API limits.")
