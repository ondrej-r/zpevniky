SHELL := /bin/bash
export LANG := C.UTF-8
export LC_ALL := C.UTF-8

PYTHON := python3
OUTDIR := build
DISTDIR := dist

PDFS := \
    $(OUTDIR)/nas_zpevnik_A4.pdf \
    $(OUTDIR)/nas_zpevnik_A5.pdf \
    $(OUTDIR)/oddilovy_zpevnik_I_A4.pdf \
    $(OUTDIR)/oddilovy_zpevnik_I_A5.pdf \
    $(OUTDIR)/oddilovy_zpevnik_II_A4.pdf \
    $(OUTDIR)/oddilovy_zpevnik_II_A5.pdf

FINAL_PDF_NAMES := \
    nas_zpevnik_A4.pdf \
    nas_zpevnik_A5.pdf \
    oddilovy_zpevnik_I_A4.pdf \
    oddilovy_zpevnik_I_A5.pdf \
    oddilovy_zpevnik_II_A4.pdf \
    oddilovy_zpevnik_II_A5.pdf

.PHONY: all clean prepare compile deliver

all: prepare
	@$(MAKE) compile
	@$(MAKE) deliver

prepare:
	@mkdir -p $(OUTDIR)
	@echo "=== Running convert.py scripts ==="
	$(PYTHON) songs/nas_zpevnik/convert.py
	$(PYTHON) songs/oddilovy_zpevnik_I/convert.py
	$(PYTHON) songs/oddilovy_zpevnik_II/convert.py

compile: $(PDFS)
	@echo "=== PDF Compilation Phase Complete ==="

$(OUTDIR)/nas_zpevnik_%.pdf: songbooks/nas_zpevnik_%.tex $(OUTDIR)/nas_zpevnik_songs_list.tex
	@echo "=== Compiling $< ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/oddilovy_zpevnik_I_%.pdf: songbooks/oddilovy_zpevnik_I_%.tex $(OUTDIR)/oddilovy_zpevnik_I_songs_list.tex
	@echo "=== Compiling $< ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

$(OUTDIR)/oddilovy_zpevnik_II_%.pdf: songbooks/oddilovy_zpevnik_II_%.tex $(OUTDIR)/oddilovy_zpevnik_II_songs_list.tex
	@echo "=== Compiling $< ==="
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
	rm -rf artifacts
