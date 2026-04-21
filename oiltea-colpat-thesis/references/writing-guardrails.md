# Writing Guardrails

Use these rules when writing the final report, thesis, or manuscript text.

## Count Logic

Keep the following counts separate:

- candidates from homology search
- candidates from HMM search
- nonredundant merged candidates
- final validated family members

Never collapse these numbers into one vague sentence.

## Safe Wording for Identification

Preferred pattern:

"A total of X candidates were retrieved by homology search and Y candidates were detected by HMM screening. After redundancy removal and domain validation, Z final family members were retained."

## Safe Wording for Domain Validation

Preferred pattern:

"Final members were screened with the [model/domain] HMM and reviewed with [SMART/CDD/InterPro/etc.] to confirm the expected conserved domain."

Do not claim extra domains unless they are actually supported by the validation files.

## Safe Wording for Expression

Use tissue/development wording only when the matrix really represents tissues or developmental stages.

If the matrix is accession-level, population-level, or mixed public data, use wording such as:

- public expression evidence
- accession-level expression profile
- population-level expression summary

Do not write:

- tissue-specific expression
- stage-specific expression
- qRT-PCR validation

unless those data are real and available.

## Safe Wording for Collinearity

Use "collinearity" or "synteny" only when the project has block-level results from MCScanX, WGDI, or an equivalent method.

If the project only has homolog links or BLAST best hits, use:

- homolog relationship
- best-hit relationship
- ortholog candidate

Do not rename homolog links as synteny.

## Figure Safety

- Put figure titles in captions by default.
- Avoid adding explanatory claims inside the image.
- If a figure is only a summary statistic, label it as a statistic, not as a biological time-course or tissue map.

## Scope Safety

Do not reuse one project's biological conclusions as if they were general truths for another species.

What can transfer:

- workflow
- table structure
- figure order
- wording patterns

What must be regenerated:

- member counts
- domains
- phylogeny
- expression conclusions
- collinearity conclusions
