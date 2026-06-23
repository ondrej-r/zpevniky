#!/usr/bin/env python3
# pylint: disable=W0621,W0718,W1309,C0114,C0115,C0116,C0301
# pyright: standard

import locale
import re
import sys
import os

# Updated to securely catch roots containing raw # and & characters alongside original Czech names
GERMAN_CHORD_REGEX = r'(?:Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G|H|bB])[#&]?(?:maj|min|dim|aug|sus|mi|m|add|4sus|\+)?\d*(?:\/(?:Cis|Dis|Eis|Fis|Gis|Ais|His|cis|dis|eis|fis|gis|ais|his|Ces|Des|Es|Fes|Ges|As|Hes|ces|des|es|fes|ges|as|hes|[A-G|H|bB])[#&]?(?:maj|min|dim|aug|sus|mi|m|add|4sus|\+)?\d*)?'

# Try native Czech locales, falling back to system defaults if missing
locale_options = ['cs_CZ.UTF-8', 'cs_CZ', 'C.UTF-8']
locale_configured = False

for loc in locale_options:
    try:
        locale.setlocale(locale.LC_COLLATE, loc)
        locale_name = loc
        locale_configured = True
        break
    except locale.Error:
        continue

if not locale_configured:
    print("Warning: Could not set Czech collation locale. Falling back to default system collation.")
    locale.setlocale(locale.LC_COLLATE, '')

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

def convert_song_text(text, singers_edition=False):
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

    # Decoupled independent tracking indices
    verse_count = 0
    chorus_count = 0

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

        # Parse environment block configuration dynamically
        if is_chorus_block:
            start_tag = "\\beginchorus{}"
            end_tag = "\\endchorus{}"
        else:
            start_tag = "\\beginverse*{}" if is_starred else "\\beginverse{}"
            end_tag = "\\endverse{}"

        block_content = "\n".join(final_lines)

        # Inject structural block layout overrides
        if singers_edition and not is_starred:
            if is_chorus_block:
                chorus_count += 1
                if chorus_count > 1:
                    block_content = f"\\chordsoff{{}}\n{block_content}\n\\chordson{{}}"
            else:
                verse_count += 1
                if verse_count > 1:
                    block_content = f"\\chordsoff{{}}\n{block_content}\n\\chordson{{}}"

        final_song_output.append(f"{start_tag}\n{block_content}\n{end_tag}\n")

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
% \\capo{{0}}
\\transpose{{0}}

{content}

\\endsong{{}}
"""

if __name__ == "__main__":
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    songbook_id = os.path.basename(script_dir)

    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    src_dir = os.path.join(script_dir, "txt")
    dst_dir = os.path.join(script_dir, "src")
    build_dir = os.path.join(project_root, "songslists")

    os.makedirs(dst_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    args = sys.argv[1:]
    singer_flag = False
    musician_flag = False
    target_file = None

    while args:
        arg = args.pop(0)
        match arg:
            case "-s" | "--singer":
                singer_flag = True
            case "-m" | "--musician":
                musician_flag = True
            case _:
                # Anything that doesn't match a flag is treated as the target file
                target_file = arg

    # Enforce mutual exclusivity
    if singer_flag and musician_flag:
        print("ERROR: Flags '-s/--singer' and '-m/--musician' are mutually exclusive. Choose only one profile.")
        sys.exit(1)

    # Resolve layout states based on valid flag states
    SINGER_ONLY = singer_flag
    MUSICIAN_ONLY = musician_flag

    # Determine files to process based on parsed arguments
    if target_file:
        files_to_process = [os.path.join(src_dir, target_file)]
    else:
        if not os.path.exists(src_dir):
            print(f"ERROR: Source directory missing: {src_dir}")
            sys.exit(1)
        sorted_files = sorted(
            [f for f in os.listdir(src_dir) if f.endswith(".txt")],
            key=locale.strxfrm
        )
        files_to_process = [os.path.join(src_dir, f) for f in sorted_files]

    print(f"Processing tracks from {src_dir} into {dst_dir}...")
    if SINGER_ONLY:
        print("Profile active: Singers Edition Layout only.")
    elif MUSICIAN_ONLY:
        print("Profile active: Musicians Edition Layout only.")

    musician_manifest_entries = []
    singer_manifest_entries = []

    for file_path in files_to_process:
        if not os.path.exists(file_path):
            print(f"Warning: File not found {file_path}")
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            title, author = parse_filename_metadata(file_path)
            clean_base = os.path.basename(file_path).replace('.txt', '').replace(' ', '')

            # --- 1. Process Musician Layout (*+musician.tex) ---
            if not SINGER_ONLY:
                musician_content = convert_song_text(raw_text, singers_edition=False)
                musician_latex = generate_latex_song(title, author, musician_content)
                musician_tex_filename = f"{clean_base}+musician.tex"

                with open(os.path.join(dst_dir, musician_tex_filename), 'w', encoding='utf-8') as f:
                    f.write(musician_latex)

                musician_rel_path = f"songs/{songbook_id}/src/{musician_tex_filename}"
                musician_manifest_entries.append(f"\\input{{{musician_rel_path}}}\\sclearpage{{}}")

            # --- 2. Process Singer Layout (*+singer.tex) ---
            if not MUSICIAN_ONLY:
                singer_content = convert_song_text(raw_text, singers_edition=True)
                singer_latex = generate_latex_song(title, author, singer_content)
                singer_tex_filename = f"{clean_base}+singer.tex"

                with open(os.path.join(dst_dir, singer_tex_filename), 'w', encoding='utf-8') as f:
                    f.write(singer_latex)

                singer_rel_path = f"songs/{songbook_id}/src/{singer_tex_filename}"
                singer_manifest_entries.append(f"\\input{{{singer_rel_path}}}\\sclearpage{{}}")

        except Exception as e:
            print(f"Failed to convert {os.path.basename(file_path)}: {str(e)}")

    # Distinct mappings for separate musician and singer lists
    manifest_file_map = {
        "nas_zpevnik": ("nas_zpevnik_musician_songs_list.tex", "nas_zpevnik_singer_songs_list.tex"),
        "oddilovy_zpevnik_i": ("oddilovy_zpevnik_I_musician_songs_list.tex", "oddilovy_zpevnik_I_singer_songs_list.tex"),
        "oddilovy_zpevnik_ii": ("oddilovy_zpevnik_II_musician_songs_list.tex", "oddilovy_zpevnik_II_singer_songs_list.tex")
    }

    m_name, s_name = manifest_file_map.get(
        songbook_id,
        (f"{songbook_id}_musician_songs_list.tex", f"{songbook_id}_singer_songs_list.tex")
    )

    if not SINGER_ONLY:
        m_path = os.path.join(build_dir, m_name)
        print(f"Writing Musicians tracklist blueprint: {m_path}")
        with open(m_path, 'w', encoding='utf-8') as f:
            f.write("% Generated automatically by convert.py (Musicians Layout Profile)\n")
            f.write("\n".join(musician_manifest_entries) + "\n")

    if not MUSICIAN_ONLY:
        s_path = os.path.join(build_dir, s_name)
        print(f"Writing Singers tracklist blueprint: {s_path}")
        with open(s_path, 'w', encoding='utf-8') as f:
            f.write("% Generated automatically by convert.py (Singers Layout Profile)\n")
            f.write("\n".join(singer_manifest_entries) + "\n")

    print(f"Done! Clean tracklist architecture written.")
