"""
TDD — customer_repo.py.
Unified customer record CRUD. do_not_contact enforcement lives here
(get_contactable_by_id is the only variant callers needing a contactable
customer should use — SEC-3).
"""
from unittest.mock import MagicMock, patch

from app.repositories import customer_repo
from app.models.customer import Customer


def make_customer(customer_id="C1", do_not_contact=False) -> Customer:
    c = MagicMock(spec=Customer)
    c.customer_id = customer_id
    c.name = "Test Customer"
    c.phone = "0812345678"
    c.email = None
    c.line_id = None
    c.language = "th"
    c.language_source = "auto_detected"
    c.do_not_contact = do_not_contact
    c.source = "crm_import"
    c.staff_id = None
    return c


class TestGetById:
    def test_returns_customer_when_found(self):
        db = MagicMock()
        customer = make_customer()
        db.query.return_value.filter.return_value.first.return_value = customer
        result = customer_repo.get_by_id(db, "C1")
        assert result is customer

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = customer_repo.get_by_id(db, "C_MISSING")
        assert result is None


class TestGetContactableById:
    def test_filters_do_not_contact(self):
        """The query must filter do_not_contact == False at the DB layer."""
        db = MagicMock()
        customer = make_customer(do_not_contact=False)
        db.query.return_value.filter.return_value.first.return_value = customer
        result = customer_repo.get_contactable_by_id(db, "C1")
        assert result is customer
        # Assert filter() was called with more than one condition (id + do_not_contact)
        filter_call = db.query.return_value.filter.call_args
        assert len(filter_call[0]) >= 2

    def test_returns_none_for_do_not_contact_customer(self):
        """Even if the row exists, a do_not_contact=True customer must not be returned."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = customer_repo.get_contactable_by_id(db, "C_BLOCKED")
        assert result is None


class TestCreate:
    def test_create_inserts_and_flushes(self):
        db = MagicMock()
        data = {
            "customer_id": "C2",
            "name": "New Customer",
            "phone": "0899999999",
            "source": "crm_import",
        }
        result = customer_repo.create(db, data)
        db.add.assert_called_once()
        db.flush.assert_called_once()
        assert result.customer_id == "C2"


class TestRegister:
    def test_register_sets_manual_registration_source(self):
        db = MagicMock()
        data = {
            "customer_id": "TMP-abc123",
            "name": "Walk-in Customer",
            "phone": "0811111111",
            "staff_id": 90001,
        }
        result = customer_repo.register(db, data)
        db.add.assert_called_once()
        db.flush.assert_called_once()
        assert result.source == "manual_registration"
        assert result.staff_id == 90001


class TestUpdateContactInfo:
    def test_updates_phone_email_line_id_only(self):
        db = MagicMock()
        customer = make_customer()
        customer_repo.update_contact_info(
            db, customer, phone="0822222222", email="new@example.com", line_id="U123"
        )
        assert customer.phone == "0822222222"
        assert customer.email == "new@example.com"
        assert customer.line_id == "U123"
        db.flush.assert_called_once()


class TestAssignTempId:
    def test_returns_tmp_prefixed_unique_id(self):
        db = MagicMock()
        temp_id = customer_repo.assign_temp_id(db)
        assert temp_id.startswith("TMP-")
        assert len(temp_id) > len("TMP-")

    def test_two_calls_return_different_ids(self):
        db = MagicMock()
        id1 = customer_repo.assign_temp_id(db)
        id2 = customer_repo.assign_temp_id(db)
        assert id1 != id2
