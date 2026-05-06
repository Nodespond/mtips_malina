from db.connection import get_connection
from typing import Dict, List, Tuple, Optional
from ml_model import predict_best, is_model_trained


class Solver:

    @staticmethod
    def classify_instance(input_data: Dict[str, str]) -> Tuple[Optional[List[str]], List[dict]]:
        if not input_data:
            return None, []

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM varieties ORDER BY name")
        all_varieties = cursor.fetchall()

        suitable = []
        all_rejections = []

        for var_row in all_varieties:
            variety_id = var_row["id"]
            variety_name = var_row["name"]

            is_suitable = True
            variety_rejections = []

            for prop_name, user_value in input_data.items():
                cursor.execute("""
                    SELECT p.type, vv.categorical_value, vv.min_value, vv.max_value
                    FROM variety_properties vp
                    JOIN properties p ON vp.property_id = p.id
                    LEFT JOIN variety_values vv 
                        ON vv.variety_id = vp.variety_id 
                       AND vv.property_id = vp.property_id
                    WHERE vp.variety_id = ? AND p.name = ?
                """, (variety_id, prop_name))

                spec = cursor.fetchone()

                if not spec:
                    is_suitable = False
                    variety_rejections.append({
                        "property": prop_name,
                        "user_value": user_value,
                        "reason": "свойство отсутствует у данного вида"
                    })
                    continue

                prop_type = spec["type"]

                if prop_type == "categorical":
                    expected = spec["categorical_value"]
                    if user_value != expected:
                        is_suitable = False
                        variety_rejections.append({
                            "property": prop_name,
                            "user_value": user_value,
                            "expected": expected,
                            "reason": f"введено '{user_value}', ожидалось '{expected}'"
                        })
                else:
                    try:
                        user_num = float(user_value)
                        min_v = spec["min_value"]
                        max_v = spec["max_value"]
                        if not (min_v <= user_num <= max_v):
                            is_suitable = False
                            variety_rejections.append({
                                "property": prop_name,
                                "user_value": user_value,
                                "reason": f"введено {user_num}, ожидался диапазон [{min_v} — {max_v}]"
                            })
                    except (ValueError, TypeError):
                        is_suitable = False
                        variety_rejections.append({
                            "property": prop_name,
                            "user_value": user_value,
                            "reason": "некорректный формат числа"
                        })

            if is_suitable:
                suitable.append(variety_name)
            else:
                all_rejections.append({
                    "variety": variety_name,
                    "reasons": variety_rejections
                })

        conn.close()

        if suitable and len(suitable) > 1:
            if is_model_trained():
                print(f"[Solver] Найдено {len(suitable)} подходящих видов: {suitable}")
                print(f"[Solver] Применяю ML-модель для выбора лучшего...")

                try:
                    best_variety = predict_best(input_data, suitable)
                    if best_variety and best_variety in suitable:
                        print(f"[Solver] ML-модель выбрала: '{best_variety}'")
                        suitable = [best_variety]  #оставляем только лучший
                    else:
                        print(f"[Solver] ML-модель вернула неожиданный результат, оставляю все подходящие")
                except Exception as e:
                    print(f"[Solver] Ошибка при работе ML-модели: {e}")
                    print(f"[Solver] Оставляю все {len(suitable)} подходящих видов")
            else:
                print(f"[Solver] ML-модель не обучена, возвращаю все {len(suitable)} подходящих видов")

        return (suitable if suitable else None, all_rejections)