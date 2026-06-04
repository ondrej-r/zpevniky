#!/usr/bin/env python3
# pylint: disable=W0621,W0718,W1309,C0114,C0115,C0116,C0301
# pyright: standard

import locale
import re
import sys
import os

# Updated to securely catch roots containing raw # and & characters alongside original Czech names
GERMAN_CHORD_REGEX = r'(?:Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G|H|bB])[#&]?(?:maj|min|dim|aug|sus|mi|m|add|4sus|\+)?\d*(?:\/(?:Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G|H|bB])[#&]?(?:maj|min|dim|aug|sus|mi|m|add|4sus|\+)?\d*)?'

LOCALE_NAME = 'C.UTF-8'

try:
    locale.setlocale(locale.LC_COLLATE, LOCALE_NAME)
except locale.Error as exc:
    print(f"Locale {LOCALE_NAME!r} not found: {exc}")
    raise

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
    Translates German/Czech notation into standard international representations.
    Replaces accidentals with LaTeX-safe musical commands {\\shrp} and {\\flt}.
    """
    if '/' in chord_text:
        parts = chord_text.split('/')
        return "/".join([convert_german_chord(p) for p in parts])

    # Enhanced pattern catches accidentals (#/&) safely alongside raw letters and text tokens
    match = re.match(r'^(Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G][#&]?|H|h|B|b)(.*)$', chord_text.strip())

    if not match:
        return chord_text

    root, extension = match.groups()

    # Canonical Map using {\shrp} and {\flt} instead of raw or escaped characters
    german_to_international = {
        # The German/Czech B-flat Anomaly
        'B': 'B{\\flt}', 'b': 'B{\\flt}',

        # Naturals & German H conversion
        'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'A': 'A', 'H': 'B', 'h': 'B',

        # Sharps (Křížky -is and native # symbols)
        'C#': 'C{\\shrp}', 'D#': 'D{\\shrp}', 'F#': 'F{\\shrp}', 'G#': 'G{\\shrp}', 'A#': 'A{\\shrp}',
        'Cis': 'C{\\shrp}', 'Dis': 'D{\\shrp}', 'Fis': 'F{\\shrp}', 'Gis': 'G{\\shrp}', 'Ais': 'A{\\shrp}',
        'cis': 'C{\\shrp}', 'dis': 'D{\\shrp}', 'fis': 'F{\\shrp}', 'gis': 'G{\\shrp}', 'ais': 'A{\\shrp}',

        # Flats (Béčka -es and native & symbols)
        'D&': 'D{\\flt}', 'E&': 'E{\\flt}', 'G&': 'G{\\flt}', 'A&': 'A{\\flt}', 'B&': 'B{\\flt}',
        'Des': 'D{\\flt}', 'Es': 'E{\\flt}', 'Ges': 'G{\\flt}', 'As': 'A{\\flt}', 'Hes': 'B{\\flt}',
        'ces': 'C',  'des': 'D{\\flt}', 'es': 'E{\\flt}', 'ges': 'G{\\flt}', 'as': 'A{\\flt}', 'hes': 'B{\\flt}',
    }

    if root in german_to_international:
        root = german_to_international[root]

    if '+' in extension:
        extension = extension.replace('+', 'aug')

    return f"{root}{extension}"

def parse_filename_metadata(filename):
    """
    Extracts song title and author based on custom naming convention rules.
    Now includes LaTeX escaping for special characters.
    """
    # Remove extension and whitespace
    base_name = os.path.basename(filename).replace('.txt', '').replace(' ', '')

    placeholder = "___LITERAL_DASH___"
    protected_name = base_name.replace('_-_', placeholder)

    if '-' in protected_name:
        parts = protected_name.split('-', 1)
        raw_title = parts[0]
        raw_author = parts[1]
    else:
        raw_title = protected_name
        raw_author = ""

    def finalize_string(s):
        s = s.replace(placeholder, ' - ')
        s = s.replace('_', ' ')
        s = s.replace('#', '\\#')
        s = s.replace('&', '\\&')
        return s.strip()

    title = finalize_string(raw_title)
    author = finalize_string(raw_author)

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
    return line

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
    text = text.replace('„', '"').replace('“', '"')

    raw_lines = [line.rstrip('\r\n') for line in text.splitlines()]
    blocks, current_block = [], []
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
        is_chorus_block = False
        is_starred = False

        for line in block:
            if re.match(r'^\s*(Ref|Chorus|R):', line, re.IGNORECASE):
                is_chorus_block = True
            if re.match(r'^\s*\*:', line):
                is_starred = True

        processed_block_lines = []
        idx = 0
        while idx < len(block):
            line = block[idx]
            if is_chord_line(line):
                if idx + 1 < len(block) and not is_chord_line(block[idx + 1]):
                    merged = merge_chords_and_lyrics(line, block[idx + 1])
                    cleaned_line = re.sub(r'^\s*(Ref|Chorus|R|\*):\s*', '', merged, flags=re.IGNORECASE)
                    cleaned_line = re.sub(r'^\s*\d+\.\s*', '', cleaned_line)
                    processed_block_lines.append(clean_latex_dashes(cleaned_line).strip())
                    idx += 2
                else:
                    processed_block_lines.append(clean_latex_dashes(process_pure_chord_line(line)).strip())
                    idx += 1
            else:
                cleaned_line = re.sub(r'^\s*(Ref|Chorus|R|\*):\s*', '', line, flags=re.IGNORECASE)
                cleaned_line = re.sub(r'^\s*\d+\.\s*', '', cleaned_line)
                processed_block_lines.append(clean_latex_dashes(cleaned_line).strip())
                idx += 1

        final_lines = []
        for l in processed_block_lines:
            l = l.replace('/: ', '\\lrep{} ').replace('/:', '\\lrep{}')
            l = l.replace(' :/', ' \\rrep{}').replace(':/', ' \\rrep{}')
            l = l.replace('...', '\\ldots{}')
            final_lines.append(l)

        if not final_lines or all(not line.strip() for line in final_lines):
            final_lines = ["\\phantom{}"]

        base_name = "chorus" if is_chorus_block else "verse"
        start_tag = f"\\begin{base_name}*{{}}" if is_starred else f"\\begin{base_name}{{}}"
        end_tag = f"\\end{base_name}{{}}"

        final_song_output.append(f"{start_tag}\n" + "\n".join(final_lines) + f"\n{end_tag}\n")

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

    input_filenames = []
    output_filenames = []

    if len(sys.argv) >= 2:
        files_to_process = [os.path.join(src_dir, sys.argv[1])]
    else:
        sorted_files = sorted(
            [f for f in os.listdir(src_dir) if f.endswith(".txt")],
            key=locale.strxfrm
        )
        files_to_process = [os.path.join(src_dir, f) for f in sorted_files if f.endswith(".txt")]

    input_filenames = [os.path.basename(f) for f in files_to_process if os.path.exists(f)]

    print(f"Processing tracks from {src_dir} into {dst_dir}...\n" + "-"*50)

    for file_path in files_to_process:
        if not os.path.exists(file_path):
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            title, author = parse_filename_metadata(file_path)
            content = convert_song_text(raw_text)
            latex_song = generate_latex_song(title, author, content)

            clean_base = os.path.basename(file_path).replace('.txt', '').replace(' ', '')
            tex_filename = f"{clean_base}.tex"

            with open(os.path.join(dst_dir, tex_filename), 'w', encoding='utf-8') as f:
                f.write(latex_song)

            output_filenames.append(tex_filename)
            author_log = author if author else "None"
        except Exception as e:
            print(f"Failed to convert {os.path.basename(file_path)}: {str(e)}")

    print("-" * 50 + f"\nDone! Batch compilation complete.")

    if output_filenames:
        print("-" * 50)
        print("\n".join(output_filenames))
