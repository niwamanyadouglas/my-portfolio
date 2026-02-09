import pandas as pd
import os

def clean_dataset(file_path, output_folder="cleaned_data"):
    """
    Cleans and organizes a raw dataset by performing the following steps:
    1. Standardize column names.
    2. Remove duplicate rows.
    3. Handle missing values.
    4. Export the cleaned dataset to a CSV file.

    Args:
        file_path (str): Path to the raw dataset (CSV file).
        output_folder (str): Folder to save the cleaned dataset.

    Returns:
        None
    """
    # Step 1: Load the dataset
    print(f"Loading dataset from {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    print(f"Initial dataset shape: {df.shape}")

    # Step 2: Standardize column names
    print("Standardizing column names...")
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
    print(f"Updated column names: {list(df.columns)}")

    # Step 3: Remove duplicate rows
    print("Removing duplicate rows...")
    initial_rows = len(df)
    df = df.drop_duplicates()
    removed_duplicates = initial_rows - len(df)
    print(f"Removed {removed_duplicates} duplicate rows.")

    # Step 4: Handle missing values
    print("Handling missing values...")
    # Fill numeric columns with mean
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        df[col].fillna(df[col].mean(), inplace=True)

    # Drop rows with excessive missing values (threshold: 50% missing)
    threshold = len(df) * 0.5
    df = df.dropna(axis=1, thresh=threshold)
    print(f"Dropped columns with more than 50% missing values.")

    # Step 5: Export the cleaned dataset
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file = os.path.join(output_folder, "cleaned_dataset.csv")
    print(f"Exporting cleaned dataset to {output_file}...")
    df.to_csv(output_file, index=False)

    print(f"Cleaned dataset saved successfully. Final shape: {df.shape}")

# Example Usage
if __name__ == "__main__":
    # Path to your raw dataset
    raw_data_path = "raw_data.csv"  # Replace with your actual file path
    clean_dataset(raw_data_path)