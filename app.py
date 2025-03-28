import re
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
    # Define unwanted characters typically found in STL files
    unwanted_chars = [
        'ÿ', '', 'ÿ', 'è', 'é', 'ò', 'ç', '±', '°', '', 'å', '×', '¬', 'œ', '®', '¼', '', '', '▒', '¦', '•'
    ]
    
    # Replace unwanted characters with a space
    for char in unwanted_chars:
        text = text.replace(char, ' ')  # Replace unwanted characters with spaces
    
    # Remove any non-printable ASCII characters (those with byte values 0-31 and 127)
    text = re.sub(r'[^\x20-\x7E]', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim any leading or trailing spaces
    text = text.strip()
    
    return text

def wrap_text_to_31_cpl(text):
    """Wrap text to fit within 31 Characters Per Line (CPL)."""
    lines = []
    while len(text) > 31:
        # Find the last space within the first 31 characters to split on
        split_pos = text.rfind(' ', 0, 31)
        if split_pos == -1:
            split_pos = 31  # If no space, break at 31 characters
        lines.append(text[:split_pos])
        text = text[split_pos:].strip()
    if text:
        lines.append(text)
    
    return '\n'.join(lines)

def parse_stl(stl_content):
    """Extract timecodes, captions, and metadata from STL file content."""
    captions = []

    # Try decoding with iso-8859-15 (Latin-9) encoding for EBU Swift STL files
    try:
        lines = stl_content.decode("iso-8859-15", errors="ignore").split("\n")
    except UnicodeDecodeError:
        # Fallback to iso-8859-1 if iso-8859-15 fails
        lines = stl_content.decode("iso-8859-1", errors="ignore").split("\n")
    
    # Debugging: Show raw content to understand encoding issues
    st.text("Raw decoded content (first 50 lines):")
    st.text("\n".join(lines[:50]))  # Show more lines for deeper inspection

    # Regex to extract the timecodes and text
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
            
            # Sanitize the subtitle text to remove unwanted characters
            text = sanitize_text(text)
            
            # Wrap text to fit within 31 CPL (Characters Per Line)
            text = wrap_text_to_31_cpl(text)
            
            if text:  # Only append valid captions
                captions.append({
                    "start": start_scc,
                    "end": end_scc,
                    "text": text,
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
