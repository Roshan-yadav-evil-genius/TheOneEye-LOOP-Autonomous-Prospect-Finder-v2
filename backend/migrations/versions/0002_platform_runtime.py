"""Add durable runtime, browser pool, brain memory, and outbox lifecycle."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from loop_api.persistence import models

revision: str = "0002_platform_runtime"
down_revision: str | None = "0001_initial_sqlite"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLES = (
    models.ConsumerInbox.__table__,
    models.ScheduledTask.__table__,
    models.JobRun.__table__,
    models.DeadLetter.__table__,
    models.BrainMemory.__table__,
    models.BrowserSession.__table__,
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in TABLES:
        table.create(bind, checkfirst=True)
    columns = {column["name"] for column in sa.inspect(bind).get_columns("integration_event")}
    additions = {
        "available_at": sa.Column("available_at", sa.DateTime(timezone=True)),
        "last_error": sa.Column("last_error", sa.Text),
        "dead_lettered_at": sa.Column("dead_lettered_at", sa.DateTime(timezone=True)),
    }
    with op.batch_alter_table("integration_event") as batch:
        for name, column in additions.items():
            if name not in columns:
                batch.add_column(column)
    op.execute(
        "UPDATE integration_event SET available_at = CURRENT_TIMESTAMP WHERE available_at IS NULL"
    )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("integration_event")}
    with op.batch_alter_table("integration_event") as batch:
        for name in ("dead_lettered_at", "last_error", "available_at"):
            if name in columns:
                batch.drop_column(name)
    for table in reversed(TABLES):
        table.drop(bind, checkfirst=True)
