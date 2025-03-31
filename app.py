import streamlit as st
import struct

def convert_timecode(tc_bytes):
    hh, mm, ss, ff = struct.unpack('BBBB', tc_bytes)
    return f"{hh:02}:{mm:02}:{ss:02};{ff:02}"

def parse_stl(file_content):
    st.text(f"Raw Data (First 500 bytes): {file_content[:500]}")
    
    header = file_content[:1024]
    if not header.startswith(b'850STL'):
        st.error("Invalid STL header! Not an EBU 3264 STL file.")
        return []
    
    tti_blocks = file_content[1024:]
    block_size = 128
    num_blocks = len(tti_blocks) // block_size
    subtitles = []
    
    for i in range(num_blocks):
        block = tti_blocks[i * block_size : (i + 1) * block_size]
        start_tc = convert_timecode(block[5:9])
        end_tc = convert_timecode(block[10:14])
        text = block[16:].decode('latin-1').strip()
        
        st.text(f"Decoded Line {i}: {text}")
        
        if text:
            subtitles.append({"start": start_tc, "end": end_tc, "text": text})
    
    return subtitles

def text_to_scc_hex(text):
    hex_map = {
        "A": "1421", "B": "1422", "C": "1423", "D": "1424", "E": "1425", "F": "1426", "G": "1427", "H": "1428", "I": "1429", "J": "142A", "K": "142B", "L": "142C", "M": "142D", "N": "142E", "O": "142F", "P": "1430", "Q": "1431", "R": "1432", "S": "1433", "T": "1434", "U": "1435", "V": "1436", "W": "1437", "X": "1438", "Y": "1439", "Z": "143A", " ": "20"
    }
    return " ".join([hex_map.get(char.upper(), "20") for char in text])

def write_scc(subtitles):
    scc_lines = ["Scenarist_SCC V1.0\n"]
    for sub in subtitles:
        start_time = sub['start']
        scc_text = text_to_scc_hex(sub['text'])
        scc_lines.append(f"{start_time}\t9420 94F4 {scc_text} 942F\n")
    return "\n".join(scc_lines)

st.title("STL to SCC Converter")
uploaded_file = st.file_uploader("Upload EBU STL File", type="stl")

if uploaded_file:
    st.success("File uploaded successfully!")
    st.text(f"File Name: {uploaded_file.name}")
    file_content = uploaded_file.read()
    subtitles = parse_stl(file_content)
    
    if subtitles:
        st.success("Subtitles extracted successfully!")
        scc_content = write_scc(subtitles)
        st.download_button(label="Download SCC File", data=scc_content, file_name="output.scc", mime="text/plain")
    else:
        st.error("No subtitles found in the STL file!")
