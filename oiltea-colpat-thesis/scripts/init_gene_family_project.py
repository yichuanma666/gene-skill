#!/usr/bin/env python3
"""Initialize a standard gene family analysis workspace."""

from __future__ import annotations

import argparse
from pathlib import Path


CONFIG_TEMPLATE = """project:
  species: "{species}"
  family: "{family}"
  kingdom: "{kingdom}"
  expected_domain: "{domain}"
  reference_species: []
  notes: ""

modules:
  identification: true
  phylogeny: true
  motifs_domains: true
  gene_structure: true
  chromosome_location: true
  expression: false
  collinearity: false
  localization_or_structure: false

inputs:
  genome_fasta: ""
  annotation_gff_gtf: ""
  protein_fasta: ""
  cds_fasta: ""
  reference_family_proteins: ""
  hmm_profile: ""
  expression_matrix: ""
  sample_metadata: ""
  collinearity_results: ""
"""


CHECKLIST_TEMPLATE = """# Analysis Checklist

## Core Inputs

- [ ] genome FASTA
- [ ] annotation GFF3/GTF
- [ ] protein FASTA
- [ ] CDS FASTA
- [ ] reference family proteins
- [ ] HMM profile or domain accession

## Core Analysis

- [ ] homology-search candidate set
- [ ] HMM-search candidate set
- [ ] final validated member set
- [ ] final member information table
- [ ] phylogenetic tree
- [ ] motif/domain architecture
- [ ] gene structure

## Optional Analysis

- [ ] chromosome/scaffold location
- [ ] expression
- [ ] collinearity
- [ ] localization / protein structure

## Writing Checks

- [ ] homology, HMM, and final counts kept separate
- [ ] no unsupported tissue-expression claim
- [ ] no unsupported synteny claim
- [ ] figure titles moved to captions unless explicitly needed
"""


INPUTS_README = """# Inputs

Put raw input files here or in subfolders named for their data type.

Suggested subfolders:

- genome/
- annotation/
- proteins/
- cds/
- references/
- expression/
- collinearity/
"""


OUTPUTS_README = """# Outputs

Suggested subfolders:

- tables/
- figures/
- docs/
- logs/

Keep raw screening outputs separate from final filtered deliverables.
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a gene family project scaffold.")
    parser.add_argument("--root", required=True, help="Target project directory.")
    parser.add_argument("--species", default="Unknown species", help="Species name.")
    parser.add_argument("--family", default="Unknown family", help="Gene family name.")
    parser.add_argument("--kingdom", default="unspecified", help="Kingdom or major lineage.")
    parser.add_argument("--domain", default="", help="Expected family domain or HMM ID.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    dirs = [
        root / "inputs",
        root / "inputs" / "genome",
        root / "inputs" / "annotation",
        root / "inputs" / "proteins",
        root / "inputs" / "cds",
        root / "inputs" / "references",
        root / "inputs" / "expression",
        root / "inputs" / "collinearity",
        root / "outputs",
        root / "outputs" / "tables",
        root / "outputs" / "figures",
        root / "outputs" / "docs",
        root / "outputs" / "logs",
        root / "notes",
        root / "scripts",
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)

    write_text(
        root / "project_config.yaml",
        CONFIG_TEMPLATE.format(
            species=args.species,
            family=args.family,
            kingdom=args.kingdom,
            domain=args.domain,
        ),
    )
    write_text(root / "notes" / "analysis_checklist.md", CHECKLIST_TEMPLATE)
    write_text(root / "inputs" / "README.md", INPUTS_README)
    write_text(root / "outputs" / "README.md", OUTPUTS_README)

    print(f"Initialized project scaffold at: {root}")


if __name__ == "__main__":
    main()
