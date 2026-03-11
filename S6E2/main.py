import pandas as pd
from autogluon.tabular import TabularPredictor

target_col = 'Heart Disease'
excel_filename = 'autogluon_comparison_results.xlsx'
eval_metric = 'roc_auc'  # AutoGluon will now optimize for ROC AUC

def train_and_evaluate(file_path, model_name):
    print(f"\n{'='*40}")
    print(f"Training: {model_name}")
    print(f"{'='*40}")
    
    # Load data
    df = pd.read_csv(file_path)
    
    # Initialize the predictor (eval_metric goes here!)
    predictor = TabularPredictor(
        label=target_col, 
        eval_metric=eval_metric, 
        path=f"ag_models/{model_name}"
    )
    
    # Fit the predictor (Training parameters go here!)
    predictor.fit(
        train_data=df,
        time_limit=3600, 
        presets='best_quality',
        ag_args_fit={'num_gpus': 1}
    )
    
    # Get the full leaderboard
    leaderboard = predictor.leaderboard(silent=True)
    print(f"Finished training {model_name}. Leaderboard generated.")
    
    return predictor, leaderboard

if __name__ == "__main__":
    # 1. Train Baseline
    pred_base, lb_base = train_and_evaluate('train_baseline.csv', 'Baseline_Model')
    
    # 2. Train with Interactions
    pred_interact, lb_interact = train_and_evaluate('train_interactions.csv', 'Interaction_Model')
    
    # 3. Extract best scores for the summary
    best_base_score = lb_base.iloc[0]['score_val']
    best_interact_score = lb_interact.iloc[0]['score_val']
    
    # This will pull 'roc_auc' directly from the AutoGluon results to confirm it was used
    eval_metric_used = lb_base.iloc[0]['eval_metric'] 
    
    # 4. Create a Summary DataFrame
    summary_data = {
        'Dataset': ['Baseline (No Interactions)', 'With Interactions'],
        'Best Model': [lb_base.iloc[0]['model'], lb_interact.iloc[0]['model']],
        'Validation Score (ROC AUC)': [best_base_score, best_interact_score],
        'Evaluation Metric': [eval_metric_used, eval_metric_used],
        'Score Difference': [0, best_interact_score - best_base_score]
    }
    df_summary = pd.DataFrame(summary_data)
    
    # 5. Save everything to an Excel file
    print(f"\nSaving results to {excel_filename}...")
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Write the summary sheet
        df_summary.to_excel(writer, sheet_name='Comparison_Summary', index=False)
        
        # Write the full leaderboards to separate sheets
        lb_base.to_excel(writer, sheet_name='Baseline_Leaderboard', index=False)
        lb_interact.to_excel(writer, sheet_name='Interactions_Leaderboard', index=False)
        
    print(f"✅ Results successfully saved to {excel_filename}!")