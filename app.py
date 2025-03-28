import struct
import re
import streamlit as st

def clean_text(text):
    """Remove unwanted control characters and non-printable bytes, including padding sequences."""
    # Remove unwanted characters like \x8f and other non-printable characters
    cleaned_text = re.sub(r'[\x00-\x1F\x80-\x9F\x8f\x8aÿ_]+', '', text)  # Remove control characters & unwanted bytes
    return cleaned_text.strip()

def parse_ebu3264_stl(stl_content):
    """Extract timecodes, captions, and metadata from an EBU 3264 STL file."""
    captions = []
    lines = []

    # Show the raw bytes of the STL content (first 200 bytes)
    st.text(f"Raw Bytes (first 200 bytes): {stl_content[:200]}")  # Show first 200 bytes for analysis

    # This is a fixed-length header, starting from index 0 in STL files.
    # EBU 3264 uses 32-byte headers and then a series of subtitle records, each one starting with a 4-byte timecode
    header_length = 32  # Length of the EBU 3264 header
    content_start_index = header_length
    
    # Extracting binary information based on structure (adjust based on STL format)
    while content_start_index < len(stl_content):
        # Read 4 bytes of timecode, 2 bytes of length, and the actual text data
        timecode_start = struct.unpack('>I', stl_content[content_start_index:content_start_index+4])[0]
        timecode_end = struct.unpack('>I', stl_content[content_start_index+4:content_start_index+8])[0]
        
        # Next 2 bytes for text length
        text_length = struct.unpack('>H', stl_content[content_start_index+8:content_start_index+10])[0]
        
        # The actual subtitle text is after the timecode and text length, and is text_length bytes long
        subtitle_text = stl_content[content_start_index+10:content_start_index+10+text_length].decode('latin1', errors='ignore')
        
        # Clean the subtitle text to remove unwanted characters
        cleaned_subtitle_text = clean_text(subtitle_text)
        
        if cleaned_subtitle_text:  # Only append if the subtitle text is non-empty
            captions.append({
                'start': timecode_start,
                'end': timecode_end,
                'text': cleaned_subtitle_text
            })
        
        # Move to the next subtitle record
        content_start_index += 10 + text_length

    if not captions:
        st.error("No captions found. Please check your STL file format.")
    
    return captions

def write_scc(captions):
    """Generate SCC formatted text."""
    if not captions:
        return ""  # Return empty if no captions found
    
    scc_content = "Scenarist_SCC V1.0\n\n"
    for caption in captions:
        # Directly use the timecode values for SCC output
        start_scc = timecode_to_scc_format(caption['start'])
        end_scc = timecode_to_scc_format(caption['end'])
        
        scc_content += f"{start_scc} 942C {caption['text']}\n"
    return scc_content

def timecode_to_scc_format(timecode):
    """Convert raw timecode (in frames) to SCC format."""
    # Assuming timecode is in frames, convert to HH:MM:SS:FF (e.g., 00:02:35:20)
    hours = timecode // 3600
    minutes = (timecode % 3600) // 60
    seconds = timecode % 60
    frames = 0  # Set frames to 0 for simplicity, adjust as needed
    
    return f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

# Streamlit Web App
st.title("STL to SCC Converter")
uploaded_file = st.file_uploader("Upload STL File", type=["stl"])

if uploaded_file is not None:
    stl_content = uploaded_file.read()
    st.text(f"Raw Bytes (first 200 bytes): {stl_content[:200]}")  # Show raw bytes for debugging
    captions = parse_ebu3264_stl(stl_content)
    
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
