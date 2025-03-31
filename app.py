import streamlit as st
import struct

# Convert STL timecode to SCC timecode format
def convert_timecode(tc_bytes):
    hh, mm, ss, ff = struct.unpack('BBBB', tc_bytes)
    return f"{hh:02}:{mm:02}:{ss:02}:{ff:02}"

# Function to parse STL file
def parse_stl(file_content):
    st.text(f"Raw Data (First 500 bytes): {file_content[:500]}")

    # Ensure it's an EBU 3264 STL file
    header = file_content[:1024]
    if not header.startswith(b'850STL'):
        st.error("Invalid STL header! Not an EBU 3264 STL file.")
        return []

    # Subtitle blocks start after 1024 bytes
    tti_blocks = file_content[1024:]
    block_size = 128
    num_blocks = len(tti_blocks) // block_size

    subtitles = []

    for i in range(num_blocks):
        block = tti_blocks[i * block_size : (i + 1) * block_size]

        # Extract start/end timecodes and text
        start_tc = convert_timecode(block[5:9])
        end_tc = convert_timecode(block[10:14])
        text = block[16:].decode('latin-1').strip()

        st.text(f"Decoded Line {i}: {text}")

        if text:
            subtitles.append({
                "start": start_tc,
                "end": end_tc,
                "text": text
            })

    return subtitles

# Convert parsed STL subtitles to SCC format
def write_scc(subtitles):
    scc_lines = ["Scenarist_SCC V1.0\n"]

    for sub in subtitles:
        start_time = sub['start']
        text = sub['text'].replace("\n", " ")  # SCC does not support line breaks
        scc_lines.append(f"{start_time} 942C {text}")

    return "\n".join(scc_lines)

# Streamlit UI
st.title("STL to SCC Converter")

uploaded_file = st.file_uploader("Upload EBU STL File", type="stl")

if uploaded_file:
    st.success("File uploaded successfully!")
    st.text(f"File Name: {uploaded_file.name}")

    # Read uploaded STL file
    file_content = uploaded_file.read()
    subtitles = parse_stl(file_content)

    if subtitles:
        st.success("Subtitles extracted successfully!")

        # Convert to SCC
        scc_content = write_scc(subtitles)

        # Download SCC
        st.download_button(label="Download SCC File", data=scc_content, file_name="output.scc", mime="text/plain")

    else:
        st.error("No subtitles found in the STL file!")
