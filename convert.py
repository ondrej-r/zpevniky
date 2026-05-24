#!/usr/bin/env python3
# pylint: disable=W0621,W0718,W1309,C0114,C0115,C0116,C0301
# pyright: standard

import re
import sys
import os

# Updated to securely catch roots containing raw # and & characters alongside original Czech names
GERMAN_CHORD_REGEX = r'(?:Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G|H|bB])[#&]?(?:maj|min|dim|aug|sus|mi|m)?\d*(?:\/(?:Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G|H|bB])[#&]?(?:maj|min|dim|aug|sus|mi|m)?\d*)?'

def is_chord_line(line):
    """
    Determines if a text line consists purely of musical chords.
    Tracks standard chords, extensions, and regional German/Czech variations.
    """
    if not line.strip():
        return False

    # Strip out chords using the explicit German pattern
    cleaned = re.sub(GERMAN_CHORD_REGEX, '', line)
    cleaned = re.sub(r'[\s,:\-\(\)\/\|\]\[\d\+]', '', cleaned)

    return len(cleaned) == 0

def convert_german_chord(chord_text):
    """
    Translates German/Czech text notation definitions into standard international representations.
    Maps everything directly to one of your environment's 24 supported structural roots.
    """
    if '/' in chord_text:
        parts = chord_text.split('/')
        return "/".join([convert_german_chord(p) for p in parts])

    # Enhanced pattern catches accidentals (#/&) safely alongside raw letters and text tokens
    match = re.match(r'^(Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G][#&]?|H|h|B|b)(.*)$', chord_text.strip())

    if not match:
        return chord_text

    root, extension = match.groups()

    # Strict Canonical Map targeting your 24 explicit root combinations
    german_to_international = {
        # Naturals & German H conversion
        'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'A': 'A', 'H': 'B', 'h': 'B',

        # Sharps (Křížky -is and native # symbols mapped directly to safe output)
        'C#': 'C#', 'D#': 'D#', 'F#': 'F#', 'G#': 'G#', 'A#': 'A#',
        'Cis': 'C#', 'Dis': 'D#', 'Fis': 'F#', 'Gis': 'G#', 'Ais': 'A#',
        'cis': 'C#', 'dis': 'D#', 'fis': 'F#', 'gis': 'G#', 'ais': 'A#',

        # Flats (Béčka -es and native & or b variations mapped cleanly)
        'D&': 'D&', 'E&': 'E&', 'G&': 'G&', 'A&': 'A&', 'B&': 'B&',
        'Des': 'D&', 'Es': 'E&', 'Ges': 'G&', 'As': 'A&', 'Hes': 'B&',
        'ces': 'C',  'des': 'D&', 'es': 'E&', 'ges': 'G&', 'as': 'A&', 'hes': 'B&',

        # The German/Czech B-flat Anomaly
        'B': 'B&', 'b': 'B&'
    }

    if root in german_to_international:
        root = german_to_international[root]

    return f"{root}{extension}"

def parse_filename_metadata(filename):
    """
    Extracts song title and author based on custom naming convention rules:
    - 'Title-Author.txt' -> Title, Author
    - 'Title.txt' -> Title, Empty Author string
    """
    base_name = os.path.basename(filename).replace('.txt', '')

    if '-' in base_name:
        parts = base_name.split('-', 1)
        raw_title = parts[0]
        raw_author = parts[1]
    else:
        raw_title = base_name
        raw_author = ""

    title = raw_title.replace('_', ' ').strip()
    author = raw_author.replace('_', ' ').strip()

    return title, author

def clean_latex_dashes(line):
    """
    Applies official Czech ÚJČ guidelines for dashes mapped directly to LaTeX syntax:
    - Spaces around a dash/hyphen -> Spaced en-dash ' -- ' (Pauses / multi-word bounds).
    - No spaces around dash between digits/words -> Tight en-dash '--' (Ranges/single-word bonds).
    - True word splits (e.g. 'česko-polské') preserve the single tight hyphen '-'.
    """
    line = re.sub(r'[\u2013\u2014\u2212]', '-', line)
    line = re.sub(r'\s+-\s+', ' -- ', line)
    line = re.sub(r'(\w)-(\w)', r'\1--\2', line)

    def restore_compounds(match):
        w1, w2 = match.groups()
        if w1.endswith(('o', 'e', 'i', 'y')) and w1.islower() and w2.islower():
            return f"{w1}-{w2}"
        return f"{w1}--{w2}"

    line = re.compile(r'(\w+)--(\w+)').sub(restore_compounds, line)
    line = re.sub(r'\s+', ' ', line)
    return line # Maintain original layout structure for indexing lookup loops

def process_pure_chord_line(chord_line):
    """Helper to convert a standalone line of chords into standard LaTeX sequences."""
    chord_matches = re.finditer(GERMAN_CHORD_REGEX, chord_line)

    combined_line = list(chord_line)
    for match in reversed(list(chord_matches)):
        raw_chord = match.group()
        start_idx = match.start()
        end_idx = match.end()

        clean_chord = convert_german_chord(raw_chord)
        latex_chord = "\\ch{" + clean_chord + "}{}{}{}"
        combined_line[start_idx:end_idx] = list(latex_chord)

    return "".join(combined_line).strip()

