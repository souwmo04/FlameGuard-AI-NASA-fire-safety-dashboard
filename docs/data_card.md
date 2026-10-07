# Data Card — FLEX (PSI-69)

## Source

| | |
|---|---|
| Program | FLEX — Flame Extinguishment Experiment |
| Platform | International Space Station, Multi-User Droplet Combustion Apparatus (MDCA) in the Combustion Integrated Rack (CIR) |
| Repository | NASA Physical Sciences Informatics (PSI), investigation **PSI-69** — https://psi.nasa.gov/physci/repo/data/investigations/PSI-69 |
| DOI | https://doi.org/10.60555/mbq8-0451 (must be cited — PSI requirement) |
| License | CC0-1.0 |
| Reference report | Dietrich, D.L. et al., *Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011*, NASA/TP-2015-216046 (2015). https://ntrs.nasa.gov/citations/20150023456 — local copy in `documents/flex/` |
| Raw file | `data/raw/flex/PSI-69_Experimental table_FLEX.csv` (24,776 bytes; checksum in `MANIFEST.json`) |

The PSI CSV reproduces the per-test results table of NASA/TP-2015-216046
(column definitions: report Appendix A.1). Test dates span 2009-03-05 to 2011-12-08.

## Experimental design (from PSI-69 metadata and the report)

- Free-floating or fiber-supported single fuel droplets, ignited by hot wires, burning in a
  nominally **quiescent** chamber atmosphere at ambient temperature.
- Goal: find the **limiting oxygen index (LOI)** versus pressure and suppressant (diluent).
- Tests were chosen **adaptively**: operators stepped oxygen down / diluent up and droplet
  size up until burning was no longer sustained. Data is therefore dense near the
  extinction boundary; class balance reflects test selection, not real-world frequency.

## Shape

274 rows × 15 columns; one row = one droplet test.

| Outcome (`Test end`) | Methanol | Heptane | Total |
|---|---|---|---|
| Extinction | 126 | 60 | 186 |
| Disruption | 23 | 38 | 61 |
| Completion | 8 | 19 | 27 |

Outcome definitions (report Appendix A.1):
- **Extinction** — visible flame extinguished at a finite droplet diameter.
- **Completion** — droplet burned to completion (no extinction).
- **Disruption** — droplet disruption ended the test before extinction.

## Columns

| Raw header | Meaning | Unit | Notes |
|---|---|---|---|
| `FLEX Test #` | Science-team test number | – | 1–274 |
| `FLEX Identifier` | CIR engineering test identifier | – | Encodes atmosphere series/setpoint, e.g. `C10M101` = CO₂ series, setpoint 10, Methanol, droplet 1, attempt 01 |
| `Test Date`, `Test GMT` | When the test ran | date, GMT | 1 missing GMT |
| `Fuel` | Methanol or n-heptane | – | |
| `Ambient pressure; mmHg` | Absolute chamber pressure | mmHg | ~0.7 atm (103), ~1 atm (161), ~3 atm (9); **one invalid 0.0** |
| `O initial ambient composition; mole fraction` | **O₂** mole fraction | – | subscript lost in header; 0.12–0.34 |
| `N initial ambient composition; mole fraction` | **N₂** mole fraction | – | |
| `CO initial ambient composition; mole fraction` | **CO₂** mole fraction | – | 0–0.70 (suppressant/diluent) |
| `He initial ambient composition; mole fraction` | **He** mole fraction | – | 0–0.45 (suppressant/diluent) |
| `Droplet initial diameter; mm` | Initial droplet diameter d₀ | mm | 1.1–4.7; some missing |
| `Visible flame extinction diameter; mm` | Droplet diameter at extinction | mm | **post-outcome — never a model feature** (missing exactly when no extinction) |
| `Burning rate; mm` | Burning-rate constant (d² vs t slope) | **mm²/s** | header unit is wrong; post-outcome |
| `Burn time; s` | Flame duration | s | post-outcome; some values approximate (`~6`) |
| `Test end` | Outcome | – | Extinction / Disruption / Completion |

## Variables NOT in this dataset

