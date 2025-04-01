import streamlit as st
import struct
import re

def convert_timecode(tc_bytes):
    hh, mm, ss, ff = struct.unpack('BBBB', tc_bytes)
    frame_rate = 25  # Assuming PAL format
    return f"{hh:02}:{mm:02}:{ss:02};{ff:02}"

def clean_text(text):
    text = text.replace('\x8f', '').replace('\x8a', ' ')  # Remove unwanted characters
    text = re.sub(r'[^\x20-\x7E]', '', text)  # Keep only printable ASCII characters
    return text.strip()

def parse_stl(file_content):
    header = file_content[:1024]
    if not (header.startswith(b'850STL') or header.startswith(b'437STL')):
        st.error("Invalid STL header! Not an EBU 3264 STL file.")
        return []
    
    tti_blocks = file_content[1024:]
    block_size = 128
    num_blocks = len(tti_blocks) // block_size
    subtitles = []
    
    for i in range(num_blocks):
        block = tti_blocks[i * block_size : (i + 1) * block_size]
        if len(block) < block_size:
            continue
        
        start_tc = convert_timecode(block[5:9])
        text = clean_text(block[16:].decode('latin-1'))
        
        if text:
            subtitles.append({"start": start_tc, "text": text})
    
    return subtitles

def text_to_scc_hex(text):
    hex_map = {
        "A": "c141", "B": "c142", "C": "c143", "D": "c144", "E": "c145", "F": "c146", "G": "c147", "H": "c148", "I": "c149", "J": "c14a", "K": "c14b", "L": "c14c", "M": "c14d", "N": "c14e", "O": "c14f", "P": "c150", "Q": "c151", "R": "c152", "S": "c153", "T": "c154", "U": "c155", "V": "c156", "W": "c157", "X": "c158", "Y": "c159", "Z": "c15a", " ": "20"
    }
    return " ".join([hex_map.get(char.upper(), "20") for char in text])

def write_scc(subtitles):
    scc_lines = ["Scenarist_SCC V1.0\n"]
    for sub in subtitles:
        start_time = sub['start']
        scc_text = text_to_scc_hex(sub['text'])
        scc_lines.append(f"{start_time}\t9420 9420 94F4 94F4 {scc_text} 942C 942C 942F 942F\n")
    return "\n".join(scc_lines)

st.title("STL to SCC Converter")

uploaded_file = st.file_uploader("Upload EBU STL File", type="stl")

if uploaded_file:
    st.download_button(label="Download SCC File", data="", file_name="output.scc", mime="text/plain", key="download_scc")
    st.success("File uploaded successfully!")
    st.text(f"File Name: {uploaded_file.name}")
    file_content = uploaded_file.read()
    subtitles = parse_stl(file_content)
    
    if subtitles:
        st.success("Subtitles extracted successfully!")
        scc_content = write_scc(subtitles)
        st.download_button(label="Download SCC File", data=scc_content, file_name="output.scc", mime="text/plain", key="download_scc_content")
    else:
        st.error("No subtitles found in the STL file!")
