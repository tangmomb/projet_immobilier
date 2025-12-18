import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Modèles
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR

# Charger les données
df = pd.read_csv("csv/STEP03/STEP03_maisons_dept22_sans_outliers.csv")

# Features (X) et cible (y)
X = df[["Code INSEE", "Taille"]]
y = df["Prix"]

# Séparer en train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Liste des modèles à tester
models = {
    "Linear Regression": LinearRegression(),
    "Ridge": Ridge(),
    "Lasso": Lasso(),
    "KNN": KNeighborsRegressor(),
    "Random Forest": RandomForestRegressor(),
    "Gradient Boosting": GradientBoostingRegressor(),
    "SVR": SVR()
}

# Tester chaque modèle
results = []
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    results.append((name, mse, r2))

# Afficher les résultats
print("Résultats comparés :")
for name, mse, r2 in results:
    print(f"{name:20s} -> MSE: {mse:,.2f}, R²: {r2:.4f}")

# Trouver le meilleur modèle
best_model = max(results, key=lambda x: x[2])  # meilleur R²
print("\n🏆 Meilleur modèle :", best_model[0], f"(R² = {best_model[2]:.4f})")
