import json
import re
from urllib.parse import urlparse, parse_qs

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.set_page_config(page_title="ViralCut AI", page_icon="✂️", layout="wide")

st.markdown("""
<style>
.main {background: #0b1020;}
.block-container {max-width: 1000px; padding-top: 2rem;}
.hero {padding: 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#172554,#312e81);}
.hero h1 {color:white; margin:0;}
.hero p {color:#c7d2fe; margin:.4rem 0 0;}
</style>
<div class="hero">
<h1>✂️ ViralCut AI</h1>
<p>Turn long YouTube videos into short-form clip ideas.</p>
</div>
""", unsafe_allow_html=True)

st.write("")
api_key = st.text_input("Gemini API key", type="password", help="Get a key from Google AI Studio. Do not share it with anyone.")
url = st.text_input("Paste a YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
clip_count = st.slider("How many clip ideas?", 3, 15, 8)
clip_length = st.selectbox("Preferred clip length", ["30–45 seconds", "45–60 seconds", "60–90 seconds"])

def get_video_id(link):
    parsed = urlparse(link.strip())
    host = parsed.netloc.lower().replace("www.", "")
    if host == "youtu.be":
        return parsed.path.strip("/").split("/")[0]
    if host in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.split("/")
            return parts[2] if len(parts) > 2 else None
    return None

def clean_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("AI did not return valid JSON.")
    return json.loads(match.group(0))

if st.button("Find Viral Moments", type="primary", use_container_width=True):
    if not api_key or not url:
        st.error("Please enter both your Gemini API key and a YouTube URL.")
        st.stop()

    video_id = get_video_id(url)
    if not video_id:
        st.error("That YouTube link does not look valid. Please paste a normal video link.")
        st.stop()

    try:
        with st.spinner("Reading available captions..."):
            transcript = YouTubeTranscriptApi().fetch(video_id)
            rows = [{"start": round(x.start, 2), "duration": round(x.duration, 2), "text": x.text} for x in transcript]
        if not rows:
            st.error("No captions were found for this video.")
            st.stop()

        transcript_text = "\n".join(
            f"[{r['start']:.1f}s] {r['text']}" for r in rows
        )
        if len(transcript_text) > 90000:
            transcript_text = transcript_text[:90000] + "\n[Transcript shortened because it is very long.]"

        client = genai.Client(api_key=api_key)
        prompt = f"""
You are an expert short-form video editor. Analyze this YouTube transcript and identify the strongest self-contained moments for Shorts/Reels.
Return ONLY valid JSON in this exact shape:
{{
 "clips": [
  {{
   "start_seconds": 0,
   "end_seconds": 40,
   "title": "Short catchy title",
   "hook": "Opening hook",
   "reason": "Why this moment may hold attention",
   "score": 85
  }}
 ]
}}
Rules:
- Return at most {clip_count} clips.
- Preferred duration: {clip_length}.
- Use timestamps from the transcript. start_seconds and end_seconds must be numeric.
- Do not invent moments or dialogue.
- Prefer strong hooks, surprising reveals, funny/emotional moments, useful tips, conflict, or clear payoffs.
- Avoid overlapping clips where possible.
- Score is an estimate of short-form potential, not a guarantee of virality.
Transcript:
{transcript_text}
"""
        with st.spinner("AI is finding the strongest moments..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
        result = clean_json(response.text)
        clips = result.get("clips", [])
        if not clips:
            st.warning("The AI did not find any clips. Try another video.")
            st.stop()

        st.success(f"Found {len(clips)} clip ideas.")
        for i, clip in enumerate(clips, 1):
            start = max(0, int(float(clip.get("start_seconds", 0))))
            end = max(start, int(float(clip.get("end_seconds", start))))
            score = int(clip.get("score", 0))
            mins1, secs1 = divmod(start, 60)
            mins2, secs2 = divmod(end, 60)
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.subheader(f"{i}. {clip.get('title', 'Untitled clip')}")
                    st.caption(f"{mins1:02d}:{secs1:02d} – {mins2:02d}:{secs2:02d}")
                with c2:
                    st.metric("Potential score", f"{score}/100")
                st.write("**Hook:**", clip.get("hook", ""))
                st.write("**Why it works:**", clip.get("reason", ""))
                st.code(f"Start: {start}s | End: {end}s", language="text")

        st.info("MVP note: this version finds timestamps from available captions. It does not download or cut the YouTube video. Use videos you own or have permission to edit for the next export stage.")

    except Exception as e:
        msg = str(e)
        if "TranscriptsDisabled" in msg or "NoTranscriptFound" in msg:
            st.error("Captions are disabled or unavailable for this video. Try a video with captions.")
        else:
            st.error(f"Could not process this video: {msg}")
            st.caption("Check the URL, API key, internet connection, and whether captions are available.")
