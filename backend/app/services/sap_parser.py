"""
SAP Parser Service — Rule 7 enforcer.
All SAP data passes through here before touching MySQL.
Column names are never hardcoded — loaded from sap_column_map.json.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO

import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class SAPParseError(Exception):
    """Raised when a SAP file cannot be parsed or fails validation."""


@dataclass
class ParseResult:
    records: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    rows_skipped: int = 0


class SAPParser:
    """
    Parses SAP CSV/Excel exports into validated dicts ready for DB insert.

    Usage:
        parser = SAPParser(staff_employee_code="EMP001")
        result = parser.parse(file_bytes, filename="export.csv")
        # result.records — list of clean dicts
        # result.errors  — list of row-level error strings
    """

    def __init__(self, staff_employee_code: str):
        self.staff_employee_code = staff_employee_code
        self._column_map = self._load_column_map()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def parse(self, file: BytesIO, filename: str) -> ParseResult:
        """
        Parse a SAP export file and return validated records for this staff.

        Raises:
            SAPParseError: file is empty, required column unmapped, or no
                           records found for this Sales Rep.
        """
        df = self._read_file(file, filename)
        df = self._remap_columns(df)
        self._assert_required_columns(df)
        df = self._filter_by_sales_rep(df)
        result = self._validate_rows(df)
        result.records = self._deduplicate_by_idoc(result.records)
        return result

    # ------------------------------------------------------------------
    # Step 1 — read file
    # ------------------------------------------------------------------

    def _read_file(self, file: BytesIO, filename: str) -> pd.DataFrame:
        try:
            if filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls"):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)
        except Exception as exc:
            raise SAPParseError(f"Cannot read file '{filename}': {exc}") from exc

        if df.empty:
            raise SAPParseError(f"File '{filename}' is empty — no data to import.")

        return df

    # ------------------------------------------------------------------
    # Step 2 — remap columns using config
    # ------------------------------------------------------------------

    def _remap_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename SAP column labels to internal field names."""
        mappings: dict[str, str] = self._column_map.get("mappings", {})
        rename_map = {}
        for col in df.columns:
            if col in mappings and mappings[col] is not None:
                rename_map[col] = mappings[col]

        if not rename_map:
            unmapped = list(df.columns[:3])  # show first few for diagnosis
            raise SAPParseError(
                f"No columns could be mapped from this file. "
                f"Unrecognised headers: {unmapped}. "
                f"Contact admin to update sap_column_map.json."
            )

        return df.rename(columns=rename_map)

    # ------------------------------------------------------------------
    # Step 3 — assert all required fields are present
    # ------------------------------------------------------------------

    def _assert_required_columns(self, df: pd.DataFrame) -> None:
        required: list[str] = self._column_map.get("required_internal_fields", [])
        missing = [f for f in required if f not in df.columns]
        if missing:
            raise SAPParseError(
                f"Required field(s) could not be mapped: {missing}. "
                f"Contact admin to update column mapping config."
            )

    # ------------------------------------------------------------------
    # Step 4 — filter by this staff member's employee_code
    # ------------------------------------------------------------------

    def _filter_by_sales_rep(self, df: pd.DataFrame) -> pd.DataFrame:
        if "staff_employee_code" not in df.columns:
            raise SAPParseError("staff_employee_code column missing after remapping.")

        normalized = df["staff_employee_code"].map(self._normalize_employee_code)
        filtered = df[normalized == self._normalize_employee_code(self.staff_employee_code)]

        if filtered.empty:
            raise SAPParseError(
                f"No records found for Sales Rep ID '{self.staff_employee_code}' in this file."
            )

        logger.info(
            "SAP Parser: filtered %d rows for Sales Rep %s",
            len(filtered),
            self.staff_employee_code,
        )
        return filtered

    # ------------------------------------------------------------------
    # Step 5 — row-level validation, skip bad rows, collect errors
    # ------------------------------------------------------------------

    def _validate_rows(self, df: pd.DataFrame) -> ParseResult:
        result = ParseResult()

        for idx, row in df.iterrows():
            errors = self._validate_row(row, idx)
            if errors:
                for err in errors:
                    result.errors.append(err)
                result.rows_skipped += 1
                logger.warning("SAP Parser: skipping row %s — %s", idx, errors)
                continue

            record = {
                "customer_id": self._normalize_employee_code(row["customer_id"]),
                "idoc_number": self._normalize_employee_code(row["idoc_number"]),
                "posting_date": self._parse_date(row["posting_date"]),
                "staff_employee_code": self._normalize_employee_code(row["staff_employee_code"]),
            }

            # Optional fields
            if "ean" in df.columns:
                record["ean"] = self._normalize_employee_code(row["ean"]) if pd.notna(row.get("ean")) else None
            if "material_desc" in df.columns:
                record["material_desc"] = str(row["material_desc"]).strip() if pd.notna(row.get("material_desc")) else None

            result.records.append(record)

        return result

    def _validate_row(self, row: pd.Series, idx: int) -> list[str]:
        errors = []
        required_in_row = ["customer_id", "idoc_number", "posting_date"]
        for field_name in required_in_row:
            val = row.get(field_name)
            if pd.isna(val) or str(val).strip() == "":
                errors.append(f"Row {idx}: '{field_name}' is blank or missing.")
        return errors

    @staticmethod
    def _deduplicate_by_idoc(records: list[dict]) -> list[dict]:
        """Keep first row per idoc_number — SAP exports have one row per line item, Lumine needs one per transaction."""
        seen: set[str] = set()
        deduped = []
        for record in records:
            idoc = record["idoc_number"]
            if idoc not in seen:
                seen.add(idoc)
                deduped.append(record)
        return deduped

    @staticmethod
    def _normalize_employee_code(val) -> str:
        """Normalize SAP numeric fields: Excel stores numbers as floats ('56546.0' → '56546')."""
        s = str(val).strip()
        try:
            return str(int(float(s)))
        except (ValueError, OverflowError):
            return s

    @staticmethod
    def _parse_date(value) -> date:
        if isinstance(value, date):
            return value
        parsed = pd.to_datetime(value, dayfirst=False, errors="coerce")
        if pd.isna(parsed):
            raise SAPParseError(f"Cannot parse date value: '{value}'")
        return parsed.date()

    # ------------------------------------------------------------------
    # Config loader — reads sap_column_map.json
    # ------------------------------------------------------------------

    def _load_column_map(self) -> dict:
        config_path = settings.SAP_COLUMN_MAP_PATH
        if not os.path.exists(config_path):
            raise RuntimeError(
                f"sap_column_map.json not found at: {config_path}. "
                f"Cannot parse SAP files without column mapping config."
            )
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
