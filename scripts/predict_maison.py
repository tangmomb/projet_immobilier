import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Load the CSV data (replace 'houses.csv' with your actual file path)
data = pd.read_csv('csv/STEP03/STEP03_maisons_dept22_sans_outliers.csv')

# Assume columns: 'city', 'size', 'rooms', 'price'
X = data[['city', 'size', 'rooms']]
y = data['price']

# Preprocess: One-hot encode 'city'
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(), ['city'])
    ],
    remainder='passthrough'
)

# Create pipeline with preprocessing and linear regression
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', LinearRegression())
])

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model.fit(X_train, y_train)

# Predict for a new house (example: city='Paris', size=100, rooms=3)
new_house = pd.DataFrame({'city': ['Paris'], 'size': [100], 'rooms': [3]})
predicted_price = model.predict(new_house)
print(f"Predicted price: {predicted_price[0]}")