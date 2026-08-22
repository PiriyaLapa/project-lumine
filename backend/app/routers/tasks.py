"""
Tasks Router — GET /api/v1/tasks and PATCH /api/v1/tasks/{task_id}
Multi-staff isolation enforced here:
  - sales_associate → sees only own tasks (via transaction.staff_id)
  - store_manager   → sees all tasks under their store_id
"""
import logging
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.repositories import task_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tasks"])


# ---------------------------------------------------------------------------
# Response schema — field names locked to openapi.yaml
# ---------------------------------------------------------------------------

class FollowUpTaskResponse(BaseModel):
    id: int
    customer_id: str       # LOCKED
    task_type: str         # LOCKED: 2D | 2W | 2M
    task_basis: str        # LOCKED: posting_date | manual_override
    due_date: date_type    # LOCKED
    calculated_from: date_type  # LOCKED
    status: str            # LOCKED: Pending | Done | Superseded
    staff_name: str | None = None  # LOCKED — null for tasks uploaded before migration 0005
    customer_name: str | None = None  # LOCKED — null for tasks uploaded before migration 0010 or absent from source file
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TaskUpdateRequest(BaseModel):
    status: str  # Only "Done" is accepted via PATCH (openapi.yaml)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/tasks", response_model=list[FollowUpTaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Return tasks visible to the authenticated staff.
    sales_associate: own tasks only.
    store_manager: all tasks under their store.
    """
    if current_staff.role == "store_manager":
        tasks = task_repo.get_tasks_for_store(db, current_staff.store_id)
    else:
        tasks = task_repo.get_tasks_for_staff(db, current_staff.staff_id)

    logger.info(
        "tasks.get_tasks: staff=%d role=%s store_id=%s count=%d",
        current_staff.staff_id, current_staff.role, current_staff.store_id, len(tasks),
    )

    return [_serialize(t, name, cust_name) for t, name, cust_name in tasks]


@router.patch("/tasks/{task_id}", response_model=FollowUpTaskResponse)
def update_task(
    task_id: int,
    body: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Mark a task as Done. Only "Done" is accepted (openapi.yaml: enum [Done]).
    Staff can only update their own tasks.
    """
    if body.status != "Done":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only status='Done' is accepted via PATCH.",
        )

    task = task_repo.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    # Multi-staff isolation: verify this task belongs to the requesting staff
    _assert_task_ownership(db, task, current_staff)

    if task.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is already {task.status}. Only Pending tasks can be marked Done.",
        )

    updated = task_repo.mark_done(db, task_id)
    db.commit()

    staff_name = task_repo.get_staff_name_for_task(db, updated.idoc_number)
    customer_name = task_repo.get_customer_name_for_task(db, updated.idoc_number)
    logger.info("Task %d marked Done by staff_id=%d", task_id, current_staff.staff_id)
    return _serialize(updated, staff_name, customer_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_task_ownership(db: Session, task, current_staff: TokenPayload):
    """
    Raises 403 if a sales_associate tries to update another associate's task.
    Managers can update any task in their store.
    """
    if current_staff.role == "store_manager":
        return  # managers see all tasks in their store

    from app.models.transaction import Transaction
    transaction = db.query(Transaction).filter(
        Transaction.idoc_number == task.idoc_number
    ).first()

    if not transaction or transaction.staff_id != current_staff.staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this task.",
        )


def _serialize(task, staff_name: str, customer_name: str | None = None) -> dict:
    return {
        "id": task.id,
        "customer_id": task.customer_id,
        "task_type": task.task_type,
        "task_basis": task.task_basis,
        "due_date": task.due_date,
        "calculated_from": task.calculated_from,
        "status": task.status,
        "staff_name": staff_name,
        "customer_name": customer_name,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
    }
