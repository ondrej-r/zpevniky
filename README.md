# Custom Songbook Generator

An automated toolchain designed to convert raw text song sheets with musical chords into professionally typeset, print-ready PDF songbooks. The system cleanly supports generating individual booklets in multiple page layouts (A4 and A5 sizes).

---

## Environment & Dependencies

This toolchain was developed and tested using the TeX Live `pdflatex` implementation from the Debian repositories. Other LaTeX compilers (like XeLaTeX or LuaLaTeX) have not been tested.

The project relies on the following LaTeX packages:
`geometry` `hyperref` `fontenc` `inputenc` `xpatch` `songs`

Make sure these are present and installed in your local LaTeX environment before compiling.
* On Linux (Debian/Ubuntu), these are typically provided by installing `texlive-latex-recommended`, `texlive-latex-extra`, and `texlive-music`.
* On Windows, you can download and install the complete distribution here: [TeX Live](https://www.tug.org/texlive/)

---

## Usage

### 1. Adding or Modifying Songs
Navigate into the collection you wish to update and place your raw `.txt` files inside its `txt` folder:
`songs/<songbook_name>/txt/`

When creating or modifying songs, you must adhere to the following rules:

#### File Naming Convention
* **Standard:** `song_name-song_interpret.txt` (e.g., `Colorado-Kabát.txt`)
* **Unknown Author:** `song_name.txt` (e.g., `Brněnská_přehrada.txt`)

> *Use underscores (`_`) in place of regular spaces within the filename.*

> *Use dashes/minus signs (`-`) to separate song title and author*

> *if you need a literal hyphen/dash inside a song title or an author name, use the following escape sequence: `_-_`*

#### Content Formatting
The text files should contain **only the chords and lyrics**. Do not duplicate the song title or author inside the text file; the system dynamically extracts this metadata directly from the filename.

```text
D      Emi  G       A
mám tě rád, buď můj salám lásko...
```

### 2. Compile the System

#### Linux / macOS
Open your terminal at the project home directory and run the compilation pipeline (make sure you have `GNU Make` installed):

```bash
make clean && make 2>&1 | tee build.log
```

#### Windows (cmd.exe)
If you have `make` installed on Windows (e.g., via MinGW, Chocolatey, or GnuWin32), run the following in Command Prompt:

```cmd
make clean && make > build.log 2>&1
```

#### Windows (PowerShell / pwsh.exe)
Run the following pipeline in PowerShell:

```powershell
make clean; make 2>&1 | Tee-Object -FilePath "build.log"
```

---

### 3. Retrieve Final Songbooks
Once the compilation sequence succeeds, the automation  moves your finalized PDFs from build folder into the distribution folder.

Your print-ready files will be cleanly organized inside the `dist` directory:
```text
dist/
├── nas_zpevnik_A4.pdf
├── nas_zpevnik_A5.pdf
├── oddilovy_zpevnik_I_A4.pdf
├── oddilovy_zpevnik_I_A5.pdf
├── oddilovy_zpevnik_II_A4.pdf
└── oddilovy_zpevnik_II_A5.pdf
```

---

## Architecture Overview

The system isolates raw input assets, generated build steps, and finalized documents into a structured layout:

* `songbooks/`: Holds the static LaTeX master configuration files defining layout boundaries, geometry styles, font definitions, and book scaling properties.
* `songs/`: Contains subdirectories for individual song collections (e.g., `nas_zpevnik`, `oddilovy_zpevnik_i`, `oddilovy_zpevnik_ii`).
  * `txt/`: Raw user-facing song sheets.
  * `src/`: LaTeX song fragments generated automatically by the parser logic.
* `build/`: Temporary scratch area where raw logs, compiler flags, and dynamic tracklists live during execution.
* `dist/`: The final distribution warehouse. Only successfully built, production-ready PDFs are delivered here.
