"""Create the initial SQLite OLTP schema."""

from alembic import op

from loop_api.persistence import models  # noqa: F401
from loop_api.persistence.database import Base

revision = "0001_initial_sqlite"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
