"""Gerador de dados SINTETICOS no layout da Release 47 (31/35 campos, pipe, sem header).

Serve para testes e CI (os dados reais nao podem ser versionados). Cobre de proposito os ramos que
importam para o target: loans ativos no corte, vintages recentes (janela incompleta), modificados,
default so por evento de credito, outras remocoes, curas, status desconhecido e sujeira estrutural
(linha com campos a menos, linha em branco, loan duplicado, loans sem performance).
"""

from __future__ import annotations

import random
from pathlib import Path

from .freddie_schema import ORIG_COLS, PERF_COLS


def _yyyymm(y: int, m: int) -> str:
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y}{m:02d}"


def make_synthetic(
    out_dir: Path,
    year: int = 2010,
    n_loans: int = 60,
    seed: int = 7,
    dirty: bool = True,
    cutoff: str | None = None,
    orig_only: int = 0,
):
    """Cria sample_orig_{year}.txt e sample_perf_{year}.txt em out_dir/orig e out_dir/perf.

    cutoff: AAAAMM. Series sao truncadas nesse periodo (loans sem ZB = ativos, historico incompleto).
    orig_only: loans extras na originacao sem nenhuma linha de performance.
    """
    rng = random.Random(seed + year)
    (out_dir / "orig").mkdir(parents=True, exist_ok=True)
    (out_dir / "perf").mkdir(parents=True, exist_ok=True)
    orig_lines, perf_lines = [], []
    states = ["CA", "TX", "FL", "NY", "AZ", "NV", "OH"]
    for i in range(n_loans + orig_only):
        has_perf = i < n_loans
        lid = f"F{year % 100:02d}Q1{i:07d}"
        fico = rng.choice([rng.randint(560, 820)] * 9 + [9999])
        ltv = rng.randint(40, 97)
        term = 360
        upb = rng.randrange(80, 450) * 1000
        rate = round(rng.uniform(3.0, 7.5), 3)
        o = {
            "credit_score": str(fico),
            "first_payment_date": _yyyymm(year, 3),
            "first_time_homebuyer_flag": rng.choice(["Y", "N", "9"]),
            "maturity_date": _yyyymm(year, 3 + term - 1),
            "msa": rng.choice(["", "31080", "19100", "35620"]),
            "mi_pct": rng.choice(["0", "0", "25", "30", "999"]),
            "number_of_units": rng.choice(["1", "1", "1", "2", "99"]),
            "occupancy_status": rng.choice(["P", "P", "I", "S", "9"]),
            "cltv": str(min(ltv + rng.randint(0, 10), 998)),
            "dti": rng.choice([str(rng.randint(10, 60)), "999"]),
            "original_upb": str(upb),
            "ltv": str(ltv),
            "original_interest_rate": str(rate),
            "channel": rng.choice(["R", "B", "C", "9"]),
            "prepayment_penalty_flag": "N",
            "amortization_type": "FRM",
            "property_state": rng.choice(states),
            "property_type": rng.choice(["SF", "PU", "CO", "99"]),
            "postal_code": rng.choice(["945", "331", "787", "000"]),
            "loan_id": lid,
            "loan_purpose": rng.choice(["P", "C", "N", "9"]),
            "original_loan_term": str(term),
            "number_of_borrowers": rng.choice(["1", "2", "99"]),
            "seller_name": rng.choice(["OTHER", "BANK ONE", "LENDER X"]),
            "super_conforming_flag": "",
            "pre_harp_loan_id": "",
            "special_eligibility_program": "",
            "harp_indicator": "N",
            "property_valuation_method": rng.choice(["2", "2", "1", "7"]),
            "io_indicator": "N",
            "vantage_score_4": rng.choice([str(fico), "9999"]),
        }
        orig_lines.append("|".join(o[c[0]] for c in ORIG_COLS))
        if not has_perf:
            continue

        bal, status = float(upb), 0
        n_months = rng.randint(6, 60)
        u = rng.random()
        kind = "bad" if u < 0.12 else "ce_only" if u < 0.14 else "other" if u < 0.16 else "good"
        cure_start = (
            n_months // 3 if (kind == "good" and n_months >= 12 and rng.random() < 0.10) else 0
        )
        mod_start = n_months // 2 if (n_months >= 12 and rng.random() < 0.08) else 0
        for k in range(1, n_months + 1):
            period = _yyyymm(year, 3 + k - 1)
            if cutoff and period > cutoff:
                break  # serie truncada no corte dos dados: loan ainda ativo (sem ZB)
            last = k == n_months
            st = 0
            if kind == "bad" and k > n_months // 2:
                status += 1
                st = status
            elif cure_start and cure_start <= k < cure_start + 5:
                st = [1, 2, 3, 2, 1][k - cure_start]  # atinge 90+ e volta a ficar em dia (cura)
            elif kind == "ce_only" and last:
                st = rng.choice([0, 1])  # venda curta / charge-off sem 90+ previo
            status_txt = f"{min(st, 99):02d}" if st < 6 else "RA"
            if not last and rng.random() < 0.01:
                status_txt = "XX"  # status desconhecido
            bal = max(bal - upb / 360 * (1 + rate / 100), 0)
            p = {c[0]: "" for c in PERF_COLS}
            p.update(
                loan_id=lid,
                monthly_reporting_period=period,
                current_actual_upb=f"{bal:.2f}",
                current_loan_delinquency_status=status_txt,
                loan_age=str(k),
                remaining_months_to_legal_maturity=str(term - k),
                current_interest_rate=str(rate),
                current_interest_bearing_upb=f"{bal:.2f}",
                servicer_name="OTHER",
                estimated_ltv=rng.choice([str(ltv), "999"]),
                modification_flag="Y"
                if (mod_start and k == mod_start)
                else ("P" if mod_start and k > mod_start else ""),
            )
            if last:
                zb = {
                    "bad": rng.choice(["02", "03", "09"]),
                    "ce_only": "03",
                    "other": rng.choice(["16", "96"]),
                }.get(kind, "01")
                p.update(
                    current_actual_upb="0.00",
                    current_interest_bearing_upb="0.00",
                    zero_balance_code=zb,
                    zero_balance_effective_date=period,
                    zero_balance_removal_upb=f"{bal:.2f}",
                )
                if zb in ("02", "03", "09"):
                    loss = round(bal * rng.uniform(0.0, 0.6), 2)
                    p.update(
                        net_sales_proceeds=f"{-(bal - loss):.2f}",
                        total_expenses=f"{rng.uniform(500, 9000):.2f}",
                        actual_loss=f"{loss:.2f}",
                    )
            perf_lines.append("|".join(p[c[0]] for c in PERF_COLS))

    if dirty:
        orig_lines.append("|".join(orig_lines[0].split("|")[:30]))  # linha com campo a menos
        orig_lines.append(orig_lines[1])  # loan duplicado
        perf_lines.append("")  # linha em branco
        perf_lines.append("|".join(perf_lines[0].split("|")[:34]))  # linha com campo a menos

    (out_dir / "orig" / f"sample_orig_{year}.txt").write_text(
        "\n".join(orig_lines) + "\n", encoding="utf-8"
    )
    (out_dir / "perf" / f"sample_perf_{year}.txt").write_text(
        "\n".join(perf_lines) + "\n", encoding="utf-8"
    )
