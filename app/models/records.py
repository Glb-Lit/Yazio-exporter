from dataclasses import dataclass


@dataclass
class NutritionLogRow:
    date: str
    time: str
    meal: str
    product: str
    amount: float
    unit: str
    portions: str
    calories_per_gram: float
    calories_total: float
    protein_per_gram: float
    fat_per_gram: float
    carbs_per_gram: float
    protein_total: float
    fat_total: float
    carbs_total: float
