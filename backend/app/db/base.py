from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base. Alembic's env.py imports app.models (which
    imports every model module) before reading Base.metadata, so autogenerate
    and the hand-written initial migration both see the full schema."""
