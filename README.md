# ViralCut AI — Starter MVP

This starter website accepts a YouTube URL, reads available captions, and asks Gemini to suggest short-form clip timestamps.

## Important limits
- This MVP does NOT download or cut the YouTube video.
- It only works when captions/transcripts are accessible.
- A viral score is an estimate, not a guarantee.
- For actual video exports, use videos you own or have permission to edit, then add an upload/authorized-media workflow.

## Run locally
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`
5. Get a Gemini API key from Google AI Studio and paste it into the app.

## Deploy free
Push these files to a GitHub repository, then deploy that repository on Streamlit Community Cloud.
Do not put your API key in the source code or commit it to GitHub.
