---
name: gene-family-analysis
description: Generic gene family analysis workflow for any species. Use when planning, reproducing, or writing a gene family study across plants, animals, fungi, or algae, including member identification, HMM/domain validation, phylogenetic analysis, motif/domain architecture, gene structure, chromosome location, collinearity, expression analysis, and manuscript-ready figures/tables.
---

# Generic Gene Family Analysis

## Scope

Use this skill for species-agnostic gene family analysis projects.

Supported project types:

- plants
- animals
- fungi
- algae and other eukaryotes

Do not assume every module applies to every species or dataset. Choose only the modules that are supported by the available inputs.

Start by reading:

- `references/required-inputs.md`
- `references/workflow.md`
- `references/writing-guardrails.md`

Read `references/output-spec.md` when preparing final figures, tables, or thesis text.

## Operating Rules

1. Inventory the user's real inputs before promising outputs.
2. Keep three counts separate whenever possible:
   - homology-search candidates
   - HMM/domain-search candidates
   - final validated family members
3. Do not fabricate expression, collinearity, qRT-PCR, localization, or subcellular results.
4. If the project only has best-homolog links, do not call them synteny.
5. If the expression matrix is public population/accession data, do not describe it as tissue or developmental-stage expression.
6. Preserve the distinction between:
   - domain screening model
   - external domain review source such as SMART/CDD/InterPro
   - final biological interpretation

## Minimal Workflow

1. Check which inputs exist:
   genome, annotation, proteins/CDS, reference family sequences, HMM/domain IDs, expression matrix, collinearity results.
2. Choose the identification route:
   - homology search from trusted reference family proteins
   - HMM search from family-domain models
   - best practice: combine both and validate the final set
3. Build the final member table.
4. Run only the supported downstream modules:
   - phylogeny
   - motifs/domains
   - gene structure
   - chromosome/scaffold location
   - collinearity
   - expression
   - secondary or tertiary structure
5. Write the results with explicit evidence boundaries.

## Core Modules

### Always preferred when inputs allow

- family-member identification
- domain validation
- phylogenetic analysis
- conserved motif or domain architecture
- gene structure analysis
- family-member information table

### Optional modules

- chromosome or scaffold localization
- interspecies or intraspecies collinearity
- expression heatmap or expression statistic
- cis-element analysis
- subcellular localization
- secondary structure, transmembrane helices, signal peptides, 3D modeling

## Expression and Collinearity Rules

- Use a heatmap only when columns are real biological samples or treatments that support that interpretation.
- If only accession-level or population-level expression exists, a summary bar plot or box plot is often safer than a tissue-expression heatmap.
- Use "collinearity" or "synteny" only when the project has real MCScanX/WGDI or equivalent block results.
- If only BLAST best hits exist, describe them as homolog relationships, not collinearity.

## Deliverables

When asked for a final package, aim to provide:

- a member-information table
- a domain-validation table
- figure-ready outputs without in-figure titles unless requested
- a short methods summary
- a short results summary with exact counts
- a clearly labeled optional-data section for expression/collinearity

## Bundled Helper

Use `scripts/init_gene_family_project.py` to scaffold a new project workspace with standard folders and starter metadata.
