from sqlalchemy import Column, String, Integer
from app.core.database import Base


class ShelfLifeReference(Base):
    __tablename__ = "reference_shelf_life"

    ingredient_name = Column(String, primary_key=True)
    category = Column(String)
    pantry_days = Column(Integer)
    fridge_days = Column(Integer)
