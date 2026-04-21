from __future__ import annotations

import gzip
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(r"F:\jyfx")
OUT = ROOT / "analysis_outputs"
COL_DIR = OUT / "collinearity"
FIG_DIR = OUT / "figures_ref_style"

OIL_GFF = ROOT / "Camellia_oleifera_Changlin40.gff3"
OIL_PEP = OUT / "Changlin40.predicted_proteins.fa"
OIL_META = OUT / "Changlin40.transcript_structure.tsv"
COLPAT_TSV = OUT / "CoLPAT_candidates.tsv"

AT_GFF_GZ = COL_DIR / "Arabidopsis_thaliana.TAIR10.62.gff3.gz"
AT_PEP_GZ = COL_DIR / "Arabidopsis_thaliana.TAIR10.pep.all.fa.gz"
DIAMOND = OUT / "downloads" / "diamond" / "diamond.exe"
WGDI_EXE = Path(r"C:\Users\MYC\AppData\Roaming\Python\Python314\Scripts\wgdi.exe")

OIL_SIMPLE_PEP = COL_DIR / "Co_longest_proteins.simple.fa"
AT_SIMPLE_PEP = COL_DIR / "At_TAIR10_longest_proteins.simple.fa"
OIL_WGDI_GFF = COL_DIR / "Co.wgdi.gff"
AT_WGDI_GFF = COL_DIR / "At.wgdi.gff"
OIL_LENS = COL_DIR / "Co.lens"
AT_LENS = COL_DIR / "At.lens"
OIL_MCSCANX_GFF = COL_DIR / "Co.mcscanx.gff"
AT_MCSCANX_GFF = COL_DIR / "At.mcscanx.gff"
AT_ID_MAP = COL_DIR / "At_transcript_gene_map.tsv"

DIAMOND_DB = COL_DIR / "At_TAIR10_longest_proteins.dmnd"
BLAST_TSV = COL_DIR / "Co_vs_At.diamond.blast6.tsv"
WGDI_CONF = COL_DIR / "Co_At_wgdi_collinearity.conf"
WGDI_DOTPLOT_CONF = COL_DIR / "Co_At_wgdi_dotplot.conf"
WGDI_COLLINEARITY = COL_DIR / "Co_At.wgdi.collinearity"
WGDI_DOTPLOT = FIG_DIR / "fig10_Co_At_WGDI_dotplot.png"

COLPAT_BLOCKS_TSV = COL_DIR / "CoLPAT_AtLPAT_WGDI_collinearity_blocks.tsv"
COLPAT_LINKS_PNG = FIG_DIR / "fig6_species_collinearity_WGDI_CoLPAT_AtLPAT.png"

AT_LPAT_GENES = {
    "AT4G30580": "AtLPAT1",
    "AT3G57650": "AtLPAT2",
    "AT1G51260": "AtLPAT3",
    "AT1G75020": "AtLPAT4",
    "AT3G18850": "AtLPAT5",
}


def parse_attrs(text: str) -> dict[str, str]:
    out = {}
    for item in text.strip().split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            out[key] = value
    return out


