from __future__ import annotations

import gzip
import math
import subprocess
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from Bio.Seq import Seq
from pyhmmer import easel, hmmer, plan7


ROOT = Path(r"F:\jyfx")
OUT = ROOT / "analysis_outputs"
EXPR_DIR = OUT / "expression_public"
FIG_DIR = OUT / "figures_ref_style"
PFAM_HMM = OUT / "PF01553.hmm"

GSE_FASTA_GZ = EXPR_DIR / "GSE190644_All_transcripts_TWAS.fasta.gz"
GSE_FPKM = EXPR_DIR / "GSE190644_GEO_FPKM_matrix_for_CON_population.xlsx"
COLPAT_PEP = OUT / "CoLPAT_candidates.proteins.fa"
DIAMOND = OUT / "downloads" / "diamond" / "diamond.exe"

GSE_PEP = EXPR_DIR / "GSE190644_translated_proteins.fa"
GSE_TRANSLATION_TSV = EXPR_DIR / "GSE190644_translation_summary.tsv"
GSE_HMM_TSV = EXPR_DIR / "GSE190644_PF01553_hmm_hits.tsv"
COLPAT_SIMPLE_PEP = EXPR_DIR / "CoLPAT_candidates.simple.proteins.fa"
DIAMOND_DB = EXPR_DIR / "GSE190644_translated_proteins.dmnd"
DIAMOND_OUT = EXPR_DIR / "CoLPAT_vs_GSE190644_transcripts.diamond.tsv"

MAPPING_TSV = EXPR_DIR / "CoLPAT_GSE190644_expression_mapping.tsv"
EXPR_ALL_TSV = EXPR_DIR / "CoLPAT_GSE190644_FPKM_all_accessions.tsv"
EXPR_SUMMARY_TSV = EXPR_DIR / "CoLPAT_GSE190644_FPKM_summary.tsv"
EXPR_XLSX = EXPR_DIR / "CoLPAT_GSE190644_expression_results.xlsx"
HEATMAP_FULL = FIG_DIR / "fig8_expression_heatmap_GSE190644_all_accessions.png"
HEATMAP_TOP = FIG_DIR / "fig8_expression_heatmap_GSE190644_top40_accessions.png"
BARPLOT = FIG_DIR / "fig9_expression_median_FPKM_GSE190644.png"


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def read_fasta(path: Path):
    name = None
    chunks: list[str] = []
    with open_text(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    yield name, "".join(chunks)
                name = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line)
        if name is not None:
            yield name, "".join(chunks)


