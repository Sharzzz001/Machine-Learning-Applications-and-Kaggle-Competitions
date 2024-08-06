from sklearn.metrics import matthews_corrcoef
import numpy as np

def score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return matthews_corrcoef(y_true, y_pred)