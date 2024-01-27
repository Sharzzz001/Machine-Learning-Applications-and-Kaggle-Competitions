from sklearn.metrics import mean_squared_error
import numpy as np

def mse_func(y_true, y_pred) -> float:
    mse = mean_squared_error(np.log1p(y_true), np.log1p(y_pred))
    rmse = np.sqrt(mse)
    return rmse