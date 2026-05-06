# ml_model.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from db.connection import get_connection

_trained_pipeline = None


def _extract_raw_data_from_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM varieties ORDER BY name")
    varieties = cursor.fetchall()

    cursor.execute("SELECT id, name, type FROM properties ORDER BY name")
    properties = cursor.fetchall()

    raw_data = []

    for variety in varieties:
        variety_dict = {'variety': variety['name']}

        for prop in properties:
            prop_name = prop['name']
            prop_type = prop['type']

            if prop_type == 'categorical':
                cursor.execute("""
                    SELECT categorical_value 
                    FROM variety_values 
                    WHERE variety_id = ? AND property_id = ?
                """, (variety['id'], prop['id']))
                values = [row['categorical_value'] for row in cursor.fetchall()]
                variety_dict[prop_name] = values if values else []
            else:
                cursor.execute("""
                    SELECT min_value, max_value 
                    FROM variety_values 
                    WHERE variety_id = ? AND property_id = ?
                """, (variety['id'], prop['id']))
                row = cursor.fetchone()
                if row and row['min_value'] is not None:
                    variety_dict[prop_name] = (row['min_value'], row['max_value'])
                else:
                    variety_dict[prop_name] = None

        raw_data.append(variety_dict)

    conn.close()
    return raw_data


def _generate_synthetic_samples(raw_data, samples_per_class=250):
    all_samples = []

    for variety_data in raw_data:
        variety_name = variety_data['variety']

        for _ in range(samples_per_class):
            sample = {'variety': variety_name}

            for prop_name, prop_value in variety_data.items():
                if prop_name == 'variety':
                    continue

                if prop_value is None or (isinstance(prop_value, list) and len(prop_value) == 0):
                    sample[prop_name] = np.nan
                elif isinstance(prop_value, tuple):
                    min_val, max_val = prop_value
                    if isinstance(min_val, float) or isinstance(max_val, float):
                        sample[prop_name] = np.random.uniform(min_val, max_val)
                    else:
                        sample[prop_name] = np.random.randint(min_val, max_val + 1)
                elif isinstance(prop_value, list):
                    sample[prop_name] = np.random.choice(prop_value)
                else:
                    sample[prop_name] = prop_value

            all_samples.append(sample)

    df = pd.DataFrame(all_samples)

    y = df['variety']
    X = df.drop(columns=['variety'])

    return X, y


def train_model():

    global _trained_pipeline

    print("Начинаю обучение модели машинного обучения...")

    raw_data = _extract_raw_data_from_db()
    print(f"Извлечены данные о {len(raw_data)} видах")

    np.random.seed(42)
    X, y = _generate_synthetic_samples(raw_data, samples_per_class=250)
    print(f"Сгенерировано {len(X)} синтетических примеров")

    categorical_features = []
    numeric_features = []

    for col in X.columns:
        prop_type = None
        for variety_data in raw_data:
            if col in variety_data:
                val = variety_data[col]
                if isinstance(val, list):
                    prop_type = 'categorical'
                elif isinstance(val, tuple):
                    prop_type = 'numeric'
                break

        if prop_type == 'categorical':
            categorical_features.append(col)
        elif prop_type == 'numeric':
            numeric_features.append(col)

    print(f"Категориальные признаки: {categorical_features}")
    print(f"Числовые признаки: {numeric_features}")

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features) if numeric_features else
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
            if categorical_features else
            ('cat', 'passthrough', categorical_features)
        ]
    )

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        ))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("Обучение модели Random Forest...")
    pipeline.fit(X_train, y_train)

    accuracy = pipeline.score(X_test, y_test)
    print(f"Точность модели на тестовой выборке: {accuracy:.2%}")

    numeric_medians = {}
    for col in numeric_features:
        if col in X.columns:
            numeric_medians[col] = X[col].median()

    _trained_pipeline = {
        'pipeline': pipeline,
        'feature_names': list(X.columns),
        'categorical_features': categorical_features,
        'numeric_features': numeric_features,
        'numeric_medians': numeric_medians
    }

    print("Модель успешно обучена")


def predict_best(input_data, suitable_varieties):

    global _trained_pipeline

    if _trained_pipeline is None:
        raise RuntimeError("Модель не обучена! Сначала вызовите train_model()")

    if not suitable_varieties:
        return None

    if len(suitable_varieties) == 1:
        return suitable_varieties[0]

    feature_names = _trained_pipeline['feature_names']
    categorical_features = _trained_pipeline['categorical_features']
    numeric_features = _trained_pipeline['numeric_features']

    #Создаём словарь с правильными типами данных
    #Для числовых признаков, которые не заданы,
    #используем СРЕДНЕЕ значение из обучающей выборки
    user_data_dict = {}
    for feature in feature_names:
        if feature in input_data:
            raw_value = input_data[feature]

            if feature in numeric_features:
                try:
                    user_data_dict[feature] = float(raw_value)
                except (ValueError, TypeError):
                    user_data_dict[feature] = None
            else:
                user_data_dict[feature] = str(raw_value) if raw_value else None
        else:
            user_data_dict[feature] = None

    user_df = pd.DataFrame([user_data_dict])

    #Для числовых NaN заменяем на медианные значения
    if hasattr(_trained_pipeline['pipeline'], 'feature_importances_'):
        #Получаем медианные значения из тренировочных данных
        for col in numeric_features:
            if col in user_df.columns and pd.isna(user_df[col]).any():
                #Используем медиану из тренировочных данных
                if 'numeric_medians' in _trained_pipeline:
                    user_df[col] = user_df[col].fillna(_trained_pipeline['numeric_medians'].get(col, 0))
                else:
                    user_df[col] = user_df[col].fillna(0)
            elif col in user_df.columns:
                user_df[col] = pd.to_numeric(user_df[col], errors='coerce')

    #Категориальные NaN заменяем на "unknown"
    for col in categorical_features:
        if col in user_df.columns:
            user_df[col] = user_df[col].apply(
                lambda x: str(x) if x is not None and not pd.isna(x) else "unknown"
            )

    print(f"DataFrame для предсказания:")
    print(user_df.to_string())

    try:
        probabilities = _trained_pipeline['pipeline'].predict_proba(user_df)
    except Exception as e:
        print(f"Ошибка при предсказании: {e}")
        print(f"Типы данных:\n{user_df.dtypes}")
        return suitable_varieties[0] if suitable_varieties else None

    classes = _trained_pipeline['pipeline'].classes_
    proba_dict = dict(zip(classes, probabilities[0]))

    suitable_with_proba = {
        variety: proba_dict.get(variety, 0.0)
        for variety in suitable_varieties
    }

    if not suitable_with_proba:
        return suitable_varieties[0]

    best_variety = max(suitable_with_proba, key=suitable_with_proba.get)
    best_proba = suitable_with_proba[best_variety]

    print(f"\n✓ ML-модель выбрала: '{best_variety}' (вероятность: {best_proba:.2%})")
    print(f"Все {len(suitable_with_proba)} подходящих видов с вероятностями:")

    for i, (variety, proba) in enumerate(sorted(suitable_with_proba.items(),
                                                key=lambda x: x[1], reverse=True), 1):
        marker = " ← выбран" if variety == best_variety else ""
        print(f"  {i:2d}. {variety}: {proba:.2%}{marker}")

    return best_variety


def is_model_trained():
    return _trained_pipeline is not None