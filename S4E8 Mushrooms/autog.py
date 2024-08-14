import pandas as pd
from autogluon.tabular import TabularDataset, TabularPredictor
import os
from os.path import abspath, dirname


os.chdir(dirname(abspath(__file__)))
train = pd.read_parquet('train-AG.parquet')
test = pd.read_parquet('test-AG.parquet')

train['class'].replace(to_replace=['e','p'],value=[0,1], inplace=True)

train_data = TabularDataset(train)
test_data = TabularDataset(test)
# predictor = TabularPredictor(problem_type='multiclass',label='NObeyesdad',eval_metric='accuracy').fit(train_data=train_data,presets='best_quality',ag_args_fit={'num_gpus': 1},time_limit=7200,hyperparameters={'GBM':{},'CAT':{},'XT':{},'XGB':{}},)
predictor = TabularPredictor(problem_type='binary',label='class',eval_metric='mcc').fit(train_data=train,presets='best_quality',ag_args_fit={'num_gpus': 1},ds_args={'n_folds':3},excluded_model_types=['KNN','NN_TORCH','RF','XT'],time_limit=3600*6)

predictions = predictor.predict(test)

sample = pd.read_csv('sample_submission.csv')
# sample.head()
submission = pd.DataFrame({'id':sample.id,'class':predictions})
submission['class'].replace(to_replace=[0,1],value=['e','p'],inplace=True)
submission.to_csv('ag-ens.csv',index=False)
# submission.head()