"""
TDD — Column mapping config tests.
Verifies that sap_column_map.json is loaded, applied, and fails gracefully.
"""
import json
import io
import pytest
from unittest.mock import patch, mock_open

from app.services.sap_parser import SAPParser, SAPParseError


FULL_MAP = {
    "format_version": "SAP_ERP_6.0",
    "required_internal_fields": [
        "customer_id",
        "idoc_number",
        "posting_date",
        "staff_employee_code",
    ],
    "mappings": {
        "Customer": "customer_id",
        "Cust_ID": "customer_id",
        "CustomerNo": "customer_id",
        "IDoc Number": "idoc_number",
        "Posting Date": "posting_date",
        "EAN": "ean",
        "Material Description": "material_desc",
        "Sales Rep": "staff_employee_code",
    },
}


def _csv(headers: list[str], rows: list[list]) -> io.BytesIO:
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(v) for v in row))
    buf = io.BytesIO("\n".join(lines).encode())
    buf.seek(0)
    return buf


class TestColumnMappingConfig:
    def test_alternative_customer_label_maps_correctly(self):
        """'Cust_ID' maps to customer_id the same as 'Customer'."""
        import pandas as pd

        row = {
            "Cust_ID": "CUST002",
            "IDoc Number": "IDOC002",
            "Posting Date": "2026-02-01",
            "EAN": "111",
            "Material Description": "Watch",
            "Sales Rep": "EMP001",
        }
        df = pd.DataFrame([row])
        buf = io.BytesIO()
        buf.write(df.to_csv(index=False).encode())
        buf.seek(0)

        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=FULL_MAP):
            parser = SAPParser(staff_employee_code="EMP001")
            result = parser.parse(buf, filename="test.csv")
        assert result.records[0]["customer_id"] == "CUST002"

    def test_missing_required_field_raises_with_field_name(self):
        """If no mapping produces a required field, error names that field."""
        no_customer_map = {
            **FULL_MAP,
            "mappings": {k: v for k, v in FULL_MAP["mappings"].items()
                         if v != "customer_id"},
        }
        import pandas as pd

        row = {
            "IDoc Number": "IDOC003",
            "Posting Date": "2026-02-01",
            "Sales Rep": "EMP001",
        }
        df = pd.DataFrame([row])
        buf = io.BytesIO()
        buf.write(df.to_csv(index=False).encode())
        buf.seek(0)

        with patch("app.services.sap_parser.SAPParser._load_column_map", return_value=no_customer_map):
            parser = SAPParser(staff_employee_code="EMP001")
            with pytest.raises(SAPParseError) as exc_info:
                parser.parse(buf, filename="test.csv")
        assert "customer_id" in str(exc_info.value)

    def test_config_file_loaded_from_correct_path(self):
        """SAPParser loads sap_column_map.json (not hardcoded values)."""
        map_json = json.dumps(FULL_MAP)
        with patch("builtins.open", mock_open(read_data=map_json)):
            with patch("os.path.exists", return_value=True):
                parser = SAPParser.__new__(SAPParser)
                loaded = parser._load_column_map()
        assert loaded["format_version"] == "SAP_ERP_6.0"
        assert "Customer" in loaded["mappings"]

    def test_config_not_found_raises_runtime_error(self):
        """Missing config file raises RuntimeError with path in message."""
        with patch("os.path.exists", return_value=False):
            parser = SAPParser.__new__(SAPParser)
            with pytest.raises(RuntimeError, match="sap_column_map"):
                parser._load_column_map()

    def test_real_config_file_loads_from_correct_path(self):
        """SAP_COLUMN_MAP_PATH resolves to the real file — catches one-dot-too-many regressions."""
        import os
        from app.config import settings

        assert os.path.exists(settings.SAP_COLUMN_MAP_PATH), (
            f"sap_column_map.json not found at resolved path: {settings.SAP_COLUMN_MAP_PATH}. "
            "Check SAP_COLUMN_MAP_PATH in config.py — likely a wrong number of '..' levels."
        )
        parser = SAPParser.__new__(SAPParser)
        loaded = parser._load_column_map()
        assert "mappings" in loaded
        assert "required_internal_fields" in loaded
