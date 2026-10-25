# ENIGH downloads for historical age comparisons

These files prepare a comparison of households headed by people of the same age
in 1994, 2004, 2014, and 2024. They are downloaded source data, not harmonized
estimates or evidence of a generational effect.

## Acquisition contract

- Scope: official INEGI ENIGH microdata and associated database documentation for
  the four years below. Repository baseline: `394ab5b6f0690e6bf1f192a9089e98aff564facf`.
- Preserve the original downloaded files and extract their contents without
  converting formats or changing values. No routes or user interface are involved.
- Leave the analysis code, existing tables, figures, bibliography, and README unchanged.
- Authorized changes: local source files, their provenance manifest, this note,
  a raw-data ignore rule, and a reviewed local Git commit. No remote publication.

## Files and editions

| Year | INEGI edition | Microdata archives | Format |
|---|---|---:|---|
| 1994 | Tradicional | 6 | DBF |
| 2004 | Tradicional, demographic reconciliation with the 2005 population count | 6 | DBF |
| 2014 | Nueva construccion | 12 | CSV |
| 2024 | Nueva serie | 17 | CSV |

All tables offered in the official microdata inventories were downloaded once,
choosing CSV where available and DBF for the two older waves. Nine associated
documentation downloads include database descriptions, variable construction,
the 2014 dictionary errata, and the 2000-2005 demographic harmonization note.

- [1994 official source](https://www.inegi.org.mx/programas/enigh/tradicional/1994/)
- [2004 official source](https://www.inegi.org.mx/programas/enigh/tradicional/2004/)
- [2014 official source](https://www.inegi.org.mx/programas/enigh/nc/2014/)
- [2024 official source](https://www.inegi.org.mx/programas/enigh/nc/2024/)

Local layout, relative to the repository root:

```text
data/enigh_downloads.csv                 # tracked provenance manifest
data/raw/enigh/<year>/microdata/         # original ZIPs and extracted directories
data/raw/enigh/<year>/documentation/     # original documents and extracted PDF ZIP
data/raw/enigh/<year>/metadata/          # official download-inventory snapshot
```

`enigh_downloads.csv` records each exact source URL, edition, title, local path,
retrieval time in UTC, byte size, SHA-256, archive file count, uncompressed size,
and extraction destination. The hashes are calculated locally, not published
INEGI checksums. Archive contents were checked with ZIP CRC verification before
extraction; standalone documentation was checked for a PDF signature.

Raw files and extracted contents are excluded from Git. A clone contains this
note and the manifest; it does not contain the downloaded data. To repeat a
download, use its manifest `url` and save it to its repository-relative `path`,
then compare its SHA-256 and inspect any source revision before replacing it.

## Revision and comparability notes

- INEGI's 1994 and 2004 microdata tabs report that `concen` and the file descriptor
  were replaced on 2024-08-30 to add `EST_DIS` and `UPM` for precision estimates.
- The 2004 microdata use revised demographic weights. INEGI identifies the
  comparable 2000-2005 tabulations on its 2005 page; the original 2004 tabulations
  do not describe these revised files.
- The 2014 page reports expenditure/financing corrections dated 2015-09-17 and
  suppression of `AGEB` and `UBICA_GEO` values dated 2018-10-17. The downloaded
  database description has a separate errata document dated 2019-12-13.
- The selected 2014 edition is Nueva construccion. The 2024 edition is Nueva
  serie. Their expenditure definitions and codes still require harmonization.
- No historical D2 basket, age profile, standard error, or generational comparison
  has been calculated. The existing analysis loader still expects its original
  nested 2024 input layout; these downloads do not change that configuration.

The raw-data inventory snapshots preserve the advertised file titles and formats.
They do not establish statistical comparability across waves.
