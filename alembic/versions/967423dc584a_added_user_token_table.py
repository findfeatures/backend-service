"""added user token table

Revision ID: 967423dc584a
Revises: 010d715daceb
Create Date: 2019-12-29 17:39:57.978052

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op


# revision identifiers, used by Alembic.
revision = "967423dc584a"
down_revision = "010d715daceb"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_datetime_utc",
            sa.DateTime(),
            server_default=sa.text("(now() at time zone 'utc')"),
            nullable=False,
        ),
        sa.Column(
            "token",
            sqlalchemy_utils.types.password.PasswordType(length=1024),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "users", sa.Column("verified", sa.Boolean(), server_default="f", nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "verified")
    op.drop_table("user_tokens")
    # ### end Alembic commands ###