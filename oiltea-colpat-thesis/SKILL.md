---
name: oiltea-colpat-thesis
description: Oil tea Camellia oleifera CoLPAT/LPAT thesis workflow for reproducing the existing gene-family analysis, validating PF01553/CDD/SMART domain evidence, regenerating figures without in-figure titles, and polishing the thesis DOCX to the reference-paper structure. Use when working on this specific oil tea CoLPAT thesis project, its final figures/tables, or follow-up edits to the 13k-word no-figure-title manuscript.
---

# Oil Tea CoLPAT Thesis

## Scope

Use this skill only for the oil tea (`Camellia oleifera`, Changlin40) CoLPAT/LPAT thesis project. Do not mix in the Pleurotus/fungal laccase project, the Pinellia SWEET template paper, raw genome downloads, DIAMOND temporary files, or unrelated WeChat attachments.

The packaged final manuscript is:

`assets/final_outputs/final_thesis_13000_no_fig_titles.docx`

It has approximately 13,250 non-space characters, 8 embedded images, clean Word captions in the main text, and no in-figure titles for the regenerated project figures.

## Project Facts

Read `references/project-facts.md` before changing scientific wording. Key points:

- Final CoLPAT members: 16.
- Domain model: Pfam `PF01553` (`Acyltransferase`) HMM, with CDD/SMART复核 wording in the thesis.
- PF01553 HMM E-value range in final members: `1.61e-25` to `6.83e-08`.
- Arabidopsis best-homolog groups: 9 AtLPAT1-like, 4 AtLPAT2-like, 3 AtLPAT4-like.
- Public expression data: GSE190644 only; 16 members mapped to LPAT-homologous transcripts, 13 high-confidence and 3 low-confidence mappings.
- WGDI: 1370 Co-At genome-wide collinearity blocks; 5 blocks involve CoLPAT/AtLPAT loci; CoLPAT16 and AtLPAT3 are in the same strict collinearity block.
- Do not claim real tissue/stage TPM/FPKM, qRT-PCR validation, or seed 120-150 d high expression unless new data are provided.

## Common Workflows

### Continue Thesis Edits

1. Start from `assets/final_outputs/final_thesis_13000_no_fig_titles.docx`.
2. Preserve the reference-paper structure:
   `1 引言 -> 2 材料与方法 -> 3 结果与分析 -> 4 讨论与结论`.
3. Keep result order:
   family identification, phylogenetic tree, conserved motifs/domains, gene structure, WGDI collinearity, secondary-structure table, public expression median-FPKM statistic.
4. Keep figure names in Word captions only; do not add titles inside images.
5. If adding claims, verify against packaged tables in `assets/tables`, `assets/expression`, and `assets/collinearity`.

### Regenerate Figures

Use `scripts/make_colpat_ref_style_figures.py` for chromosome location, phylogenetic tree, motifs, domains, gene structure, secondary-structure plot, and homolog-link figure.

Notes:

- The packaged script reflects the final no-title convention: avoid `ax.set_title(...)`.
- It was written for the original workspace and may contain `ROOT = F:\jyfx`; adjust `ROOT` if running elsewhere.
- Use figures from `assets/figures` when only document editing is needed.

### Rebuild Public Expression Evidence

Use `scripts/analyze_gse190644_expression.py` only if the original public GSE190644 files are available. The skill package intentionally excludes large raw expression files and translated protein databases.

Packaged final expression outputs:

- `assets/expression/CoLPAT_GSE190644_expression_mapping.tsv`
- `assets/expression/CoLPAT_GSE190644_FPKM_summary.tsv`
- `assets/expression/CoLPAT_GSE190644_expression_results.xlsx`

When writing the thesis, describe these as public population-expression evidence, not as the user's own tissue RNA-seq, tissue/stage heatmap, or qRT-PCR results.

### Rebuild WGDI Collinearity

Use `scripts/run_colpat_wgdi_collinearity.py` only when full oil tea/Arabidopsis genome inputs and DIAMOND/WGDI are available. The skill package intentionally excludes large GFF/protein databases and DIAMOND temporary files.

Use `assets/collinearity/CoLPAT_AtLPAT_WGDI_collinearity_blocks.tsv` for final manuscript wording when not rerunning WGDI.

### Reapply Final DOCX Polishing

The polishing scripts are included under `scripts/`:

- `update_thesis_doc.py`: integrates public expression and WGDI results into the earlier thesis.
- `cover_with_template_structure.py`: rearranges the thesis to match the Pinellia SWEET reference structure.
- `expand_thesis_text.py`: expands the manuscript to about 13k non-space characters.
- `fix_final_discussion_paragraph.py`: fixes the final UTF-8 discussion paragraph if PowerShell encoding corrupts it.

These scripts are project-specific and may contain absolute paths from `F:\jyfx`; adjust paths before reuse in another workspace.

## Packaged Resources

- `assets/final_outputs`: final DOCX.
- `assets/figures`: project figures, including no-title regenerated PNGs.
- `assets/tables`: CoLPAT member, domain, motif, secondary-structure, HMM, and AtLPAT homology result tables.
- `assets/sequences`: CoLPAT candidate CDS/protein FASTA and Arabidopsis LPAT FASTA.
- `assets/hmm`: PF01553 HMM used for domain screening.
- `assets/expression`: public-expression mapping and summary outputs.
- `assets/collinearity`: small WGDI block summary/config files.
- `scripts`: reproducible project scripts only.

## Exclusions

The package deliberately excludes:

- `fungi_pleurotus/` and fungal zip files.
- `template/` and the Pinellia SWEET reference DOCX.
- Raw Changlin40 genome FASTA/GFF files and compressed genome downloads.
- Raw GSE190644 archives, translated protein databases, and large expression source matrices.
- DIAMOND executables, `.dmnd` databases, and temporary files.
- Word lock files such as `~$*.docx`.
