"""
Auto-Touch Service — orchestrates the today-list, generate, send, and
skip flows. Never queries the DB directly — always through
auto_touch_repo / task_repo.

NOTE (DEV-3 blocked): product_clean enrichment is a passthrough of the
raw SAP material_desc until sap_product_parser.py lands (blocked on
real sample Material Description values from the architect — see
docs/sprint1-backlog.md ARCH-5). category/size are always None until then.
"""
import logging
from datetime import date, datetime, timezone

from app.repositories import auto_touch_repo, task_repo
from app.services import line_client, sendgrid_client
from app.services.message_generator import MessageGenerator

logger = logging.getLogger(__name__)


class AutoTouchOwnershipError(Exception):
    """Raised when a staff member acts on a customer/task that isn't theirs."""


class AutoTouchService:
    def get_today_list(self, db, staff_id: int) -> list[dict]:
        rows = auto_touch_repo.get_today_list(db, staff_id)
        return [self._to_auto_touch_customer(task, transaction, customer) for task, transaction, customer in rows]

    def generate_message(self, db, customer_id: str, task_id: int, staff_id: int):
        task, transaction, customer = self._get_owned_row(db, task_id, staff_id)
        products = [
            p for p in self._products_for(transaction) if not p["returned"]
        ]
        generator = MessageGenerator()
        return generator.generate(
            customer_name=customer.name,
            language=customer.language,
            touchpoint=task.task_type,
            products=products,
        )

    def send_message(
        self, db, customer_id: str, task_id: int, message_text: str, channels: list[str] | None, staff_id: int
    ) -> dict:
        task, transaction, customer = self._get_owned_row(db, task_id, staff_id)

        available = {"line": bool(customer.line_id), "email": bool(customer.email)}
        requested = channels if channels else [c for c, ok in available.items() if ok]

        channels_sent: list[str] = []
        status_line = None
        status_email = None

        if "line" in requested:
            if available["line"]:
                ok = line_client.push_message(customer.line_id, message_text)
                status_line = "sent" if ok else "failed"
                if ok:
                    channels_sent.append("line")
            else:
                status_line = "not_available"

        if "email" in requested:
            if available["email"]:
                ok = sendgrid_client.send_email(customer.email, "A note from your Hugo Boss associate", message_text)
                status_email = "sent" if ok else "failed"
                if ok:
                    channels_sent.append("email")
            else:
                status_email = "not_available"

        sent_at = datetime.now(timezone.utc)

        auto_touch_repo.create_message(
            db,
            {
                "customer_id": customer_id,
                "staff_id": staff_id,
                "task_id": task_id,
                "touchpoint_type": task.task_type,
                "message_text": message_text,
                "channel_line": "line" in requested,
                "channel_email": "email" in requested,
                "status_line": status_line,
                "status_email": status_email,
                "sent_at": sent_at,
            },
        )

        if channels_sent:
            task_repo.mark_done(db, task_id)

        if requested and len(channels_sent) == len(requested):
            status = "sent"
        elif channels_sent:
            status = "partial"
        else:
            status = "failed"

        logger.info("auto_touch_service: send task_id=%d status=%s channels_sent=%s", task_id, status, channels_sent)

        return {
            "customer_id": customer_id,
            "task_id": task_id,
            "channels_sent": channels_sent,
            "sent_at": sent_at,
            "status": status,
        }

    def skip(self, db, customer_id: str, staff_id: int) -> dict:
        row = auto_touch_repo.get_pending_task_for_customer(db, customer_id, staff_id)
        if row is None:
            raise AutoTouchOwnershipError("No pending task found for this customer today.")
        task, transaction, customer = row
        deferred_to = auto_touch_repo.record_skip(db, task)
        return {"task_id": task.id, "deferred_to": deferred_to}

    def get_status(self, db, staff_id: int) -> dict:
        return auto_touch_repo.get_status_summary(db, staff_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_owned_row(self, db, task_id: int, staff_id: int) -> tuple:
        row = auto_touch_repo.get_task_with_customer(db, task_id)
        if row is None:
            raise AutoTouchOwnershipError("Task not found.")
        task, transaction, customer = row
        if transaction.staff_id != staff_id:
            raise AutoTouchOwnershipError("This customer's task does not belong to you.")
        return task, transaction, customer

    def _products_for(self, transaction) -> list[dict]:
        if not transaction.material_desc:
            return []
        return [
            {
                "product_raw": transaction.material_desc,
                "product_clean": transaction.material_desc,  # TODO(DEV-3): sap_product_parser.parse_product_name()
                "category": None,
                "size": None,
                "price": transaction.price,
                "returned": transaction.returned,
            }
        ]

    def _to_auto_touch_customer(self, task, transaction, customer) -> dict:
        return {
            "customer_id": customer.customer_id,
            "customer_name": customer.name,
            "language": customer.language,
            "task_id": task.id,
            "task_type": task.task_type,
            "due_date": task.due_date,
            "days_since_purchase": (date.today() - task.due_date).days,
            "products": self._products_for(transaction),
            "channels_available": {"email": bool(customer.email), "line": bool(customer.line_id)},
            "send_status": "pending",
        }
