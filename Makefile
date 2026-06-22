SHELL := /bin/bash
export LANG := C.UTF-8
export LC_ALL := C.UTF-8

PYTHON := python3
OUTDIR := build
DISTDIR := dist

# List of all songbooks to process
SONGBOOKS := nas_zpevnik oddilovy_zpevnik_I oddilovy_zpevnik_II

# Reconstruct targets to look exactly like your preferred output names: build/SONGBOOK_FORMAT+VARIANT.pdf
PDFS := $(foreach sb,$(SONGBOOKS),\
          $(foreach fmt,A4 A5,\
            $(foreach var,singer musician,$(OUTDIR)/$(sb)_$(fmt)+$(var).pdf)))

# Extract only the file names for delivery verification
FINAL_PDF_NAMES := $(notdir $(PDFS))

.PHONY: all clean prepare compile deliver

all: prepare
	@$(MAKE) compile
	@$(MAKE) deliver

prepare:
	@mkdir -p $(OUTDIR)
	@echo "=== Running convert.py scripts ==="
	@# 1. Process Musician Editions explicitly
	$(PYTHON) songs/nas_zpevnik/convert.py -m
	$(PYTHON) songs/oddilovy_zpevnik_I/convert.py -m
	$(PYTHON) songs/oddilovy_zpevnik_II/convert.py -m
	@# 2. Process Singer Editions explicitly
	$(PYTHON) songs/nas_zpevnik/convert.py -s
	$(PYTHON) songs/oddilovy_zpevnik_I/convert.py -s
	$(PYTHON) songs/oddilovy_zpevnik_II/convert.py -s

compile: $(PDFS)
	@echo "=== PDF Compilation Phase Complete ==="

# Pattern rules matched precisely to their decoupled variant manifests
$(OUTDIR)/%_A4+singer.pdf: songbooks/%_A4+singer.tex $(OUTDIR)/%_singer_songs_list.tex
	@echo "=== Compiling $< (Singer A4) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/%_A5+singer.pdf: songbooks/%_A5+singer.tex $(OUTDIR)/%_singer_songs_list.tex
	@echo "=== Compiling $< (Singer A5) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/%_A4+musician.pdf: songbooks/%_A4+musician.tex $(OUTDIR)/%_musician_songs_list.tex
	@echo "=== Compiling $< (Musician A4) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/%_A5+musician.pdf: songbooks/%_A5+musician.tex $(OUTDIR)/%_musician_songs_list.tex
	@echo "=== Compiling $< (Musician A5) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

deliver:
	@echo "=== Verifying Final PDF Artifacts ==="
	@ALL_PRESENT=true; \
	for pdf in $(FINAL_PDF_NAMES); do \
		if [ ! -f "$(OUTDIR)/$$pdf" ]; then \
			echo "ERROR: Missing compiled asset -> $(OUTDIR)/$$pdf"; \
			ALL_PRESENT=false; \
		fi; \
	done; \
	if [ "$$ALL_PRESENT" = true ]; then \
		echo "Verification successful! Purging old distribution and moving assets..."; \
		rm -rf $(DISTDIR); \
		mkdir -p $(DISTDIR); \
		for pdf in $(FINAL_PDF_NAMES); do \
			mv "$(OUTDIR)/$$pdf" $(DISTDIR)/; \
			echo "Delivered: $(DISTDIR)/$$pdf"; \
		done; \
		echo "=== Complete! Production files are isolated in /$(DISTDIR) ==="; \
	else \
		echo "CRITICAL ERROR: Delivery aborted because one or more files failed to compile."; \
		exit 1; \
	fi

clean:
	@echo "=== Wiping Build and Distribution Folders ==="
	rm -rf $(OUTDIR)
	rm -rf $(DISTDIR)
	rm -rf songs/*/src/*
	rm -rf artifacts
