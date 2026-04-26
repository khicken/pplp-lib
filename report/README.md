# PPLP Reports (ACM 2-column)

This folder contains the ACM-formatted midterm and final reports for the Privacy-Preserving Link Prediction (PPLP) project.

## Files

- **PPLP-midterm.tex** — Midterm LaTeX source
- **PPLP-final.tex** — Final LaTeX source (extends the midterm with proposed solution, demos, threat model expansion, tradeoffs, limitations, future work, conclusion)
- **references.bib** — Shared BibTeX references
- **acmart.cls** — ACM Primary Article Template class (sigconf = 2-column)
- **ACM-Reference-Format.bst** — Bibliography style
- **PPLP-midterm.pdf** / **PPLP-final.pdf** — Compiled PDFs (generated)

## Build

From this directory (replace `PPLP-final` with `PPLP-midterm` as needed):

```bash
pdflatex PPLP-final
bibtex PPLP-final
pdflatex PPLP-final
pdflatex PPLP-final
```

Or use Overleaf: create a new project, upload `PPLP-final.tex`, `references.bib`, `acmart.cls`, and `ACM-Reference-Format.bst` plus the `figures/` directory, set the main file to `PPLP-final.tex`, and compile.

## Submission

For Canvas, submit `PPLP-final.pdf` (rename to `PPLP.pdf` if the course expects `ProjectAcronym.pdf`) along with the source code archive.
