"""
CRM Import Service — bulk customer import from a CRM Excel export.

Fixed columns (Customer ID, Customer Name, Phone, Email) — not SAP, so
no JSON column-map config per architect decision (the SAP no-hardcode
rule is scoped to SAP exports specifically).

On a name conflict (same Customer ID, different name already stored):
the entire row is held back — no field is updated, only the conflict is
recorded — to avoid partial-write ambiguity (see docs/arch-sprint1-decisions.md).
"""
import logging
from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd

from app.repositories import customer_repo
from app.services.language_detection import detect_language

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["Customer ID", "Customer Name", "Phone", "Email"]


class CRMImportError(Exception):
    """Raised when a CRM export file cannot be parsed or is missing required columns."""


@dataclass
class CRMImportResult:
    updated: int = 0
    created: int = 0
    conflicts: int = 0
    conflict_details: list[dict] = field(default_factory=list)


class CRMImportService:
    """
    Usage:
        service = CRMImportService(staff_id=90001)
        result = service.import_file(db, file_bytes, filename="crm_export.xlsx")
    """

    def __init__(self, staff_id: int):
        self.staff_id = staff_id

    def import_file(self, db, file: BytesIO, filename: str) -> CRMImportResult:
        df = self._read_file(file, filename)
        self._assert_required_columns(df, filename)
        return self._process_rows(db, df)

    def _read_file(self, file: BytesIO, filename: str) -> pd.DataFrame:
        try:
            df = pd.read_excel(file)
        except Exception as exc:
            raise CRMImportError(f"Cannot read file '{filename}': {exc}") from exc

        if df.empty:
            raise CRMImportError(f"File '{filename}' is empty — no rows to import.")

        return df

    def _assert_required_columns(self, df: pd.DataFrame, filename: str) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise CRMImportError(
                f"File '{filename}' is missing required column(s): {missing}. "
                f"Expected: {REQUIRED_COLUMNS}."
            )

    def _process_rows(self, db, df: pd.DataFrame) -> CRMImportResult:
        result = CRMImportResult()

        for _, row in df.iterrows():
            customer_id = str(row["Customer ID"]).strip()
            name = str(row["Customer Name"]).strip()
            phone = str(row["Phone"]).strip() if pd.notna(row.get("Phone")) and str(row["Phone"]).strip() else None
            email = str(row["Email"]).strip() if pd.notna(row.get("Email")) and str(row["Email"]).strip() else None

            existing = customer_repo.get_by_id(db, customer_id)

            if existing is None:
                customer_repo.create(
                    db,
                    {
                        "customer_id": customer_id,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "language": detect_language(name),
                        "language_source": "auto_detected",
                        "source": "crm_import",
                        "staff_id": self.staff_id,
                    },
                )
                result.created += 1
                logger.info("crm_import: created customer_id=%s", customer_id)
                continue

            if existing.name != name:
                result.conflicts += 1
                result.conflict_details.append(
                    {"customer_id": customer_id, "existing_name": existing.name, "import_name": name}
                )
                logger.warning("crm_import: name conflict for customer_id=%s", customer_id)
                continue

            customer_repo.update_contact_info(db, existing, phone=phone, email=email)
            result.updated += 1
            logger.info("crm_import: updated customer_id=%s", customer_id)

        return result
