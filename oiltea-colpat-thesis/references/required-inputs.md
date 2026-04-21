# Required Inputs

Use this checklist to decide which analysis modules are scientifically supported.

## Core Identification Inputs

At least one of the following is needed:

- trusted reference family protein sequences from one or more species
- a known Pfam/custom HMM profile for the family

Strong projects usually have both.

## Genome and Annotation Inputs

Needed for member localization and gene-structure analysis:

- genome FASTA
- GFF3 or GTF annotation

Recommended:

- protein FASTA
- CDS FASTA
- gene-to-transcript mapping

## Domain Validation Inputs

Needed for defensible final membership:

- Pfam/custom HMM model, or
- external domain review results from SMART, CDD, InterPro, or equivalent

Best practice:

- screen candidates with homology search and/or HMM
- validate the final members with a domain-aware method

## Phylogeny Inputs

Needed for phylogenetic analysis:

- final protein sequences for the target family
- optional reference family proteins from model or related species

## Motif and Domain Inputs

Needed for motif/domain architecture figures:

- final protein FASTA
- optional domain-coordinate table

## Gene Structure Inputs

Needed for exon-intron structure:

- annotation file with exon/CDS coordinates
- final gene IDs

## Chromosome or Scaffold Location Inputs

Needed for location plots:

- chromosome/scaffold coordinates for the final genes
- sequence lengths or genome index

## Collinearity Inputs

Needed for real synteny/collinearity claims:

- all-vs-all BLAST/DIAMOND results or equivalent
- genome annotation for both compared species or haplotypes
- MCScanX, WGDI, or equivalent block results

Without block-level results, only describe homolog links.

## Expression Inputs

Needed for a valid expression figure:

- TPM, FPKM, normalized counts, or comparable expression matrix
- clear sample metadata

The sample metadata must support the intended biological claim.

Examples:

- tissues
- developmental stages
- treatments
- population/accession panels

Do not reinterpret accession-level data as tissue data.

## Optional Structure and Feature Inputs

Needed only for extra modules:

- transmembrane prediction inputs
- signal peptide prediction inputs
- subcellular localization prediction outputs
- AlphaFold or other 3D structure resources

## If Inputs Are Missing

You can still do a partial analysis, but label it honestly.

Examples:

- no expression matrix -> skip expression figure
- no block results -> skip true collinearity claims
- no annotation -> skip gene-structure analysis
