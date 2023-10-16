from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.spreadsheet.infrastructure.postgres import Base


class SourceModel(Base):
    __tablename__ = "source"
    title: Mapped[str] = mapped_column(String(32), nullable=False)
