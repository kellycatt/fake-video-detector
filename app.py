import streamlit as st
import cv2  # OpenCV for video processing
from PIL import Image
from transformers import pipeline

# --- PART 1: THE REAL AI BRAIN ---
# We use a cache so we don't reload the heavy AI model every time you click a button
@st.cache_resource
def load_model():
    # This downloads a model specifically trained to spot AI-generated images
    # Model: "umm-maybe/AI-image-detector" (Good for general AI art/video frames)
    pipe = pipeline("image-classification", model="umm-maybe/AI-image-detector")
    return pipe

def analyze_video(video_path):
    """
    1. Breaks video into frames.
    2. Scans 1 frame every second.
    3. Averages the 'Artificial' score.
    """
    pipe = load_model()
    vidcap = cv2.VideoCapture(video_path)
    
    fps = vidcap.get(cv2.CAP_PROP_FPS) # Frames per second
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    frame_scores = []
    
    # We will scan 1 frame every second to save time
    for i in range(0, int(duration)):
        # Jump to the specific second
        vidcap.set(cv2.CAP_PROP_POS_MSEC, i * 1000) 
        success, image = vidcap.read()
        
        if success:
            # Convert OpenCV Image (BGR) to PIL Image (RGB) for the AI
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            
            # ASK THE AI
            result = pipe(pil_image)
            
            # The result looks like: [{'label': 'artificial', 'score': 0.99}, ...]
            # We find the score for 'artificial'
            ai_score = next((item['score'] for item in result if item['label'] == 'artificial'), 0)
            frame_scores.append(ai_score)

    vidcap.release()
    
    # Calculate average score across all frames
    if not frame_scores:
        return 0.0
    
    final_score = sum(frame_scores) / len(frame_scores)
    return final_score

# --- PART 2: THE WEBSITE INTERFACE ---

st.set_page_config(page_title="Real AI Video Detector", page_icon="🤖")

st.title("🤖 Real AI Video Detector")
st.write("This tool breaks video into frames and scans them for AI generation artifacts.")

uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("Analyze Video (Real Scan)"):
        # Save the uploaded file temporarily so OpenCV can read it
        with open("temp_video.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        status_bar = st.progress(0)
        status_text = st.empty()
        status_text.write("📱 Loading AI Model... (This takes a moment)")
        
        # RUN THE SCAN
        try:
            score = analyze_video("temp_video.mp4")
            status_bar.progress(100)
            
            # DISPLAY RESULTS
            st.divider()
            percentage = score * 100
            
            if score > 0.60:
                st.error(f"🚨 **AI DETECTED**")
                st.metric("AI Confidence Score", f"{percentage:.1f}%")
                st.write("The visual textures in this video strongly match AI generation patterns.")
            elif score < 0.40:
                st.success(f"✅ **LIKELY REAL**")
                st.metric("AI Confidence Score", f"{percentage:.1f}%")
                st.write("The video contains natural noise and patterns typical of real cameras.")
            else:
                st.warning(f"⚠️ **UNCERTAIN**")
                st.metric("AI Confidence Score", f"{percentage:.1f}%")
                st.write("The video has mixed signals. It might be heavily edited or a high-quality deepfake.")
                
        except Exception as e:
            st.error(f"Error analyzing video: {e}")
