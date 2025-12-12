from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class HeritageSiteModel(Base):
    __tablename__ = 'heritage_site'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    country = Column(String(100))
    description_en = Column(Text)
    description_zh = Column(Text)
    content = Column(Text)
    category = Column(String(50))
    metadata_ = Column("metadata", JSONB) # metadata is reserved in some contexts, mapping it explicitly
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_heritage_country', 'country'),
        Index('idx_heritage_category', 'category'),
    )

    def __repr__(self):
        return f"<HeritageSite(name='{self.name}', country='{self.country}')>"
