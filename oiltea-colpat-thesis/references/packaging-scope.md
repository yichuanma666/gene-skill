# Packaging Scope

This skill package contains only files directly related to the oil tea CoLPAT thesis workflow.

## Included

Project scripts:

- `scripts/extract_lpat_candidates.py`
- `scripts/make_colpat_ref_style_figures.py`
- `scripts/analyze_gse190644_expression.py`
- `scripts/run_colpat_wgdi_collinearity.py`
- `scripts/update_thesis_doc.py`
- `scripts/cover_with_template_structure.py`
- `scripts/expand_thesis_text.py`
- `scripts/fix_final_discussion_paragraph.py`

Final outputs:

- `assets/final_outputs/final_thesis_13000_no_fig_titles.docx`
- `assets/figures/*.png`

Small supporting data:

- final member tables,
- PF01553 domain tables,
- expression mapping/summary tables,
- WGDI block summary,
- CoLPAT and Arabidopsis LPAT FASTA files,
- PF01553 HMM.

## Excluded

Excluded because they are unrelated or too large for a reusable skill:

- `fungi_pleurotus/`
- `fungi_pleurotus.zip`
- `fungi_pleurotus (2).zip`
- `template/`
- Pinellia SWEET reference DOCX
- raw Changlin40 genome FASTA/GFF files
- upstream promoter FASTA
- raw GSE190644 archives and source expression matrix
- generated protein databases and DIAMOND `.dmnd` files
- DIAMOND temporary files
- downloaded tools/executables
- Word lock files

If future work requires rerunning the full pipeline from raw genomes, obtain those raw files separately and adjust script `ROOT` constants.
