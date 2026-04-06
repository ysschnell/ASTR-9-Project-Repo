# How to Use This Catalog

We intend for this catalog to be a flexible resource for the community. Different science cases place different demands on reliability, completeness, and alias handling, and no single set of cuts is optimal for all applications. This section outlines several anticipated use cases and demonstrates how users can construct tailored subsamples using the catalog columns and the accompanying processing script.

## The Catalog Generation Script

We provide a Python script, [`master_validation.py`](https://github.com/awboyle/TARS/blob/main/scripts/master_validation.py), for validating TESS rotation period measurements against external reference samples and generating final rotation period catalogs with user-specified quality cuts. All of the data needed to run this script can be downloaded from Zenodo here: 10.5281/zenodo.18342591. This is the same script we used to generate the default TARS catalog. The script performs two primary functions:

1. **Validation**: Compares TESS rotation period measurements against the same four external catalogs from the paper (Section 5.2) to assess recovery rates and aliasing.
2. **Catalog Generation**: Produces a final catalog of adopted rotation periods using the same logic as in the paper (Section 5.1).

The goal of the script is to allow users to set different probability thresholds and quality cuts than are used in our default catalog, propagate those choices to the same validation sets we used to get estimates for reliability and completeness, and output a rotation catalog based on these different cuts.

The available command-line arguments are listed below. The validation sample files must be present in a `validation_samples/` subdirectory relative to the script location, and the output catalog will contain the same columns as the default TARS catalog.

### Command-Line Arguments

#### Input/Output

- `--input, -i` (default: `tars_table_4.feather`): Input rotation results file
- `--input_format` (default: inferred): Input format — `feather`, `csv`, or `parquet`
- `--output, -o` (default: none): Output catalog file path
- `--output_format` (default: inferred): Output format — `feather`, `csv`, or `parquet`

#### Threshold Settings

- `--sys_threshold, -s` (default: `0.8`): Systematics classifier probability threshold
- `--alias_threshold, -a` (default: `0.8`): Alias classifier probability threshold
- `--test_thresholds` (default: none): Test multiple thresholds (space-separated)

#### Quality Flags

- `--apply_quality_flags, -q` (default: `False`): Apply all quality flag cuts
- `--no_quality_flags` (default: `False`): Disable all quality flag cuts
- `--require_consistent_periods` (default: `False`): Require consistent periods across sectors
- `--require_multiple_sectors` (default: `False`): Require >1 sector observations
- `--require_no_binaries` (default: `False`): Exclude potential binaries
- `--require_no_contaminants` (default: `False`): Exclude contaminated sources

#### Alias Handling

- `--alias_handling` (default: `double`): How to handle aliases — `double`, `remove`, `none`, or `skip`

#### Execution Options

- `--skip_validation` (default: `False`): Skip validation, only generate catalog
- `--validation_only` (default: `False`): Only run validation tests
- `--n_workers, -n` (default: `1`): Number of parallel workers (`-1` for all CPUs)
- `--chunksize` (default: `5000`): Chunk size for parallel processing

---

## Use Cases

We frame several anticipated use cases in the form of a question and answer below.

---

***Q: I would like to use only your highest-quality rotation periods. How can I select these?***

**A:**
If you would like to start from our default catalog, you can apply all quality flags mentioned in the catalog column descriptions and require that the period was observed in multiple sectors.

Alternatively, you can start from the full TARS catalog and create your own final catalog with higher systematics and alias classifier cutoffs. For applications requiring maximal reliability, we recommend thresholds of 0.9 for both classifiers. This selection corresponds to the most conservative rows in the validation statistics table, where match fractions exceed 90-95% across all validation samples.

```bash
python master_validation.py \
    --input rotations_results.feather \
    --rf_threshold 0.9 \
    --alias_threshold 0.9 \
    --apply_quality_flags \
    --output final_catalog.feather
```

This command selects measurements with a systematics-classifier probability >0.9, requires alias-classifier probabilities >0.9 (either true period or alias), applies all quality flags, and adopts final rotation periods following the period adoption logic described in the paper. The resulting catalog is optimized for purity rather than size.

---

***Q: How can I construct a more complete rotation catalog?***

**A:**
To prioritize completeness, we recommend retaining a systematics-classifier threshold of ~0.8 while relaxing the alias-classifier threshold to 0.5. This ensures that retained signals are genuine periodic variability while accepting a higher level of alias contamination.

```bash
python master_validation.py \
    --input rotations_results.feather \
    --rf_threshold 0.8 \
    --alias_threshold 0.5 \
    --output final_catalog.feather
```

In this configuration, true rotation signals are efficiently retained, but some fraction (~10-15%) of periods may be doubled relative to the true rotation period. This mode is well suited for population-level studies where statistical trends matter more than per-star accuracy and yields ~1-1.5 million rotation periods.

---

***Q: I only trust periods measured in more than one TESS sector. How do I select those?***

**A:**
Use the catalog-level quality flags. Specifically, require that the number of contributing sectors exceeds one and that there is no evidence for inconsistent sector-level periods:

```bash
python master_validation.py \
    --input rotations_results.feather \
    --require_multiple_sectors \
    --require_consistent_periods \
    --output catalog.feather
```

Only the specified flags will be applied; the other quality flags (binaries, contaminants) will not be enforced. This ensures that the adopted period is supported by repeated, consistent detections across independent TESS sectors. Or, when using our default catalog, select measurements with `n_secs > 1` and `flag_multiple_periods == False`. This will require that the resulting periods were seen in multiple sectors and that the measurements across each sector are consistent with each other.

---

***Q: How can I select a set of stars with as little aliasing as possible?***

**A:**
The catalog-generation script supports multiple strategies for handling half-period aliases via the `--alias_handling` option:

- **`double`** (default): Correct aliases by doubling periods classified as P_rot/2
- **`remove`**: Remove alias-classified measurements entirely, keeping only periods with high probability of being the true rotation period
- **`none`**: Apply no alias correction; leave measured periods as-is
- **`skip`**: Bypass the alias classifier entirely (no second-stage filtering)

```bash
# (Default) Correct aliases by doubling them
python master_validation.py \
    --input rotations_results.feather \
    --rf_threshold 0.9 \
    --alias_threshold 0.9 \
    --apply_quality_flags \
    --alias_handling double \
    --output final_catalog.feather
```

```bash
# Remove alias-classified measurements instead of doubling
python master_validation.py \
    --input rotations_results.feather \
    --rf_threshold 0.9 \
    --alias_threshold 0.9 \
    --apply_quality_flags \
    --alias_handling remove \
    --output final_catalog_no_aliases.feather
```

```bash
# No alias correction (leave measured periods as-is)
python master_validation.py \
    --input rotations_results.feather \
    --rf_threshold 0.9 \
    --alias_threshold 0.9 \
    --apply_quality_flags \
    --alias_handling none \
    --output final_catalog_uncorrected.feather
```

In practice, `double` maximizes completeness at longer periods but can introduce a small population of incorrectly doubled periods (see the paper for details). The `remove` option yields a cleaner sample with minimal alias contamination, but it preferentially removes stars whose dominant signal is at P_rot/2 and therefore reduces completeness at longer periods. The `none` option is useful if you want to handle aliases yourself downstream, but it will retain half-period aliases in the catalog. The `skip` option bypasses the alias classifier entirely, performing no second-stage filtering at all.

---

***Q: How can I remove non-rotational variability from the catalog?***

**A:**
Most non-rotational variability in TARS occurs above the Kraft break, at (G_BP - G_RP)_0 < ~0.55 or T_eff > ~6700 K. Restricting the sample to cooler or redder stars efficiently removes most delta Scuti and gamma Doradus variables while preserving genuine rotation signals.

---

***Q: Is there a way to identify which periods were doubled?***

**A:**
Yes. The boolean column `flag_doubled_period` is set to `True` if any sector-level measurement contributing to the adopted period was doubled during alias correction. Users may retain or exclude these stars depending on whether completeness or reliability is prioritized.

---

***Q: How can I quickly test different threshold values?***

**A:**
Use the `--test_thresholds` option to compare validation results across multiple probability thresholds without generating a full catalog:

```bash
python master_validation.py \
    --validation_only \
    --test_thresholds 0.5 0.6 0.7 0.8 0.9 \
    --apply_quality_flags
```

This will output validation statistics for each threshold, allowing you to assess the trade-off between completeness and reliability before committing to a particular selection.

---

***Q: How can I speed up catalog generation for large datasets?***

**A:**
Use the `--n_workers` option to enable parallel processing:

```bash
python master_validation.py \
    --input rotations_results.feather \
    --n_workers -1 \
    --apply_quality_flags \
    --output final_catalog.feather
```

The `-1` value automatically uses all available CPU cores. You can also specify a specific number of workers (e.g., `--n_workers 8`).

---

In summary, the TARS catalog is intentionally not prescriptive. The default configuration provides a balanced catalog suitable for broad use, while the accompanying probabilities and quality flags allow users to explicitly tune the balance between completeness, reliability, and alias handling to meet the needs of their specific science applications.