def merge_chords_and_lyrics(chord_line, lyric_line):
    """
    Weaves chords into lyrics cleanly using a Right-to-Left loop.
    This guarantees that modifications downstream never offset early indices.
    """
    chord_matches = list(re.finditer(GERMAN_CHORD_REGEX, chord_line))
    combined_lyric = list(lyric_line)

    # Process RIGHT-TO-LEFT so shifting lengths don't spoil our text boundaries
    for match in reversed(chord_matches):
        raw_chord = match.group()
        start_idx = match.start()

        clean_chord = convert_german_chord(raw_chord)
        latex_chord = "\\ch{" + clean_chord + "}{}{}{}"

        if start_idx < len(combined_lyric):
            combined_lyric.insert(start_idx, latex_chord)
        else:
            # If chord line is longer than lyric text line, pad and append safely
            combined_lyric.extend([' '] * (start_idx - len(combined_lyric)))
            combined_lyric.append(latex_chord)

    return "".join(combined_lyric)

def convert_song_text(text):
    text = text.replace('\xa0', ' ')

    # Step 1: Keep ALL original spaces completely intact so chords match up
    # perfectly with character positions! Only strip trailing newlines.
    raw_lines = [line.rstrip('\r\n') for line in text.splitlines()]

    # Group raw text into layout paragraphs
    blocks = []
    current_block = []
    for line in raw_lines:
        if line.strip():
            current_block.append(line)
        else:
            if current_block:
                blocks.append(current_block)
                current_block = []
    if current_block:
        blocks.append(current_block)

    final_song_output = []

    for block in blocks:
        # Detect if this block is a chorus based on a prefix anywhere inside it
        is_chorus_block = False
        for line in block:
            if re.match(r'^\s*(Ref|Chorus|R):', line, re.IGNORECASE):
                is_chorus_block = True
                break

        processed_block_lines = []
        idx = 0
        while idx < len(block):
            line = block[idx]

            if is_chord_line(line):
                if idx + 1 < len(block) and not is_chord_line(block[idx + 1]):
                    next_line = block[idx + 1]

                    # Step 2: Merge chords directly into the RAW lyric line (Right-to-Left)
                    merged = merge_chords_and_lyrics(line, next_line)

                    # Step 3: Now that chords are locked in place, strip prefixes and clean layout
                    cleaned_line = re.sub(r'^\s*(Ref|Chorus|R):\s*', '', merged, flags=re.IGNORECASE)
                    cleaned_line = re.sub(r'^\s*\d+\.\s*', '', cleaned_line)

                    # Apply official Czech ÚJČ dash guidelines
                    sanitized_line = clean_latex_dashes(cleaned_line)

                    # Strip all leading/trailing whitespace completely before final output
                    processed_block_lines.append(sanitized_line.strip())
                    idx += 2
                else:
                    # Standalone chord line
                    processed_line = clean_latex_dashes(process_pure_chord_line(line))
                    processed_block_lines.append(processed_line.strip())
                    idx += 1
            else:
                # Regular lyric line without any chords on top
                cleaned_line = re.sub(r'^\s*(Ref|Chorus|R):\s*', '', line, flags=re.IGNORECASE)
                cleaned_line = re.sub(r'^\s*\d+\.\s*', '', cleaned_line)
                sanitized_line = clean_latex_dashes(cleaned_line)
                processed_block_lines.append(sanitized_line.strip())
                idx += 1

        env_tag = "chorus" if is_chorus_block else "verse"
        final_song_output.append(f"\\begin{env_tag}{{}}")
        final_song_output.extend(processed_block_lines)
        final_song_output.append(f"\\end{env_tag}{{}}\n")

    return "\n".join(final_song_output).strip()

def generate_latex_song(title, author, content):
    if author:
        meta_string = f"\\beginsong{{{title}}}[by={{{author}}}]"
    else:
        meta_string = f"\\beginsong{{{title}}}"

    return f"""% chktex-file 8
% chktex-file 12
% chktex-file 18
{meta_string}

{content}

\\endsong{{}}
"""

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, "txt")
    dst_dir = os.path.join(script_dir, "src")

    os.makedirs(dst_dir, exist_ok=True)

    if len(sys.argv) >= 2:
        target_filename = sys.argv[1]
        input_path = os.path.join(src_dir, target_filename)
        files_to_process = [input_path] if os.path.exists(input_path) else []
        if not files_to_process:
            print(f"Error: Could not find '{target_filename}' inside folder: {src_dir}")
            sys.exit(1)
    else:
        if not os.path.exists(src_dir):
            print(f"Error: The 'txt' folder does not exist relative to the script layout at: {src_dir}")
            sys.exit(1)
        files_to_process = [os.path.join(src_dir, f) for f in os.listdir(src_dir) if f.endswith(".txt")]

    if not files_to_process:
        print(f"No source files detected inside: {src_dir}")
        sys.exit(0)

    print(f"Processing tracks from {src_dir} into {dst_dir}...\n" + "-"*50)

    for file_path in files_to_process:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            title, author = parse_filename_metadata(file_path)
            converted_content = convert_song_text(raw_text)
            latex_song = generate_latex_song(title, author, converted_content)

            base_name = os.path.basename(file_path).replace('.txt', '')
            output_path = os.path.join(dst_dir, base_name + ".tex")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex_song)

            author_log = author if author else "None"
            print(f"✓ '{title}' [Author: {author_log}] -> src/{base_name}.tex")
        except Exception as e:
            print(f"✗ Failed to convert {os.path.basename(file_path)}: {str(e)}")

    print("-"*50 + f"\nDone! Batch compilation complete.")
