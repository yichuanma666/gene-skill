# Oil Tea CoLPAT Project Facts

Use these facts when editing the thesis or regenerating project artifacts.

## Final Counts

- Final oil tea CoLPAT members: 16.
- Candidate tables:
  - `assets/tables/CoLPAT_candidates.tsv`
  - `assets/tables/CoLPAT_members_full.tsv`
- PF01553 domain-coordinate table: `assets/tables/CoLPAT_PF01553_domain_coordinates.tsv`
- Secondary-structure table: `assets/tables/CoLPAT_secondary_structure.tsv`

## Domain Validation

- HMM model: Pfam `PF01553`, named `Acyltransferase`.
- HMM file: `assets/hmm/PF01553.hmm`.
- All 16 final CoLPAT members have PF01553 hits.
- Whole-protein PF01553 HMM E-value range in the final member table: `1.61e-25` to `6.83e-08`.
- Domain-coordinate results record 16 PF01553 domain rows.
- Thesis wording should say the candidates were screened with the PF01553 HMM and reviewed against CDD/SMART.
- Do not add unsupported extra domains.

## Phylogenetic and Homology Results

Arabidopsis best-homolog grouping:

- AtLPAT1-like: 9 CoLPAT members.
- AtLPAT2-like: 4 CoLPAT members.
- AtLPAT4-like: 3 CoLPAT members.

The current phylogenetic tree uses oil tea CoLPAT and Arabidopsis AtLPAT sequences only. Do not say that rice, rapeseed, or five plant-wide subfamilies were used unless new data are added.

## WGDI Collinearity

- WGDI detected 1370 genome-wide Co-At collinearity blocks.
- Blocks involving CoLPAT or AtLPAT loci: 5.
- Strict CoLPAT-AtLPAT synteny: CoLPAT16 and AtLPAT3 are in the same block.
- CoLPAT2, CoLPAT4, CoLPAT6, and CoLPAT7 also fall in WGDI blocks, but the corresponding Arabidopsis blocks do not contain AtLPAT loci.
- The best-homolog link figure is supplementary and must not be described as an MCScanX/WGDI synteny figure.

## Public Expression

- Public dataset: GSE190644.
- This is public population-expression evidence, not the user's own tissue/stage RNA-seq and not qRT-PCR.
- All 16 CoLPAT members map to LPAT-homologous public transcripts.
- Mapping confidence: 13 high-confidence and 3 low-confidence mappings.
- Higher median FPKM group: CoLPAT1, CoLPAT2, and CoLPAT4 at 14.10, followed by CoLPAT6, CoLPAT7, and CoLPAT8 at 12.28.
- Medium median FPKM group: CoLPAT3, CoLPAT5, CoLPAT9, CoLPAT10, CoLPAT11, and CoLPAT12 at 8.70.
- Lower overall expression group: CoLPAT13-CoLPAT16 at 3.14.
- The final manuscript uses a median-FPKM bar statistic, not an accession heatmap. Do not describe GSE190644 as tissue or developmental-stage expression.

Do not claim:

- tissue-specific expression from this project,
- seed-stage 120-150 d expression,
- qRT-PCR consistency,
- true TPM/FPKM matrix from the user's own samples.

## Final Manuscript Constraints

- Target length: about 13,000 Chinese non-space characters.
- Main text figure sequence: Figure 1-Figure 7.
- Figure names belong in captions only; do not put titles inside the image canvases.
- Keep final conclusion as numbered items under `4.2 结论`.
