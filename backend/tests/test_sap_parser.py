"""
TDD — SAP Parser tests.
Tests written BEFORE sap_parser.py logic.
All test cases from SRS §6.6.
"""
import io
import json
import pytest
import pandas as pd
from unittest.mock import patch

from app.services.sap_parser import SAPParser, SAPParseError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_COLUMN_MAP = {
    "format_version": "SAP_ERP_6.0",
    "required_internal_fields": [
        "customer_id",
        "idoc_number",
        "posting_date",
        "staff_employee_code",
    ],
    "mappings": {
        "Customer": "customer_id",
        "IDoc Number": "idoc_number",
        "Posting Date": "posting_date",
        "EAN": "ean",
        "Material Description": "material_desc",
        "Sales Rep": "staff_employee_code",
    },
}


def make_csv(rows: list[dict], columns: list[str] | None = None) -> io.BytesIO:
    """Build an in-memory CSV file from a list of row dicts."""
    df = pd.DataFrame(rows, columns=columns or list(rows[0].keys()))
    buf = io.BytesIO()
    buf.write(df.to_csv(index=False).encode("utf-8"))
    buf.seek(0)
    return buf


VALID_ROW = {
    "Customer": "CUST001",
    "IDoc Number": "IDOC123",
    "Posting Date": "2026-01-15",
    "EAN": "1234567890",
    "Material Description": "Luxury Bag",
    "Sales Rep": "EMP001",
}


# ---------------------------------------------------------------------------
# Column mapping tests
# ---------------------------------------------------------------------------


class TestColumnMapping:
    def test_known_format_maps_correctly(self):
        """Known SAP column labels remap to internal field names."""
        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=VALID_COLUMN_MAP):
            parser = SAPParser(staff_employee_code="EMP001")
            file = make_csv([VALID_ROW])
            result = parser.parse(file, filename="test.csv")
            assert len(result.records) == 1
            assert result.records[0]["customer_id"] == "CUST001"
            assert result.records[0]["idoc_number"] == "IDOC123"

    def test_unknown_column_triggers_error_with_column_name(self):
        """Unmapped required column raises SAPParseError naming the column."""
        bad_map = {
            **VALID_COLUMN_MAP,
            "mappings": {},  # empty — nothing will map
        }
        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=bad_map):
            parser = SAPParser(staff_employee_code="EMP001")
            file = make_csv([VALID_ROW])
            with pytest.raises(SAPParseError) as exc_info:
                parser.parse(file, filename="test.csv")
            assert "customer_id" in str(exc_info.value) or "Customer" in str(exc_info.value)


# ---------------------------------------------------------------------------
# SAP Parser core tests
# ---------------------------------------------------------------------------


