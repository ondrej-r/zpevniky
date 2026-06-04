SHELL := /bin/bash
export LANG := C.UTF-8
export LC_ALL := C.UTF-8

PYTHON := python3
OUTDIR := build

PDFS := \
	$(OUTDIR)/nas_zpevnik_A4.pdf \
	$(OUTDIR)/nas_zpevnik_A5.pdf \
	$(OUTDIR)/oddilovy_zpevnik_I_A4.pdf \
	$(OUTDIR)/oddilovy_zpevnik_I_A5.pdf \
	$(OUTDIR)/oddilovy_zpevnik_II_A4.pdf \
	$(OUTDIR)/oddilovy_zpevnik_II_A5.pdf

.PHONY: all clean prepare

all: prepare $(PDFS)

prepare:
	@echo "=== Running convert.py ==="
	$(PYTHON) songs/nas_zpevnik/convert.py
	$(PYTHON) songs/oddilovy_zpevnik_i/convert.py
	$(PYTHON) songs/oddilovy_zpevnik_ii/convert.py

$(OUTDIR)/%.pdf: songbooks/%.tex
	@mkdir -p $(OUTDIR)
	@echo "=== Compiling $< ==="
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<
	pdflatex -interaction=nonstopmode -output-directory=$(OUTDIR) $<

clean:
	rm -rf $(OUTDIR)
