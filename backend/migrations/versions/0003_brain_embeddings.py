"""Update BrainMemory to store local hash embeddings for vector recall."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_brain_embeddings"
down_revision: str | None = "0002_platform_runtime"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("brain_memory")}
    if "embedding" not in columns:
        with op.batch_alter_table("brain_memory") as batch:
            batch.add_column(sa.Column("embedding", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("brain_memory")}
    if "embedding" in columns:
        with op.batch_alter_table("brain_memory") as batch:
            batch.drop_column("embedding")