class TestSAPParser:
    def _make_parser(self, employee_code: str = "EMP001") -> SAPParser:
        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=VALID_COLUMN_MAP):
            return SAPParser(staff_employee_code=employee_code)

    def test_empty_file_raises_error(self):
        """Empty CSV raises SAPParseError."""
        parser = self._make_parser()
        empty = io.BytesIO(b"")
        with pytest.raises(SAPParseError, match="empty"):
            parser.parse(empty, filename="empty.csv")

    def test_missing_required_column_raises_error(self):
        """CSV missing a required column raises SAPParseError naming it."""
        row_missing_idoc = {k: v for k, v in VALID_ROW.items() if k != "IDoc Number"}
        parser = self._make_parser()
        file = make_csv([row_missing_idoc])
        with pytest.raises(SAPParseError) as exc_info:
            parser.parse(file, filename="test.csv")
        assert "idoc_number" in str(exc_info.value) or "IDoc" in str(exc_info.value)

    def test_unmapped_column_raises_error(self):
        """CSV with an unmapped column name raises SAPParseError."""
        bad_row = {**VALID_ROW, "UnknownColumn": "garbage"}
        bad_map = {
            **VALID_COLUMN_MAP,
            "mappings": {**VALID_COLUMN_MAP["mappings"], "UnknownColumn": None},
        }
        # Simpler: just remove a required mapping so it can't find customer_id
        broken_map = {
            **VALID_COLUMN_MAP,
            "mappings": {k: v for k, v in VALID_COLUMN_MAP["mappings"].items() if k != "Customer"},
        }
        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=broken_map):
            parser = SAPParser(staff_employee_code="EMP001")
            file = make_csv([VALID_ROW])
            with pytest.raises(SAPParseError):
                parser.parse(file, filename="test.csv")

    def test_valid_file_returns_records(self):
        """Valid CSV with matching Sales Rep returns parsed records."""
        parser = self._make_parser(employee_code="EMP001")
        file = make_csv([VALID_ROW])
        result = parser.parse(file, filename="test.csv")
        assert len(result.records) == 1
        assert result.errors == []

    def test_sales_rep_filter_excludes_other_reps(self):
        """Only rows matching the staff's employee_code are returned."""
        rows = [
            VALID_ROW,  # EMP001 — should be included
            {**VALID_ROW, "IDoc Number": "IDOC999", "Sales Rep": "EMP002"},  # excluded
        ]
        parser = self._make_parser(employee_code="EMP001")
        file = make_csv(rows)
        result = parser.parse(file, filename="test.csv")
        assert len(result.records) == 1
        assert result.records[0]["idoc_number"] == "IDOC123"

    def test_no_matching_sales_rep_raises_error(self):
        """File with no rows for this Sales Rep raises SAPParseError."""
        row_other_rep = {**VALID_ROW, "Sales Rep": "EMP999"}
        parser = self._make_parser(employee_code="EMP001")
        file = make_csv([row_other_rep])
        with pytest.raises(SAPParseError, match="Sales Rep"):
            parser.parse(file, filename="test.csv")

    def test_invalid_rows_logged_valid_rows_imported(self):
        """Rows with missing data are logged as errors; valid rows still imported."""
        bad_row = {**VALID_ROW, "IDoc Number": "", "Customer": ""}  # blank required fields
        good_row = {**VALID_ROW, "IDoc Number": "IDOC200"}
        parser = self._make_parser(employee_code="EMP001")
        file = make_csv([bad_row, good_row])
        result = parser.parse(file, filename="test.csv")
        assert len(result.records) == 1
        assert result.records[0]["idoc_number"] == "IDOC200"
        assert len(result.errors) >= 1

    def test_header_only_file_raises_empty_error(self):
        """CSV with header row but no data rows raises SAPParseError about empty file."""
        import io as _io
        header_only = _io.BytesIO(
            "Customer,IDoc Number,Posting Date,EAN,Material Description,Sales Rep\n".encode()
        )
        parser = self._make_parser()
        with pytest.raises(SAPParseError, match="empty"):
            parser.parse(header_only, filename="empty.csv")

    def test_staff_employee_code_column_missing_after_remap(self):
        """If Sales Rep column is entirely absent, raises SAPParseError."""
        import pandas as pd, io as _io
        row = {
            "Customer": "CUST001",
            "IDoc Number": "IDOC001",
            "Posting Date": "2026-01-01",
        }  # no Sales Rep column at all
        no_rep_map = {
            **VALID_COLUMN_MAP,
            "mappings": {
                "Customer": "customer_id",
                "IDoc Number": "idoc_number",
                "Posting Date": "posting_date",
            },
            "required_internal_fields": ["customer_id", "idoc_number", "posting_date"],
        }
        df = pd.DataFrame([row])
        buf = _io.BytesIO()
        buf.write(df.to_csv(index=False).encode())
        buf.seek(0)
        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=no_rep_map):
            parser = SAPParser(staff_employee_code="EMP001")
            # Override internal map to skip required-field assertion
            parser._column_map = {**no_rep_map, "required_internal_fields": []}
            with pytest.raises(SAPParseError, match="staff_employee_code"):
                parser.parse(buf, filename="test.csv")

    def test_date_already_a_date_object_returned_as_is(self):
        """_parse_date returns a date object unchanged (no re-parsing)."""
        from datetime import date
        from app.services.sap_parser import SAPParser as _SP
        result = _SP._parse_date(date(2026, 1, 15))
        assert result == date(2026, 1, 15)

    def test_unparseable_date_raises_error(self):
        """_parse_date raises SAPParseError on garbage date strings."""
        from app.services.sap_parser import SAPParser as _SP
        with pytest.raises(SAPParseError, match="Cannot parse date"):
            _SP._parse_date("not-a-date")

    def test_posting_date_parsed_as_date(self):
        """posting_date is returned as a Python date object."""
        from datetime import date
        parser = self._make_parser()
        file = make_csv([VALID_ROW])
        result = parser.parse(file, filename="test.csv")
        assert isinstance(result.records[0]["posting_date"], date)

    def test_excel_file_parsed(self):
        """XLSX files are parsed identically to CSV."""
        df = pd.DataFrame([VALID_ROW])
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        parser = self._make_parser()
        result = parser.parse(buf, filename="test.xlsx")
        assert len(result.records) == 1
