# 01 Data Quality Report

- Gate status: PASS
- Price source: `/home/tato/proyectos/MPC_Conexar/historico_merval.db` / `historico_diario`
- FX source: `/home/tato/proyectos/MPC_Conexar/historico_merval.db` / `ccl_diario` (ccl_proxy_for_mep)
- Base overlap window: `2021-03-29` → `2026-07-10`
- Curated panel: `/home/tato/shared/estrategia/202060711_Momentung_pull_back_argentina/data/processed/t267_argentina_panel.csv`
- Tradable universe by scale: `/home/tato/shared/estrategia/202060711_Momentung_pull_back_argentina/data/processed/t267_argentina_tradable_by_scale.csv`
- JSON summary: `/home/tato/shared/estrategia/202060711_Momentung_pull_back_argentina/data/quality_reports/t267_data_quality_summary.json`

## Critical failures
- none

## Warnings
- No dedicated historical MEP table found; using ccl_diario as the current canonical USD conversion proxy.
- Zero-volume rows detected: 36
- ALUA: 5 invalid OHLC row(s) tolerated
- BYMA: 3 invalid OHLC row(s) tolerated
- CEPU: 3 invalid OHLC row(s) tolerated
- GGAL: 3 invalid OHLC row(s) tolerated
- PAMP: 3 invalid OHLC row(s) tolerated
- TGSU2: 4 invalid OHLC row(s) tolerated
- TXAR: 4 invalid OHLC row(s) tolerated
- YPFD: 4 invalid OHLC row(s) tolerated

## Included tickers
ALUA, BYMA, CEPU, GGAL, PAMP, TGSU2, TXAR, YPFD

## Excluded tickers
| Ticker | Reasons | Missing dates | Missing date sample | Invalid dates |
| --- | --- | --- | --- | --- |
| BBAR | invalid_ohlc_on_2022-05-13; invalid_ohlc_on_2022-05-16; invalid_ohlc_on_2024-12-24; invalid_ohlc_on_2025-07-31; invalid_ohlc_on_2026-03-09; invalid_ohlc_on_2026-07-08; invalid_ohlc_on_2026-07-10 | 0 |  | 2022-05-13, 2022-05-16, 2024-12-24, 2025-07-31, 2026-03-09 (+2 more) |
| BMA | invalid_ohlc_on_2022-05-13; invalid_ohlc_on_2022-05-16; invalid_ohlc_on_2024-08-09; invalid_ohlc_on_2025-02-04; invalid_ohlc_on_2026-04-10; invalid_ohlc_on_2026-05-19 | 0 |  | 2022-05-13, 2022-05-16, 2024-08-09, 2025-02-04, 2026-04-10 (+1 more) |

## Deliverables
- Curated panel rows: `10310`
- Tradable rows: `30930`
- Universe precalculated by scale: `['ALUA', 'BYMA', 'CEPU', 'GGAL', 'PAMP', 'TGSU2', 'TXAR', 'YPFD']`
