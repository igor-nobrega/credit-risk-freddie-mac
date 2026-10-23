from credit_risk.freddie_schema import ORIG_COLS, PERF_COLS

TYPES = {"str", "int", "double", "yyyymm"}


def test_column_counts():
    assert len(ORIG_COLS) == 32
    assert len(PERF_COLS) == 32


def test_names_unique_and_types_valid():
    for cols in (ORIG_COLS, PERF_COLS):
        names = [c[0] for c in cols]
        assert len(names) == len(set(names))
        assert all(c[1] in TYPES for c in cols)


def test_loan_key_present_in_both():
    assert "loan_sequence_number" in [c[0] for c in ORIG_COLS]
    assert "loan_sequence_number" in [c[0] for c in PERF_COLS]
