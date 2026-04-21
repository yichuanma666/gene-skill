# Output Specification

Use this as a standard deliverable checklist.

## Core Tables

### Table 1: Final Family Members

Recommended columns:

- gene ID
- protein ID
- chromosome/scaffold
- genomic coordinates
- CDS length
- protein length
- domain or model support
- notes

### Table 2: Domain Validation

Recommended columns:

- gene ID
- domain/model name
- e-value or score
- domain coordinates
- validation source

### Table 3: Optional Expression Summary

Recommended columns:

- gene ID
- mapped transcript or gene
- confidence class
- mean expression
- median expression
- max expression
- sample coverage

## Core Figures

### Figure 1

Chromosome or scaffold distribution of final family members.

### Figure 2

Phylogenetic tree with target species and selected reference sequences.

### Figure 3

Conserved motifs or domain architecture.

### Figure 4

Gene structure.

## Optional Figures

### Expression Figure

Choose one based on the real data:

- heatmap for real tissues, stages, or treatments
- bar plot or box plot for accession-level or summary expression

### Collinearity Figure

Use only when real block-level results exist.

### Secondary or 3D Structure Figure

Use only when that analysis is part of the actual project.

## Standard Methods Items

Methods should clearly state:

- source of genome and annotation
- source of reference sequences
- HMM/domain model used
- search tools used
- filtering and validation logic
- data source for expression and collinearity

## Standard Results Items

Results should clearly state:

- candidate counts from each identification route
- final member count
- dominant domain or motif pattern
- main phylogenetic grouping
- optional expression and collinearity findings with evidence limits
