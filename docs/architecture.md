# Technical decisions

Maitre's architecture addresses three practical problems in restaurant order management. Each decision below connects the problem to its implementation, tradeoff, and tests.

## 1. Keep business rules independent of the ORM

Using SQLAlchemy models throughout the application tied business logic and response serialization to the database session.

`Table`, `Product`, `Order`, and `OrderItem` are now plain Python dataclasses. Entities own state transitions, such as rejecting changes to a finished order. Services depend on repository ports defined with `Protocol`; infrastructure adapters map SQLAlchemy models to domain entities. HTTP handlers translate domain exceptions into responses without adding HTTP dependencies to the business rules.

**Tradeoff:** separate entities and database models require explicit mapping. In return, business rules can be tested without a database, and returned entities remain usable after the session closes.

**Evidence:** [domain entities](../src/maitre_api/domain/entities), [repository mapping](../src/maitre_api/infrastructure/repositories/mappers.py), [application boundary test](../tests/test_application_boundaries.py), and [serialization after session closure](../tests/test_domain_entities_integration.py).

## 2. Persist an operation as one transaction

Creating an order occupies a table and inserts its items. If a product is invalid after the table has been marked occupied, committing those changes separately could leave the table unavailable without the intended order.

Services coordinate these changes through a Unit of Work and commit once after the operation succeeds. Repositories flush changes but do not commit. An exception or exit without a commit triggers rollback. Closing or cancelling an order also persists its new status and the released table in the same transaction.

Each item stores the product price at the time it is added, preserving the charged amount independently of later product price changes.

**Tradeoff:** services must explicitly request persistence and commit. Rollback restores database state; it does not rewind changes to in-memory entities.

**Evidence:** [order service](../src/maitre_api/application/services/order_service.py), [Unit of Work](../src/maitre_api/infrastructure/database/unit_of_work.py), [transaction tests](../tests/test_unit_of_work.py), and [HTTP lifecycle and rollback tests](../tests/test_api_integration.py).

## 3. Protect order state from competing requests

Two requests can observe the same available table or open order before either commits. Checking the status in application code alone does not prevent that race.

Order creation locks the table row with `SELECT ... FOR UPDATE`. Adding items, closing, and cancelling lock the order row before validating its state. Locked reads refresh previously loaded ORM values with `populate_existing=True`. PostgreSQL also enforces at most one open order per table through a partial unique index.

Table numbers have a separate unique constraint. The repository translates its duplicate-number violation into a domain conflict, covering concurrent inserts even when both requests initially find no matching table.

**Tradeoff:** competing mutations may wait for a transaction to finish. Locks protect the service workflows; the database constraints provide additional integrity checks for persisted data.

**Evidence:** [order repository](../src/maitre_api/infrastructure/repositories/order_repository.py), [unique open-order index](../alembic/versions/b9e01347187a_add_unique_open_order_per_table.py), [concurrent creation tests](../tests/test_order_concurrency_integration.py), and [competing mutation tests](../tests/test_order_mutations_integration.py).
