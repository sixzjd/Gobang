---
name: pdf-to-latex
description: Convert a PDF to LaTeX that compiles to visually identical output. Extracts text structure, generates matching LaTeX source, and compiles with xelatex.
---

# PDF to LaTeX Precise Reproduction

Convert a PDF document into LaTeX source code that, when compiled, produces output visually identical to the original.

## Prerequisites

- **poppler** (`pdftotext`, `pdfinfo`): `brew install poppler`
- **xelatex** (from MacTeX): `brew install --cask mactex`
- **pymupdf** (optional, for glyph-level edits): `pip3 install pymupdf`

Check availability before starting:
```bash
which pdftotext pdfinfo xelatex && python3 -c "import fitz; print('pymupdf ok')"
```

## Workflow

### Step 1: Extract PDF metadata and content

```bash
pdfinfo '<PDF_PATH>'
pdftotext -layout '<PDF_PATH>' /tmp/pdf_content.txt
```

Record: page count, page size, font info, text content with layout.

### Step 2: Analyze document structure

Read the extracted text and identify:
- Title page layout (centering, font sizes, spacing)
- Body text structure (single/two-column, paragraphs, headings)
- Special elements (tables, figures, footnotes, headers/footers)
- References/bibliography format
- Page numbering style

### Step 3: Identify fonts and CJK support

For Chinese/CJK documents:
- Use `\documentclass[fontset=fandol]{ctexart}` (avoids STHeiti issues on macOS)
- Available CJK fonts: `Heiti SC` (黑体), `Songti SC` (宋体), `STSong` (华文宋体)
- **Do NOT use Unicode curly quotes** (`""`) directly — fandol renders them incorrectly
- Use LaTeX quote syntax: ``` ``text'' ``` for opening+closing quotes

For Latin-only documents:
- Use `fontspec` package with system fonts

### Step 4: Generate LaTeX source

Write the `.tex` file matching the original layout:
- Match page geometry (`geometry` package)
- Reproduce typography (font sizes, line spacing, paragraph spacing)
- Use `multicol` package for two-column layouts
- Match heading styles and section formatting
- Preserve all text content exactly

### Step 5: Compile and verify

```bash
xelatex -interaction=nonstopmode -output-directory=/tmp '<FILENAME>.tex' 2>&1 | tail -20
xelatex -interaction=nonstopmode -output-directory=/tmp '<FILENAME>.tex' 2>&1 | tail -5
```

Run twice for cross-references. Compare output PDF with original.

### Step 6: Iterate on differences

Common issues to fix:
- **Quote characters wrong**: Use LaTeX ``` `` ``` / `''` syntax, not Unicode
- **Font size/weight mismatch**: Adjust `\fontsize{}` and `\fontseries{}`
- **Spacing off**: Tune `\vspace{}`, `\parskip`, `\baselineskip`
- **Layout shifted**: Adjust `geometry` margins and `multicol` column widths

## Gotchas

- pymupdf `insert_text(fontname="china-s")` uses a different built-in font, NOT the original STSong — causes bold/size changes. For pixel-perfect PDF edits, use content stream glyph swap instead.
- Content stream glyph swap: decompress zlib content streams, replace hex byte sequences for quote glyphs, recompress. STSong: `<49A7>`↔`<49A8>`; STHeiti: `<1BB0>`↔`<1BB1>`; LMRoman10: `<01F3>`↔`<01F4>`.
- `''` in LaTeX produces U+201D (closing double quote) for BOTH opening and closing — wrong for Chinese. Always use ``` `` ``` and `''` syntax or Unicode `""` directly (but beware fandol rendering).
