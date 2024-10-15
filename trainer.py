from sklearn.ensemble import AdaBoostClassifier
import xgboost as xgb
from data_pipeline import DATASET_FILEPATH, DATASET_LABELS_FILEPATH
from utils import load_dataset, save_model, split_train_validation


X, y = load_dataset(DATASET_FILEPATH, DATASET_LABELS_FILEPATH)
# model = AdaBoostClassifier(n_estimators=500, algorithm="SAMME", random_state=0)
model: xgb.XGBClassifier = xgb.XGBClassifier(
    objective="binary:logistic", random_state=42, early_stopping_rounds=10
)
X = X.squeeze()
X, X_val, y, y_val = split_train_validation(X, y, validation_size=0.1)
print(X.shape, y.shape)
model.fit(X, y, eval_set=[(X_val, y_val)], verbose=True)
# model.fit(X, y)

print(model.score(X, y))
print(model.score(X_val, y_val))
# print(model.feature_importances())
# print(model.feature_importances())
print(model.predict_proba([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]))
print(
    model.predict_proba(
        [[1445044, 0.1, 0.18, -0.8, 0.1, -0.04, 3, 0, 3, -1, -1, -5, 80000, -5, 180000]]
    )
)

print(
    model.predict_proba(
        [[1445044, 0.1, 0.18, 0.8, 0.1, -0.04, -5, 0, 3, -1, -1, 0, 0, 0, 0]]
    )
)
save_model(model, "./models/adaboost")
