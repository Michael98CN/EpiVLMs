### 🛠️ Utilities: Temporal Post-processing for Adverse Conditions

#For real-world deployments involving low-quality recordings (e.g., 720p compression artifacts) or night-vision environments, isolated visual noise might trigger transient false positives. We provide a simple rule-based temporal filter (`temporal_filter.py`) that enforces a minimum duration constraint. 

#Applying this script with `min_duration=2` effectively smooths out isolated spurious artifacts, notably improving **Specificity** without compromising the model's robust **Recall**.

import pandas as pd
import ast

def remove_short_spikes(preds, min_duration=2):
    """
    Minimum duration filter to remove transient false positives.
    Flips contiguous '1's to '0's if their length is less than min_duration.
    """
    smoothed = list(preds)
    n = len(smoothed)
    i = 0
    
    while i < n:
        if smoothed[i] == 1:
            start = i
            while i < n and smoothed[i] == 1:
                i += 1
            end = i
            
            if (end - start) < min_duration:
                for j in range(start, end):
                    smoothed[j] = 0
        else:
            i += 1
            
    return smoothed

def calculate_metrics(df_subset, pred_column):
    """Calculates Specificity and Recall for a given subset."""
    total_TP = total_FP = total_TN = total_FN = 0
    
    for _, row in df_subset.iterrows():
        gt = row['GT_Segments']
        pred = row[pred_column]
        min_len = min(len(gt), len(pred))
        
        for i in range(min_len):
            if gt[i] == 1 and pred[i] == 1:
                total_TP += 1
            elif gt[i] == 0 and pred[i] == 1:
                total_FP += 1
            elif gt[i] == 0 and pred[i] == 0:
                total_TN += 1
            elif gt[i] == 1 and pred[i] == 0:
                total_FN += 1
                
    recall = total_TP / (total_TP + total_FN) if (total_TP + total_FN) > 0 else 0
    specificity = total_TN / (total_TN + total_FP) if (total_TN + total_FP) > 0 else 0
    
    return round(specificity * 100, 2), round(recall * 100, 2)

if __name__ == "__main__":
    # Configuration (Modify these parameters as needed)
    FILE_PATH = 'data/your_predictions.xlsx' 
    MIN_DURATION = 2
    
    print("Loading data...")
    df = pd.read_excel(FILE_PATH)
    
    # Parse list strings into actual Python lists
    df['GT_Segments'] = df['GT_Segments'].apply(lambda x: ast.literal_eval(str(x)) if isinstance(x, str) else x)
    df['Pred_Segments'] = df['Pred_Segments'].apply(lambda x: ast.literal_eval(str(x)) if isinstance(x, str) else x)
    
    print(f"Applying temporal filter (min_duration={MIN_DURATION})...")
    df['Smoothed_Preds'] = df['Pred_Segments'].apply(lambda x: remove_short_spikes(x, min_duration=MIN_DURATION))
    
    print("\n" + "="*40)
    print("PERFORMANCE EVALUATION (Adverse Conditions)")
    print("="*40)
    
    # Evaluate 720p subset
    df_720p = df[df['DeviceClass'].str.contains('720p', na=False)]
    if not df_720p.empty:
        orig_spec, orig_rec = calculate_metrics(df_720p, 'Pred_Segments')
        new_spec, new_rec = calculate_metrics(df_720p, 'Smoothed_Preds')
        print(f"[720p Videos] (n={len(df_720p)})")
        print(f"  Original -> Specificity: {orig_spec}%, Recall: {orig_rec}%")
        print(f"  Smoothed -> Specificity: {new_spec}%, Recall: {new_rec}%")
        print("-" * 40)
        
    # Evaluate Night-vision subset
    df_night = df[df['Illumination'].str.contains('Night-vision', na=False, case=False)]
    if not df_night.empty:
        orig_spec, orig_rec = calculate_metrics(df_night, 'Pred_Segments')
        new_spec, new_rec = calculate_metrics(df_night, 'Smoothed_Preds')
        print(f"[Night-Vision Videos] (n={len(df_night)})")
        print(f"  Original -> Specificity: {orig_spec}%, Recall: {orig_rec}%")
        print(f"  Smoothed -> Specificity: {new_spec}%, Recall: {new_rec}%")
        print("-" * 40)
