import re
import os
import streamlit as st

def convert_timecode(stl_timecode):
    """Convert STL timecode (HH:MM:SS:FF) to SCC format (HH:MM:SS;FF)."""
    parts = stl_timecode.split(':')
    if len(parts) != 4:
        return None  # Invalid format
    hours, minutes, seconds, frames = map(int, parts)
    return f"{hours:02}:{minutes:02}:{seconds:02};{frames:02}"

def adjust_frame_rate(timecode, source_fps=25, target_fps=29.97):
    """Convert timecode frame rates (e.g., 25fps -> 29.97fps)."""
    if not timecode:
        return None
    hours, minutes, seconds, frames = map(int, timecode.split(';'))
    total_frames = ((hours * 3600 + minutes * 60 + seconds) * source_fps) + frames
    adjusted_frames = round(total_frames * (target_fps / source_fps))
    new_hours = adjusted_frames // (3600 * target_fps)
    remaining = adjusted_frames % (3600 * target_fps)
    new_minutes = remaining // (60 * target_fps)
    remaining = remaining % (60 * target_fps)
    new_seconds = remaining // target_fps
    new_frames = remaining % target_fps
    return f"{new_hours:02}:{new_minutes:02}:{new_seconds:02};{new_frames:02}"

  def sanitize_text(text):
    """Remove unwanted characters and control characters from the text."""
    # Remove non-printable characters, including control characters
    text = ''.join(char for char in text if char.isprintable())
    
    # Replace specific unwanted characters with spaces or remove them
    text = text.replace("", " ").replace("ÿ", "").strip()
    
    # Handle common "garbage" characters (these are often control characters)
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)  # Remove non-printable/control characters
    
    return text

def parse_stl(stl_content):
    """Extract timecodes, captions, and metadata from STL file content."""
    captions = []
    lines = stl_content.decode("latin-1", errors="ignore").replace("", " ").split("\n")
    
    # Debugging: Display first few lines of the file
    st.text("Preview of STL file:")
    st.text("\n".join(lines[:10]))
    
    for line in lines:
        match = re.search(r'(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})?\s*(.*)', line.strip())
        if match:
            start, end, text = match.groups()
            if not end:
                end = start  # Handle missing end timecodes
            
            start_scc = adjust_frame_rate(convert_timecode(start))
            end_scc = adjust_frame_rate(convert_timecode(end))
            
            if not start_scc or not end_scc:
                continue  # Skip invalid entries
            
            control_code = "942C"  # Default: Pop-on
            if "{RU2}" in text:
                control_code = "94AD"  # Roll-up 2 lines
                text = text.replace("{RU2}", "")
            elif "{RU3}" in text:
                control_code = "94AE"  # Roll-up 3 lines
                text = text.replace("{RU3}", "")
            elif "{RU4}" in text:
                control_code = "94AF"  # Roll-up 4 lines
                text = text.replace("{RU4}", "")
            elif "{PA}" in text:
                control_code = "9429"  # Paint-on captions
                text = text.replace("{PA}", "")
            
            captions.append({
                "start": start_scc,
                "end": end_scc,
                "text": text.strip(),
                "control_code": control_code
            })
    
    if not captions:
        st.error("No captions found. Please check your STL file format.")
    return captions

def write_scc(captions):
    """Generate SCC formatted text."""
    if not captions:
        return ""  # Return empty if no captions found
    
    scc_content = "Scenarist_SCC V1.0\n\n"
    for caption in captions:
        scc_content += f"{caption['start']} {caption['control_code']} {caption['text']}\n"
    return scc_content

# Streamlit Web App
st.title("STL to SCC Converter")
uploaded_file = st.file_uploader("Upload STL File", type=["stl"])

if uploaded_file is not None:
    captions = parse_stl(uploaded_file.read())
    scc_content = write_scc(captions)
    
    if scc_content:
        st.download_button(
            label="Download SCC File",
            data=scc_content,
            file_name="output.scc",
            mime="text/plain"
        )