def write_fasta(handle, name: str, seq: str, width: int = 60):
    handle.write(f">{name}\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i : i + width] + "\n")


def as_text(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def translate_best_orf(nt: str) -> tuple[str, int, int, int]:
    seq = nt.upper().replace("U", "T")
    best = ("", 0, 0, 0)
    for frame in range(3):
        trimmed = seq[frame : len(seq) - ((len(seq) - frame) % 3)]
        if not trimmed:
            continue
        aa = str(Seq(trimmed).translate(to_stop=False))
        start = 0
        for part in aa.split("*"):
            end = start + len(part)
            if len(part) > len(best[0]):
                best = (part, frame + start * 3, frame + end * 3, frame)
            start = end + 1
    return best


def prepare_translated_proteins():
    if GSE_PEP.exists() and GSE_TRANSLATION_TSV.exists():
        return
    rows = []
    with GSE_PEP.open("w", encoding="utf-8") as pep:
        for tid, nt in read_fasta(GSE_FASTA_GZ):
            aa, nt_start, nt_end, frame = translate_best_orf(nt)
            if len(aa) < 30:
                continue
            write_fasta(pep, tid, aa)
            rows.append(
                {
                    "transcript_id": tid,
                    "nt_length": len(nt),
                    "orf_start_0based": nt_start,
                    "orf_end_0based": nt_end,
                    "frame": frame,
                    "aa_length": len(aa),
                }
            )
    pd.DataFrame(rows).to_csv(GSE_TRANSLATION_TSV, sep="\t", index=False)


def load_hmm(path: Path):
    with path.open("rb") as handle:
        hmms = list(plan7.HMMFile(handle))
    if not hmms:
        raise RuntimeError(f"No HMM found in {path}")
    return hmms[0]


def hmmsearch_pf01553():
    if GSE_HMM_TSV.exists():
        return
    hmm = load_hmm(PFAM_HMM)
    records = []
    with easel.SequenceFile(str(GSE_PEP), digital=True, alphabet=hmm.alphabet) as seq_file:
        proteins = list(seq_file)
    hits = next(hmmer.hmmsearch(hmm, proteins, cpus=4, E=1e-5, domE=1e-5))
    for hit in hits:
        if not hit.included:
            continue
        domains = [d for d in hit.domains if d.included]
        best_domain = min(domains, key=lambda d: d.i_evalue) if domains else None
        records.append(
            {
                "transcript_id": as_text(hit.name),
                "hmm_evalue": hit.evalue,
                "hmm_score": hit.score,
                "best_domain_evalue": best_domain.i_evalue if best_domain else math.nan,
                "best_domain_score": best_domain.score if best_domain else math.nan,
                "env_from": best_domain.env_from if best_domain else math.nan,
                "env_to": best_domain.env_to if best_domain else math.nan,
            }
        )
    pd.DataFrame(records).sort_values(["hmm_evalue", "hmm_score"], ascending=[True, False]).to_csv(
        GSE_HMM_TSV, sep="\t", index=False
    )


def simplify_colpat_headers():
    if COLPAT_SIMPLE_PEP.exists():
        return
    with COLPAT_SIMPLE_PEP.open("w", encoding="utf-8") as out:
        for header, seq in read_fasta(COLPAT_PEP):
            colpat = header.split("|")[0]
            write_fasta(out, colpat, seq)


def run_diamond():
    if not DIAMOND.exists():
        raise RuntimeError(f"DIAMOND executable not found: {DIAMOND}")
    if not DIAMOND_DB.exists():
        subprocess.run(
            [str(DIAMOND), "makedb", "--in", str(GSE_PEP), "-d", str(DIAMOND_DB.with_suffix(""))],
            check=True,
        )
    if not DIAMOND_OUT.exists():
        subprocess.run(
            [
                str(DIAMOND),
                "blastp",
                "-q",
                str(COLPAT_SIMPLE_PEP),
                "-d",
                str(DIAMOND_DB),
                "-o",
                str(DIAMOND_OUT),
                "--outfmt",
                "6",
                "qseqid",
                "sseqid",
                "pident",
                "length",
                "qlen",
                "slen",
                "qstart",
                "qend",
                "sstart",
                "send",
                "evalue",
                "bitscore",
                "qcovhsp",
                "scovhsp",
                "--max-target-seqs",
                "100",
                "--evalue",
                "1e-3",
                "--threads",
                "4",
                "--very-sensitive",
            ],
            check=True,
        )


def build_expression_outputs():
    hmm = pd.read_csv(GSE_HMM_TSV, sep="\t")
    cols = [
        "CoLPAT",
        "GSE190644_transcript",
        "pident",
        "align_len",
        "q_len",
        "s_len",
        "q_start",
        "q_end",
        "s_start",
        "s_end",
        "evalue",
        "bitscore",
        "qcovhsp",
        "scovhsp",
    ]
    blast = pd.read_csv(
        DIAMOND_OUT,
        sep="\t",
        header=None,
        names=cols,
    )
    blast = blast.merge(hmm, left_on="GSE190644_transcript", right_on="transcript_id", how="left")
    blast["has_PF01553"] = blast["hmm_evalue"].notna()
    best = (
        blast.sort_values(["CoLPAT", "has_PF01553", "bitscore", "qcovhsp"], ascending=[True, False, False, False])
        .groupby("CoLPAT", as_index=False)
        .head(1)
        .copy()
    )
    def confidence(row):
        if row["pident"] >= 60 and (row["qcovhsp"] >= 50 or row["scovhsp"] >= 70) and row["bitscore"] >= 100:
            return "High"
        if bool(row["has_PF01553"]) and row["bitscore"] >= 100:
            return "Medium"
        if bool(row["has_PF01553"]) and row["evalue"] <= 1e-5:
            return "Low"
        return "Weak"

    best["mapping_confidence"] = best.apply(confidence, axis=1)
    best.to_csv(MAPPING_TSV, sep="\t", index=False)

    expr = pd.read_excel(GSE_FPKM, sheet_name=0)
    expr = expr.rename(columns={expr.columns[0]: "Geneid"})
    selected = best[["CoLPAT", "GSE190644_transcript"]].dropna()
    expr_sel = selected.merge(expr, left_on="GSE190644_transcript", right_on="Geneid", how="left")
    expr_sel = expr_sel.drop(columns=["Geneid"])
    expr_sel.to_csv(EXPR_ALL_TSV, sep="\t", index=False)

    value_cols = [c for c in expr_sel.columns if c not in {"CoLPAT", "GSE190644_transcript"}]
    summary = []
    for _, row in expr_sel.iterrows():
        values = pd.to_numeric(row[value_cols], errors="coerce")
        summary.append(
            {
                "CoLPAT": row["CoLPAT"],
                "GSE190644_transcript": row["GSE190644_transcript"],
                "mapping_confidence": best.set_index("CoLPAT").loc[row["CoLPAT"], "mapping_confidence"],
                "mean_FPKM": values.mean(),
                "median_FPKM": values.median(),
                "max_FPKM": values.max(),
                "min_FPKM": values.min(),
                "sd_FPKM": values.std(),
                "detected_accessions_FPKM_gt_1": int((values > 1).sum()),
                "total_accessions": int(values.notna().sum()),
            }
        )
    summary_df = pd.DataFrame(summary).sort_values("CoLPAT")
    summary_df.to_csv(EXPR_SUMMARY_TSV, sep="\t", index=False)

    with pd.ExcelWriter(EXPR_XLSX, engine="openpyxl") as writer:
        best.to_excel(writer, "mapping", index=False)
        expr_sel.to_excel(writer, "FPKM_all_accessions", index=False)
        summary_df.to_excel(writer, "FPKM_summary", index=False)
        hmm.to_excel(writer, "PF01553_hits_in_GSE", index=False)

    draw_heatmaps(expr_sel, summary_df, value_cols)


def row_zscore(data: pd.DataFrame) -> pd.DataFrame:
    arr = np.log2(data.astype(float) + 1.0)
    mean = arr.mean(axis=1)
    sd = arr.std(axis=1).replace(0, np.nan)
    return arr.sub(mean, axis=0).div(sd, axis=0).fillna(0)


def draw_heatmaps(expr_sel: pd.DataFrame, summary_df: pd.DataFrame, value_cols: list[str]):
    FIG_DIR.mkdir(exist_ok=True)
    matrix = expr_sel.set_index("CoLPAT")[value_cols].apply(pd.to_numeric, errors="coerce")
    matrix = matrix.loc[summary_df["CoLPAT"]]
    z = row_zscore(matrix)

    plt.figure(figsize=(16, 5.6))
    sns.heatmap(z, cmap="RdYlBu_r", center=0, xticklabels=False, yticklabels=True, cbar_kws={"label": "row Z-score"})
    plt.xlabel("GSE190644 oil-tea accessions (n=221)")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(HEATMAP_FULL, dpi=300)
    plt.close()

    var_cols = z.var(axis=0).sort_values(ascending=False).head(40).index.tolist()
    plt.figure(figsize=(14, 5.8))
    sns.heatmap(
        z[var_cols],
        cmap="RdYlBu_r",
        center=0,
        xticklabels=True,
        yticklabels=True,
        cbar_kws={"label": "row Z-score"},
    )
    plt.xticks(rotation=60, ha="right", fontsize=7)
    plt.xlabel("Top 40 variable accessions")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(HEATMAP_TOP, dpi=300)
    plt.close()

    plot_df = summary_df.sort_values("median_FPKM", ascending=True)
    plt.figure(figsize=(7.8, 5.6))
    plt.barh(plot_df["CoLPAT"], plot_df["median_FPKM"], color="#2f7f7a")
    plt.xlabel("Median FPKM across 221 accessions")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(BARPLOT, dpi=300)
    plt.close()


def main():
    EXPR_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)
    prepare_translated_proteins()
    hmmsearch_pf01553()
    simplify_colpat_headers()
    run_diamond()
    build_expression_outputs()
    print(f"Wrote {MAPPING_TSV}")
    print(f"Wrote {EXPR_XLSX}")
    print(f"Wrote {HEATMAP_FULL}")
    print(f"Wrote {HEATMAP_TOP}")


if __name__ == "__main__":
    main()
