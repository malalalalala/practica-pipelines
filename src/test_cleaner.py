from cleaner import clean_orders

HEADER = "order_id,marketplace,status,amount,updated_at\n"


def write_csv(tmp_path, lines):
    """Crea un CSV temporal con las filas dadas y devuelve su ruta."""
    path = tmp_path / "orders.csv"
    path.write_text(HEADER + "".join(line + "\n" for line in lines), encoding="utf-8")
    return str(path)


def test_keeps_most_recent_version_of_order(tmp_path):
    path = write_csv(tmp_path, [
        "A1,MX,PENDING,100,2026-01-01T10:00:00",
        "A1,MX,SHIPPED,100,2026-01-02T10:00:00",
    ])

    valid, quarantine, summary = clean_orders(path)

    assert len(valid) == 1
    assert valid[0]["status"] == "SHIPPED"


def test_tie_on_date_last_row_wins(tmp_path):
    path = write_csv(tmp_path, [
        "Z1,MX,PRIMERA,10,2026-01-01T10:00:00",
        "Z1,MX,SEGUNDA,10,2026-01-01T10:00:00",
    ])

    valid, _, _ = clean_orders(path)

    assert len(valid) == 1
    assert valid[0]["status"] == "SEGUNDA"


def test_invalid_rows_go_to_quarantine_with_reason(tmp_path):
    path = write_csv(tmp_path, [
        ",MX,SHIPPED,20,2026-01-01T09:00:00",
        "C3,CO,SHIPPED,abc,2026-01-01T09:00:00",
        "D4,MX,SHIPPED,-5,2026-01-01T09:00:00",
        "E5,BR,SHIPPED,30,no-es-fecha",
    ])

    valid, quarantine, _ = clean_orders(path)

    assert valid == []
    assert sorted(row["reason"] for row in quarantine) == sorted([
        "order_id vacío",
        "amount no es numero",
        "amount negativo",
        "updated_at no es una fecha válida",
    ])


def test_totals_by_marketplace(tmp_path):
    path = write_csv(tmp_path, [
        "A1,MX,PENDING,100,2026-01-01T10:00:00",
        "A1,MX,SHIPPED,100,2026-01-02T10:00:00",
        "B2,BR,SHIPPED,50.5,2026-01-01T09:00:00",
        "F6,MX,SHIPPED,30,2026-01-03T09:00:00",
    ])

    _, _, summary = clean_orders(path)

    assert summary["total_by_marketplace"] == {"MX": 130.0, "BR": 50.5}
    assert summary["orders_by_status"] == {"SHIPPED": 3}


def test_empty_file_does_not_break(tmp_path):
    path = write_csv(tmp_path, [])   # solo el encabezado

    valid, quarantine, summary = clean_orders(path)

    assert valid == []
    assert quarantine == []
    assert summary == {"total_by_marketplace": {}, "orders_by_status": {}}


def test_running_twice_gives_same_result(tmp_path):
    path = write_csv(tmp_path, [
        "A1,MX,PENDING,100,2026-01-01T10:00:00",
        "A1,MX,SHIPPED,100,2026-01-02T10:00:00",
        ",MX,SHIPPED,20,2026-01-01T09:00:00",
    ])

    first = clean_orders(path)
    second = clean_orders(path)

    assert first == second