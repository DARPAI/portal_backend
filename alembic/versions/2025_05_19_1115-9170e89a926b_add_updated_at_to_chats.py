"""add updated_at to chats.

Revision ID: 9170e89a926b
Revises: 1a669b6ad184
Create Date: 2025-05-19 11:15:49.677501

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9170e89a926b"
down_revision: Union[str, None] = "1a669b6ad184"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chats", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")))

    op.execute(
        """
               CREATE OR REPLACE FUNCTION update_chat_updated_at()
    RETURNS TRIGGER AS $$
               BEGIN
               UPDATE chats
               SET updated_at = NOW()
               WHERE id = NEW.chat_id;
               RETURN NEW;
               END;
    $$ LANGUAGE plpgsql;
               """
    )

    op.execute(
        """
               CREATE TRIGGER trg_update_chat_updated_at
                   AFTER INSERT ON messages
                   FOR EACH ROW
                   EXECUTE FUNCTION update_chat_updated_at();
               """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_update_chat_updated_at ON messages;")
    op.execute("DROP FUNCTION IF EXISTS update_chat_updated_at;")
    op.drop_column("chats", "updated_at")
