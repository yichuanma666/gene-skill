# Workflow

This is the standard order for a robust gene family analysis.

## 1. Define the Biological Scope

Record:

- species
- assembly or annotation version
- target gene family
- expected domain(s)
- reference species used for homolog collection

## 2. Collect and Normalize Inputs

Prepare:

- protein FASTA
- CDS FASTA if available
- genome FASTA if available
- annotation file
- reference family sequences
- HMM profile or domain accession

Normalize names early so that gene IDs stay consistent across tables and figures.

## 3. Screen Family Candidates

Use one or both:

- homology search
- HMM search

Keep the raw outputs. Do not overwrite them with the final filtered set.

## 4. Validate Final Members

Build the final member set with explicit rules.

Typical rules:

- remove redundant isoforms if the project is gene-level
- remove truncated false positives if unsupported
- require the expected domain or catalytic signature
- review borderline candidates manually

Always report:

- number from homology search
- number from HMM search
- final validated member count

## 5. Build the Core Result Table

A standard final member table should include:

- gene ID
- protein ID or transcript ID
- chromosome/scaffold
- start/end
- protein length
- predicted domain(s)
- evidence source

Optional additions:

- molecular weight
- pI
- transmembrane helices
- subcellular localization

## 6. Run Core Downstream Analyses

Preferred order:

1. phylogeny
2. motif/domain architecture
3. gene structure
4. chromosome/scaffold distribution

## 7. Add Optional Modules

Run only if supported:

- collinearity
- expression
- cis-elements
- protein structure or localization

## 8. Make Figures and Tables

Keep figure canvases clean. Put full figure titles in captions unless the user explicitly wants titles inside the images.

## 9. Write Methods and Results

Match every sentence to actual evidence.

The writing should answer:

- how members were screened
- what model or references were used
- how many candidates each method found
- how many final members were retained
- which optional modules were truly supported

## 10. Package Deliverables

A good delivery bundle usually includes:

- raw screening files
- final member table
- final figures
- brief methods and results summary
- explanation of unsupported modules