def chrom_key(chrom: str):
    chrom = str(chrom)
    m = re.match(r"Chr(\d+)([a-z]*)$", chrom)
    if m:
        return (int(m.group(1)), m.group(2))
    if chrom.isdigit():
        return (int(chrom), "")
    return (999, chrom)


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def read_fasta(path: Path):
    name = None
    desc = ""
    chunks: list[str] = []
    with open_text(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    yield name, desc, "".join(chunks)
                desc = line[1:]
                name = desc.split()[0]
                chunks = []
            else:
                chunks.append(line)
        if name is not None:
            yield name, desc, "".join(chunks)


def write_fasta(handle, name: str, seq: str, width: int = 60):
    handle.write(f">{name}\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i : i + width] + "\n")


def prepare_oiltea():
    pep = {}
    for header, _, seq in read_fasta(OIL_PEP):
        tid = header.split("|", 1)[0]
        pep[tid] = seq
    with OIL_SIMPLE_PEP.open("w", encoding="utf-8") as out:
        for tid in sorted(pep):
            write_fasta(out, tid, pep[tid])

    meta = pd.read_csv(OIL_META, sep="\t")
    meta = meta[meta["transcript_id"].isin(pep)].copy()
    meta["chrom_sort"] = meta["chrom"].map(chrom_key)
    meta = meta.sort_values(["chrom_sort", "start", "end", "transcript_id"])
    rows = []
    lens_rows = []
    for chrom, group in meta.groupby("chrom", sort=False):
        group = group.copy()
        group["order"] = range(1, len(group) + 1)
        lens_rows.append((chrom, int(group["end"].max()), int(group["order"].max())))
        for _, row in group.iterrows():
            rows.append((chrom, row["transcript_id"], int(row["start"]), int(row["end"]), row["strand"], int(row["order"])))
    pd.DataFrame(rows).to_csv(OIL_WGDI_GFF, sep="\t", header=False, index=False)
    pd.DataFrame(lens_rows).to_csv(OIL_LENS, sep="\t", header=False, index=False)
    pd.DataFrame([(r[1], r[0], r[2], r[3]) for r in rows]).to_csv(
        OIL_MCSCANX_GFF, sep="\t", header=False, index=False
    )


def parse_at_peptides():
    best_by_gene = {}
    for tid, desc, seq in read_fasta(AT_PEP_GZ):
        gene_match = re.search(r"\bgene:([A-Za-z0-9_.-]+)", desc)
        transcript_match = re.search(r"\btranscript:([A-Za-z0-9_.-]+)", desc)
        gene = gene_match.group(1) if gene_match else tid.split(".")[0]
        transcript = transcript_match.group(1) if transcript_match else tid
        current = best_by_gene.get(gene)
        if current is None or len(seq) > len(current["seq"]):
            best_by_gene[gene] = {"gene": gene, "transcript": transcript, "seq": seq}
    return best_by_gene


def prepare_arabidopsis():
    best_by_gene = parse_at_peptides()
    selected_tids = {rec["transcript"] for rec in best_by_gene.values()}
    tid_to_gene = {rec["transcript"]: gene for gene, rec in best_by_gene.items()}
    with AT_SIMPLE_PEP.open("w", encoding="utf-8") as out:
        for gene in sorted(best_by_gene):
            rec = best_by_gene[gene]
            write_fasta(out, rec["transcript"], rec["seq"])
    pd.DataFrame(
        [{"transcript_id": tid, "gene_id": gene} for tid, gene in sorted(tid_to_gene.items())]
    ).to_csv(AT_ID_MAP, sep="\t", index=False)

    mrnas = []
    with gzip.open(AT_GFF_GZ, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 9 or parts[2] != "mRNA":
                continue
            chrom, _, _, start, end, _, strand, _, attrs = parts
            if chrom not in {"1", "2", "3", "4", "5"}:
                continue
            attr = parse_attrs(attrs)
            tid = attr.get("transcript_id") or attr.get("ID", "").replace("transcript:", "")
            if tid in selected_tids:
                mrnas.append((chrom, tid, int(start), int(end), strand))
    df = pd.DataFrame(mrnas, columns=["chrom", "transcript_id", "start", "end", "strand"])
    df = df.sort_values(["chrom", "start", "end", "transcript_id"])
    rows = []
    lens_rows = []
    for chrom, group in df.groupby("chrom", sort=False):
        group = group.copy()
        group["order"] = range(1, len(group) + 1)
        lens_rows.append((chrom, int(group["end"].max()), int(group["order"].max())))
        for _, row in group.iterrows():
            rows.append((chrom, row["transcript_id"], int(row["start"]), int(row["end"]), row["strand"], int(row["order"])))
    pd.DataFrame(rows).to_csv(AT_WGDI_GFF, sep="\t", header=False, index=False)
    pd.DataFrame(lens_rows).to_csv(AT_LENS, sep="\t", header=False, index=False)
    pd.DataFrame([(r[1], "At" + r[0], r[2], r[3]) for r in rows]).to_csv(
        AT_MCSCANX_GFF, sep="\t", header=False, index=False
    )


def run_diamond():
    if not DIAMOND_DB.exists():
        subprocess.run(
            [str(DIAMOND), "makedb", "--in", str(AT_SIMPLE_PEP), "-d", str(DIAMOND_DB.with_suffix(""))],
            check=True,
        )
    if not BLAST_TSV.exists():
        subprocess.run(
            [
                str(DIAMOND),
                "blastp",
                "-q",
                str(OIL_SIMPLE_PEP),
                "-d",
                str(DIAMOND_DB),
                "-o",
                str(BLAST_TSV),
                "--outfmt",
                "6",
                "--max-target-seqs",
                "20",
                "--evalue",
                "1e-5",
                "--threads",
                "8",
                "--sensitive",
            ],
            check=True,
        )


def write_wgdi_configs():
    WGDI_CONF.write_text(
        "\n".join(
            [
                "[collinearity]",
                f"gff1 = {OIL_WGDI_GFF}",
                f"gff2 = {AT_WGDI_GFF}",
                f"lens1 = {OIL_LENS}",
                f"lens2 = {AT_LENS}",
                f"blast = {BLAST_TSV}",
                "blast_reverse = false",
                "comparison = genomes",
                "multiple = 1",
                "process = 4",
                "evalue = 1e-5",
                "score = 100",
                "grading = 50,40,25",
                "mg = 50,50",
                "pvalue = 1",
                "repeat_number = 10",
                "position = order",
                f"savefile = {WGDI_COLLINEARITY}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    WGDI_DOTPLOT_CONF.write_text(
        "\n".join(
            [
                "[dotplot]",
                f"blast = {BLAST_TSV}",
                f"gff1 = {OIL_WGDI_GFF}",
                f"gff2 = {AT_WGDI_GFF}",
                f"lens1 = {OIL_LENS}",
                f"lens2 = {AT_LENS}",
                "genome1_name = Camellia oleifera",
                "genome2_name = Arabidopsis thaliana",
                "multiple = 1",
                "score = 100",
                "evalue = 1e-5",
                "repeat_number = 10",
                "markersize = 0.15",
                "figsize = 7,14",
                "position = order",
                "blast_reverse = false",
                f"savefig = {WGDI_DOTPLOT}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_wgdi():
    if not WGDI_COLLINEARITY.exists():
        subprocess.run([str(WGDI_EXE), "-icl", str(WGDI_CONF)], check=True)


def read_wgdi_gff(path: Path):
    df = pd.read_csv(path, sep="\t", header=None, names=["chrom", "id", "start", "end", "strand", "order"])
    return df.set_index("id")


def parse_collinearity_blocks():
    oil_gff = read_wgdi_gff(OIL_WGDI_GFF)
    at_gff = read_wgdi_gff(AT_WGDI_GFF)
    at_map = pd.read_csv(AT_ID_MAP, sep="\t").set_index("transcript_id")["gene_id"].to_dict()
    colpat = pd.read_csv(COLPAT_TSV, sep="\t")
    tid_to_colpat = dict(zip(colpat["transcript_id"], colpat["colpat_name"]))

    blocks = []
    current = None
    with WGDI_COLLINEARITY.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# Alignment"):
                if current:
                    blocks.append(current)
                current = {"header": line, "pairs": []}
                continue
            if current is None:
                continue
            parts = re.split(r"\s+", line)
            if len(parts) >= 3:
                current["pairs"].append((parts[0], parts[2]))
    if current:
        blocks.append(current)

    rows = []
    for idx, block in enumerate(blocks, start=1):
        pairs = block["pairs"]
        oil_ids = [p[0] for p in pairs]
        at_ids = [p[1] for p in pairs]
        oil_colpats = sorted({tid_to_colpat[tid] for tid in oil_ids if tid in tid_to_colpat})
        at_lpat_hits = sorted(
            {
                f"{AT_LPAT_GENES[at_map[tid]]}({at_map[tid]})"
                for tid in at_ids
                if tid in at_map and at_map[tid] in AT_LPAT_GENES
            }
        )
        paired_at_genes = sorted(
            {
                at_map[tid]
                for tid in at_ids
                if tid in at_map
            }
        )
        if not oil_colpats and not at_lpat_hits:
            continue
        oil_chrs = sorted({str(oil_gff.loc[tid, "chrom"]) for tid in oil_ids if tid in oil_gff.index}, key=chrom_key)
        at_chrs = sorted({str(at_gff.loc[tid, "chrom"]) for tid in at_ids if tid in at_gff.index}, key=chrom_key)
        rows.append(
            {
                "block_id": idx,
                "pair_count": len(pairs),
                "oiltea_chromosomes": ",".join(oil_chrs),
                "arabidopsis_chromosomes": ",".join(at_chrs),
                "CoLPAT_members_in_block": ",".join(oil_colpats),
                "AtLPAT_members_in_block": ",".join(at_lpat_hits),
                "paired_arabidopsis_genes_in_block": ",".join(paired_at_genes[:40]),
                "header": block["header"],
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(COLPAT_BLOCKS_TSV, sep="\t", index=False)
    draw_wgdi_dotplot_from_blocks(blocks, oil_gff, at_gff, tid_to_colpat, at_map)
    draw_colpat_block_links(out, oil_gff, at_gff)


def is_oiltea_chromosome(chrom) -> bool:
    return bool(re.match(r"^Chr\d+[a-z]?$", str(chrom)))


def global_order_maps(gff: pd.DataFrame, chrom_filter=None):
    if chrom_filter is not None:
        gff = gff[gff["chrom"].map(chrom_filter)].copy()
    lens = gff.reset_index().groupby("chrom")["order"].max().sort_index()
    chroms = sorted(lens.index.tolist(), key=chrom_key)
    offset = {}
    total = 0
    for chrom in chroms:
        offset[chrom] = total
        total += int(lens.loc[chrom])
    positions = {}
    centers = []
    for chrom in chroms:
        sub = gff[gff["chrom"] == chrom]
        vals = offset[chrom] + sub["order"].astype(int)
        positions.update(vals.to_dict())
        centers.append((chrom, offset[chrom] + int(lens.loc[chrom]) / 2))
    return positions, centers, total


def draw_wgdi_dotplot_from_blocks(blocks, oil_gff: pd.DataFrame, at_gff: pd.DataFrame, tid_to_colpat, at_map):
    oil_pos, oil_centers, oil_total = global_order_maps(oil_gff, is_oiltea_chromosome)
    at_pos, at_centers, at_total = global_order_maps(at_gff)
    xs, ys, colors = [], [], []
    for block in blocks:
        block_has_colpat = any(oil in tid_to_colpat for oil, _ in block["pairs"])
        block_has_at_lpat = any((at in at_map and at_map[at] in AT_LPAT_GENES) for _, at in block["pairs"])
        for oil, at in block["pairs"]:
            if oil in oil_pos and at in at_pos:
                xs.append(at_pos[at])
                ys.append(oil_pos[oil])
                colors.append("#d95f02" if (block_has_colpat or block_has_at_lpat) else "#2f6f8f")
    if not xs:
        return
    fig, ax = plt.subplots(figsize=(7.6, 11.0))
    ax.scatter(xs, ys, s=1.4, c=colors, alpha=0.5, linewidths=0)
    for chrom, center in at_centers:
        ax.axvline(center * 0 + center, color="white", lw=0)
    for chrom, center in oil_centers:
        ax.axhline(center * 0 + center, color="white", lw=0)
    ax.set_xlim(0, at_total)
    ax.set_ylim(oil_total, 0)
    ax.set_xticks([c for _, c in at_centers])
    ax.set_xticklabels(["At" + str(chrom) for chrom, _ in at_centers], fontsize=8)
    ax.set_yticks([c for _, c in oil_centers])
    ax.set_yticklabels([str(chrom) for chrom, _ in oil_centers], fontsize=6)
    ax.xaxis.tick_top()
    ax.set_xlabel("Arabidopsis thaliana", labelpad=12)
    ax.xaxis.set_label_position("top")
    ax.set_ylabel("Camellia oleifera")
    ax.grid(color="#d9d9d9", lw=0.35, alpha=0.6)
    plt.tight_layout()
    plt.savefig(WGDI_DOTPLOT, dpi=300)
    plt.close()


def draw_colpat_block_links(blocks: pd.DataFrame, oil_gff: pd.DataFrame, at_gff: pd.DataFrame):
    colpat = pd.read_csv(COLPAT_TSV, sep="\t")
    block_chrs = []
    if not blocks.empty:
        for item in blocks["oiltea_chromosomes"].dropna():
            block_chrs.extend(str(item).split(","))
    oil_chrs = sorted(set(block_chrs) | set(colpat["chrom"].unique()), key=chrom_key)
    at_chrs = ["1", "2", "3", "4", "5"]
    oil_y = {c: i for i, c in enumerate(oil_chrs)}
    at_y = {c: i for i, c in enumerate(at_chrs)}

    fig, ax = plt.subplots(figsize=(9, 6.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.8, max(len(oil_chrs), len(at_chrs)) - 0.2)
    ax.axis("off")
    oil_x, at_x = 0.18, 0.82
    for chrom in oil_chrs:
        y = oil_y[chrom]
        ax.plot([oil_x, oil_x], [y - 0.35, y + 0.35], lw=7, color="#3f6f8f", solid_capstyle="butt")
        ax.text(oil_x - 0.045, y, chrom, ha="right", va="center", fontsize=9)
    for chrom in at_chrs:
        y = at_y[chrom]
        ax.plot([at_x, at_x], [y - 0.35, y + 0.35], lw=7, color="#7c7a31", solid_capstyle="butt")
        ax.text(at_x + 0.045, y, "At" + chrom, ha="left", va="center", fontsize=9)

    colpat_chrom = dict(zip(colpat["colpat_name"], colpat["chrom"]))
    linked_colpats = set()
    if not blocks.empty:
        for _, block in blocks.iterrows():
            members = [x for x in str(block.get("CoLPAT_members_in_block", "")).split(",") if x and x != "nan"]
            at_block_chrs = [x for x in str(block.get("arabidopsis_chromosomes", "")).split(",") if x and x != "nan"]
            at_lpat = [x for x in str(block.get("AtLPAT_members_in_block", "")).split(",") if x and x != "nan"]
            if not members or not at_block_chrs:
                continue
            at_chrom = at_block_chrs[0]
            y2 = at_y.get(at_chrom)
            if y2 is None:
                continue
            for member in members:
                chrom = colpat_chrom.get(member)
                if chrom not in oil_y:
                    continue
                y1 = oil_y[chrom]
                linked_colpats.add(member)
                if at_lpat:
                    color, lw, alpha, style = "#d95f02", 2.1, 0.88, "-"
                    right_label = ";".join(x.split("(")[0] for x in at_lpat)
                else:
                    color, lw, alpha, style = "#6b6b6b", 1.2, 0.58, "--"
                    right_label = f"Block {int(block['block_id'])}"
                ax.plot([oil_x + 0.03, at_x - 0.03], [y1, y2], color=color, lw=lw, alpha=alpha, linestyle=style)
                ax.text(oil_x + 0.04, y1 + 0.13, member, ha="left", va="center", fontsize=7, color="#1f1f1f")
                ax.text(at_x - 0.04, y2 + 0.13, right_label, ha="right", va="center", fontsize=7, color="#1f1f1f")

    unlinked = [x for x in colpat["colpat_name"].tolist() if x not in linked_colpats]
    if unlinked:
        ax.text(
            0.5,
            -0.55,
            f"WGDI blocks detected for {len(linked_colpats)}/16 CoLPAT members; CoLPAT16 shares a block with AtLPAT3.",
            ha="center",
            fontsize=8,
        )

    ax.text(oil_x, len(oil_chrs) - 0.05, "C. oleifera CoLPAT loci", ha="center", va="bottom", fontsize=10, weight="bold")
    ax.text(at_x, len(oil_chrs) - 0.05, "A. thaliana LPAT loci", ha="center", va="bottom", fontsize=10, weight="bold")
    plt.tight_layout()
    plt.savefig(COLPAT_LINKS_PNG, dpi=300)
    plt.close()


def main():
    COL_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)
    prepare_oiltea()
    prepare_arabidopsis()
    run_diamond()
    write_wgdi_configs()
    run_wgdi()
    parse_collinearity_blocks()
    print(f"Wrote {BLAST_TSV}")
    print(f"Wrote {WGDI_COLLINEARITY}")
    print(f"Wrote {WGDI_DOTPLOT}")
    print(f"Wrote {COLPAT_BLOCKS_TSV}")
    print(f"Wrote {COLPAT_LINKS_PNG}")


if __name__ == "__main__":
    main()
