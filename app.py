import re

def clean_text(text):
    """Remove unwanted control characters from subtitle text."""
    cleaned = re.sub(r'[\x8f\x8aÿ\x00]', '', text)  # Remove known unwanted characters
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
    return cleaned.strip()

def parse_stl(file_path):
    """Extract subtitle text from an STL (EBU 3264) file."""
    with open(file_path, 'rb') as f:
        content = f.read()

    # Locate the subtitle text region (TTI blocks start after 1024 bytes)
    tti_start = 1024  
    subtitle_data = content[tti_start:]

    subtitles = []
    for i in range(0, len(subtitle_data), 128):  # Each TTI block is 128 bytes
        block = subtitle_data[i:i+128]
        if len(block) < 128:
            break  # Ignore incomplete blocks

        raw_text = block[11:].decode('latin-1', errors='ignore')  # Decode using Latin-1
        cleaned_text = clean_text(raw_text)
        if cleaned_text:
            subtitles.append(cleaned_text)

    return subtitles

def write_scc(subtitles, output_file):
    """Convert cleaned subtitles to SCC format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Scenarist_SCC V1.0\n\n")
        for i, subtitle in enumerate(subtitles):
            f.write(f"00:{i//60:02}:{i%60:02}:00 942C {subtitle}\n")  # Fake SCC timecodes

# Usage Example
stl_file = "Red_Dwarf_US_Online.stl"
scc_output = "output.scc"

subtitles = parse_stl(stl_file)
write_scc(subtitles, scc_output)

print("Conversion complete! Check 'output.scc'.")
