from credit_risk.freddie_schema import (
    ORIG_COLS,
    PERF_COLS,
    ZB_WITH_ACTUAL_LOSS,
    ZERO_BALANCE_CODES,
)

TYPES = {"str", "int", "double", "yyyymm"}


def test_column_counts_release_47():
    assert len(ORIG_COLS) == 31
    assert len(PERF_COLS) == 35


def test_names_unique_and_types_valid():
    for cols in (ORIG_COLS, PERF_COLS):
        names = [c[0] for c in cols]
        assert len(names) == len(set(names))
        assert all(c[1] in TYPES for c in cols)


def test_key_and_order_anchors():
    assert ORIG_COLS[0][0] == "credit_score"
    assert ORIG_COLS[19][0] == "loan_id"
    assert PERF_COLS[0][0] == "loan_id"
    assert PERF_COLS[3][0] == "current_loan_delinquency_status"
    assert PERF_COLS[8][0] == "zero_balance_code"
    assert PERF_COLS[21][0] == "actual_loss"


def test_zero_balance_codes():
    assert ZB_WITH_ACTUAL_LOSS <= set(ZERO_BALANCE_CODES)
