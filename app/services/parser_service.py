import json
from pathlib import Path
from typing import Any


def _fix_encoding(name: str) -> str:
    try:
        return name.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
        return name


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


def parse_reports(days_file: Path, products_file: Path) -> tuple[list[dict[str, Any]], list[list[Any]], list[list[Any]]]:
    with days_file.open("r", encoding="utf-8") as file:
        days_data = json.load(file)
    with products_file.open("r", encoding="utf-8") as file:
        products_data = json.load(file)

    product_lookup = {pid: pdata for pid, pdata in products_data.items()}
    rows: list[dict[str, Any]] = []
    summary_by_meal: dict[tuple[str, str], float] = {}
    summary_by_day: dict[str, dict[str, float]] = {}

    for date, content in days_data.items():
        consumed = content.get("consumed")
        if not consumed or not isinstance(consumed, dict):
            continue

        products = consumed.get("products", [])
        if not isinstance(products, list):
            continue

        for item in products:
            if not isinstance(item, dict):
                continue

            product_id = item.get("product_id", "")
            product = product_lookup.get(product_id, {})
            name = _fix_encoding(product.get("name", "Unknown"))
            nutrients = product.get("nutrients", {})

            kcal_g = _to_float(nutrients.get("energy.energy", 0))
            protein_g = _to_float(nutrients.get("nutrient.protein", 0))
            fat_g = _to_float(nutrients.get("nutrient.fat", 0))
            carbs_g = _to_float(nutrients.get("nutrient.carb", 0))
            amount = _to_float(item.get("amount", 0))

            total_kcal = round(amount * kcal_g, 2)
            total_protein = round(amount * protein_g, 2)
            total_fat = round(amount * fat_g, 2)
            total_carbs = round(amount * carbs_g, 2)

            meal_type = item.get("daytime", "unknown")
            key_meal = (date, meal_type)

            summary_by_meal[key_meal] = summary_by_meal.get(key_meal, 0.0) + total_kcal
            if date not in summary_by_day:
                summary_by_day[date] = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
            summary_by_day[date]["kcal"] += total_kcal
            summary_by_day[date]["protein"] += total_protein
            summary_by_day[date]["fat"] += total_fat
            summary_by_day[date]["carbs"] += total_carbs

            rows.append(
                {
                    "Date": date,
                    "Time": item.get("date", ""),
                    "Meal": meal_type,
                    "Product": name,
                    "Amount": amount,
                    "Unit": item.get("serving", ""),
                    "Portions": item.get("serving_quantity", ""),
                    "Calories/g": kcal_g,
                    "Calories total": total_kcal,
                    "Protein/g": protein_g,
                    "Fat/g": fat_g,
                    "Carbs/g": carbs_g,
                    "Protein total": total_protein,
                    "Fat total": total_fat,
                    "Carbs total": total_carbs,
                }
            )

    meal_rows = [["Date", "Meal", "Calories total"]]
    for (date, meal), total in sorted(summary_by_meal.items()):
        meal_rows.append([date, meal, round(total, 2)])

    daily_rows = [["Date", "Calories total", "Protein total", "Fat total", "Carbs total"]]
    for date, data in sorted(summary_by_day.items()):
        daily_rows.append(
            [
                date,
                round(data["kcal"], 2),
                round(data["protein"], 2),
                round(data["fat"], 2),
                round(data["carbs"], 2),
            ]
        )

    return rows, meal_rows, daily_rows
