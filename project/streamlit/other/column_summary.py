import pandas as pd

def edaSummarizeDfColumns(df: pd.DataFrame):
    summary=[]

    for column in df.columns:
        col_data = df[column]
        col_summary = {
            'column': column,
            'dtype': col_data.dtype,
            'is_categorical': False,
            'is_datetime': False,
            'unique_values': None,
            'min': None,
            'mean': None,
            'median': None,
            'max': None
        }

        # Try to parse as datetime
        try:
            pd.to_datetime(col_data, errors='raise')
            col_summary['is_datetime'] = True
        except (ValueError, TypeError):
            pass

        # Check if the column is categorical
        if col_data.dtype == 'object' or pd.api.types.is_integer_dtype(col_data):
            unique_count = col_data.nunique()
            if unique_count / len(col_data) < 0.05:  # Threshold for categorical
                col_summary['is_categorical'] = True
                col_summary['unique_values'] = unique_count

        # Calculate statistics for numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            col_summary['min'] = col_data.min()
            col_summary['mean'] = col_data.mean()
            col_summary['median'] = col_data.median()
            col_summary['max'] = col_data.max()

        summary.append(col_summary)

    return pd.DataFrame(summary)

# Example usage
# df = pd.read_csv('your_data.csv')
# summary_df = summarize_columns(df)
# print(summary_df)
