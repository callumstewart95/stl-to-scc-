import re
import streamlit as st

def clean_text(text):
    """Remove unwanted control characters and non-printable bytes, including padding sequences."""
    # Remove non-printable characters and padding sequences like \x8f
    cleaned_text = re.sub(r'[\x00-\x1F\x80-\x9F\x8f\x8a]+', '', text)  # Remove control characters & unwanted bytes
    return cleaned_text.strip()

def parse_stl(stl_content):
    """Extract timecodes, captions, and metadata from STL file content."""
    captions = []

    # Debugging: Display raw bytes of the file content (first 200 bytes)
    st.text(f"Raw Bytes (first 200 bytes): {stl_content[:200]}")  # Display first 200 bytes for analysis

    try:
        # Try decoding with iso-8859-15 encoding, as STL files often use this encoding
        lines = stl_content.decode("iso-8859-15", errors="ignore").split("\n")
    except UnicodeDecodeError:
        # Fallback to iso-8859-1 if iso-8859-15 fails
        lines = stl_content.decode("iso-8859-1", errors="ignore").split("\n")

    # Debugging: Display lines after decoding
    st.text(f"Decoded lines: {lines[:10]}")  # Show the first 10 decoded lines for inspection

    # Regex to extract the timecodes and text
    for line in lines:
        match = re.search(r'(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})?\s*(.*)', line.strip())
        if match:
            start, end, text = match.groups()
            if not end:
                end = start  # Handle missing end timecodes
            
            # Clean the subtitle text to remove unwanted characters
            text = clean_text(text)
            
            if text:  # Only append valid captions
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
                
                # Wrap text to fit within 31 CPL (Characters Per Line)
                text = wrap_text_to_31_cpl(text)
                
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
    stl_content = uploaded_file.read()
    st.text(f"Raw Bytes (first 200 bytes): {stl_content[:200]}")  # Show raw bytes again for debugging
    captions = parse_stl(stl_content)
    
    if captions:  # Check if captions exist before trying to write the SCC file
        scc_content = write_scc(captions)
        st.download_button(
            label="Download SCC File",
            data=scc_content,
            file_name="output.scc",
            mime="text/plain"
        )
    else:
        st.warning("No valid captions found. Please check the STL file format.")
