# PPLP Midterm Report (ACM 2-column)

This folder contains the ACM-formatted midterm report for the Privacy-Preserving Link Prediction (PPLP) project.

## Files

- **PPLP-midterm.tex** — Main LaTeX source
- **references.bib** — BibTeX references
- **acmart.cls** — ACM Primary Article Template class (sigconf = 2-column)
- **ACM-Reference-Format.bst** — Bibliography style
- **PPLP-midterm.pdf** — Compiled PDF (generated)

## Build

From this directory:

```bash
pdflatex PPLP-midterm
bibtex PPLP-midterm
pdflatex PPLP-midterm
pdflatex PPLP-midterm
```

Or use Overleaf: create a new project, upload `PPLP-midterm.tex`, `references.bib`, `acmart.cls`, and `ACM-Reference-Format.bst`, set the main file to `PPLP-midterm.tex`, and compile.

## Submission

For Canvas, you may submit `PPLP-midterm.pdf` as-is, or copy/rename it to `PPLP.pdf` if your course expects the filename `ProjectAcronym.pdf`.
