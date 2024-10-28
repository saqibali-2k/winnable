import xgboost as xgb
import matplotlib.pyplot as plt
from src.training_data_processor import DATASET_FILEPATH, DATASET_LABELS_FILEPATH
from src.utils import load_dataset, save_model, split_train_validation

X, y = load_dataset(DATASET_FILEPATH, DATASET_LABELS_FILEPATH)
model: xgb.XGBClassifier = xgb.XGBClassifier(
    objective="binary:logistic", random_state=42, early_stopping_rounds=10
)
X = X.squeeze()
X, X_val, y, y_val = split_train_validation(X, y, validation_size=0.1)
print(X.shape, y.shape)
model.fit(X, y, eval_set=[(X_val, y_val)], verbose=True)

print(model.score(X, y))
print(model.score(X_val, y_val))
p = xgb.plot_importance(model, importance_type="weight")
# Save the plot to a file
plt.savefig("feature_importance.png")

# These are some sanity checks, uncomment to run them

# Start state: should be 50/50
# print(model.predict_proba([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]))
save_model(model, "./models/xgboost")
