SHELL := /bin/bash
export LANG := C.UTF-8
export LC_ALL := C.UTF-8

PYTHON := python3
OUTDIR := build
DISTDIR := dist
BOOKDIR := book
LISTDIR := songslists

# List of all songbooks to process
SONGBOOKS := nas_zpevnik oddilovy_zpevnik_I oddilovy_zpevnik_II

# Reconstruct targets to look exactly like your preferred output names: build/SONGBOOK_FORMAT+VARIANT.pdf
PDFS := $(foreach sb,$(SONGBOOKS),\
          $(foreach fmt,A4 A5,\
            $(foreach var,singer musician,$(OUTDIR)/$(sb)_$(fmt)+$(var).pdf)))

# Extract only the file names for delivery verification
FINAL_PDF_NAMES := $(notdir $(PDFS))

.PHONY: everything all clean prepare songs compile deliver booklets

# Run the code three times in a row to fix table of contents numbering, then generate brochures
everything:
	@$(MAKE) clean
	@$(MAKE) all
	@$(MAKE) all
	@$(MAKE) all
	@$(MAKE) booklets

all:
	@$(MAKE) prepare
	@$(MAKE) compile
	@$(MAKE) deliver

prepare:
	@mkdir -p $(OUTDIR)
	@mkdir -p $(LISTDIR)

txttotex:
	rm -rf songs/*/src/*
	rm -rf $(LISTDIR)
	@$(MAKE) songs

songs:
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

$(OUTDIR)/%_A4+singer.pdf: songbooks/%_A4+singer.tex $(LISTDIR)/%_singer_songs_list.tex
	@echo "=== Compiling $< (Singer A4) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/%_A5+singer.pdf: songbooks/%_A5+singer.tex $(LISTDIR)/%_singer_songs_list.tex
	@echo "=== Compiling $< (Singer A5) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/%_A4+musician.pdf: songbooks/%_A4+musician.tex $(LISTDIR)/%_musician_songs_list.tex
	@echo "=== Compiling $< (Musician A4) ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/%_A5+musician.pdf: songbooks/%_A5+musician.tex $(LISTDIR)/%_musician_songs_list.tex
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

booklets:
	@echo "=== Generating 12 Brochure Booklets ==="
	rm -rf $(BOOKDIR)
	mkdir -p $(OUTDIR) $(BOOKDIR)
	@for pdf in $(FINAL_PDF_NAMES); do \
		echo "Processing booklet for $$pdf..."; \
		cp "$(DISTDIR)/$$pdf" $(OUTDIR)/; \
		pushd $(OUTDIR) > /dev/null; \
		pdfbook2 -nsp a4paper "$$pdf"; \
		BASE_NAME=$${pdf%.pdf}; \
		mv "$${BASE_NAME}-book.pdf" "../$(BOOKDIR)/$${BASE_NAME}+book.pdf"; \
		popd > /dev/null; \
	done
	@echo "=== Booklet Generation Complete! Brochures are isolated in /$(BOOKDIR) ==="

clean:
	@echo "=== Wiping Build, Distribution, and Book Folders ==="
	rm -rf $(OUTDIR)
	rm -rf $(DISTDIR)
	rm -rf $(BOOKDIR)
	rm -rf artifacts
