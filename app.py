import re
import streamlit as st

def clean_text(text):
    """Clean the subtitle text by removing unwanted characters."""
    # Replace non-printable characters (such as 8F) with spaces
    text = re.sub(r'[\x8F\x00-\x1F\x7F]', ' ', text)  # Remove control characters, 8F byte
    return text.strip()

def parse_stl(stl_content):
    """Extract timecodes, captions, and metadata from STL file content."""
    captions = []
    
    # Debugging: Display raw bytes of the file content
    st.text("Raw Bytes (first 200 bytes):")
    st.text(view_raw_bytes(stl_content))  # Show raw bytes for analysis
    
    # Try decoding with iso-8859-15 (Latin-9) encoding for EBU Swift STL files
    try:
        lines = stl_content.decode("iso-8859-15", errors="ignore").split("\n")
    except UnicodeDecodeError:
        # Fallback to iso-8859-1 if iso-8859-15 fails
        lines = stl_content.decode("iso-8859-1", errors="ignore").split("\n")
    
    # Regex to extract the timecodes and text
    for line in lines:
        match = re.search(r'(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})?\s*(.*)', line.strip())
        if match:
            start, end, text = match.groups()
            if not end:
                end = start  # Handle missing end timecodes
            
            # Convert timecodes and apply frame rate adjustment (as before)
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
            
            # Clean the subtitle text to remove unwanted characters
            text = clean_text(text)
            
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

# Streamlit Web App
st.title("STL to SCC Converter")
uploaded_file = st.file_uploader("Upload STL File", type=["stl"])

if uploaded_file is not None:
    stl_content = uploaded_file.read()
    captions = parse_stl(stl_content)
    scc_content = write_scc(captions)
    
    if scc_content:
        st.download_button(
            label="Download SCC File",
            data=scc_content,
            file_name="output.scc",
            mime="text/plain"
        )