No airflow velocity (quiescent chamber), no ambient temperature, no solid materials,
no SF₆ (mentioned in FLEX objectives but not in this table), no support-fiber flag
(present in the report's table, not the CSV).

## Known quality issues (to handle in cleaning, never by editing raw files)

1. File encoding is cp1252/latin-1; missing values appear as an en dash (`\x96`).
2. Approximate values written with `~` (e.g. `~6`).
3. Test 114 (`C11M201`) has pressure `0.0` — invalid record, not vacuum.
4. Identifier `193F001` appears twice (tests 70 and 73).
5. Mole fractions sum to 0.98–1.01 (rounding).
6. Header subscripts lost (`O`→O₂, `CO`→CO₂, `N`→N₂); burning-rate unit mislabelled.
7. **Fuel contamination (reported by NASA).** In these tests the fuel needles carried a conformal coating that
   dissolved or flaked into the droplets. NASA judges burning rates and flame histories minimally affected, but
   methanol disruptions "probably due to the presence of the contaminant"; for heptane disruptions it draws no
   conclusion (NASA/TP-2015-216046, §5.2, pp. 16–17). Not correctable from the data; see the model card,
   limitation 6.
8. Figure captions in the report occasionally disagree with the tabulated data (e.g. FLEX-094: caption
   0.27/0.56/0.20 O₂/N₂/CO₂, which sums to 1.03; table and dataset 0.24/0.56/0.20). The dataset values are used.

## Cleaning (Phase 3) — `data/processed/combustion_master.csv`

Built by `python scripts/build_master.py` (code: `src/flameguard/preprocessing.py`,
schema: `src/flameguard/schema.py`, tests: `tests/test_preprocessing.py`).
Counts below are from `data/processed/qc_summary.json`.

**Rules**
- No value is invented, imputed or renormalised. Missing or invalid source values stay `NaN`.
- No row is dropped. Anomalies are recorded in the semicolon-separated `qc_flags` column
  (definitions in `schema.QC_FLAGS`); exclusion decisions are made, and documented, at
  modelling time.
- Unknown tokens, outcome labels, fuels or identifier patterns raise an error instead of
  being guessed.

**Decisions**

| Item | Decision |
|---|---|
| Target `y_sustained` | 1 = Completion or Disruption (flame had not self-extinguished while fuel remained), 0 = Extinction. 88 vs 186. |
| `diluent` | `He` if x_He > 0, `CO2` if x_CO2 > 0, else `N2` (no test has both). CO2 123, N2 101, He 50. |
| `p_o2_atm` | x_O2 × pressure_atm. |
| Test 114 pressure 0.0 | Set to missing; `pressure_level` (0.7 atm) taken from its chamber-fill siblings for validation grouping only. |
| `pressure_level` | Bands `0.7atm` (104), `1atm` (161), `2-3atm` (9). The high-pressure tests span 2.03–3.05 atm within one CO2-diluted series, so they are not given a nominal value. |
| Tests 70 & 73 | Same identifier and GMT time in the NASA report itself, but described as separate tests (both with fuel-dispensing anomalies). Kept, flagged `duplicate_identifier`. |
| Dates | Source mixes `3/5/2009` and `10/24/09`; both parsed explicitly. Stored as ISO 8601 GMT. |
| `flow_cm_s` | Missing for every FLEX row (quiescent chamber, not recorded); never 0. |
| `d_ext_mm` on non-extinction tests | Present for 38 Completion/Disruption tests in the NASA table; kept and flagged. Post-outcome, never a feature. |

**Validation groups** (for grouped cross-validation; never model inputs)
- `group_id_fill`: chamber-atmosphere setpoint decoded from the identifier (`C10`, `H05`, `TP193`, `CAL`) — 79 groups.
- `group_id_atmosphere`: pressure band + O2/CO2/He mole fractions — 45 groups (1–29 tests each).
  More conservative: no atmosphere ever appears in both training and test folds.

**Remaining missing values**: `d0_mm` 12, `pressure_atm` 1, `burn_rate_mm2_s` 16,
`burn_time_s` 6, `d_ext_mm` 77.
