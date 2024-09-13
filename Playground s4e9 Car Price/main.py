import pandas as pd
from autogluon.tabular import TabularDataset, TabularPredictor
import os
from os.path import abspath, dirname


os.chdir(dirname(abspath(__file__)))
train = pd.read_parquet('train.parquet')
test = pd.read_parquet('test.parquet')

# train['class'].replace(to_replace=['e','p'],value=[0,1], inplace=True)

train_data = TabularDataset(train)
test_data = TabularDataset(test)
predictor = TabularPredictor(problem_type='regression',label='price',eval_metric='root_mean_squared_error').fit(train_data=train_data,presets='best_quality',ag_args_fit={'num_gpus': 1},ds_args={'validation_procedure':'cv','n_folds':5,'n_repeats':4},time_limit=3600*6)
predictions = predictor.predict(test_data)
predictions = predictor.predict(test)

sample = pd.read_csv('sample_submission.csv')
# sample.head()
submission = pd.DataFrame({'id':sample['id'],'price':predictions})
submission.to_csv('autog-ensfull.csv',index=False)
submission.head()
# submission.head()