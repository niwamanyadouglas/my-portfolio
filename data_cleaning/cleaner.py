import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

class DataCleaner:
    """Advanced data cleaning engine with configurable options."""
    
    def __init__(self, df: pd.DataFrame):
        self.original_df = df.copy()
        self.df = df.copy()
        self.cleaning_log = []
    
    def log_action(self, action: str, details: str):
        """Record cleaning actions for the report."""
        self.cleaning_log.append({
            'action': action,
            'details': details
        })
    
    def standardize_columns(self) -> pd.DataFrame:
        """Standardize column names: lowercase, underscores, no special chars."""
        original_cols = self.df.columns.tolist()
        self.df.columns = (
            self.df.columns
            .str.lower()
            .str.replace(r'\s+', '_', regex=True)
            .str.replace(r'[^a-z0-9_]', '', regex=True)
        )
        changed_cols = sum(1 for o, n in zip(original_cols, self.df.columns) if o != n)
        self.log_action(
            'Column Standardization',
            f'Standardized {changed_cols} column names to lowercase with underscores'
        )
        return self.df
    
    def remove_duplicates(self, subset: Optional[list] = None) -> pd.DataFrame:
        """Remove duplicate rows."""
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset)
        removed_count = initial_count - len(self.df)
        self.log_action(
            'Duplicate Removal',
            f'Removed {removed_count} duplicate rows'
        )
        return self.df
    
    def drop_sparse_columns(self, threshold: float = 0.5) -> pd.DataFrame:
        """Drop columns with excessive missing values. MUST be called BEFORE filling."""
        initial_cols = len(self.df.columns)
        cols_to_drop = []
        
        for col in self.df.columns:
            missing_pct = self.df[col].isna().sum() / len(self.df)
            if missing_pct > threshold:
                cols_to_drop.append(col)
        
        self.df = self.df.drop(columns=cols_to_drop)
        self.log_action(
            'Sparse Column Removal',
            f'Dropped {len(cols_to_drop)} columns with >{threshold*100}% missing values: {", ".join(cols_to_drop)}'
        )
        return self.df
    
    def fill_missing_values(
        self,
        numeric_strategy: str = 'mean',
        categorical_strategy: str = 'mode'
    ) -> pd.DataFrame:
        """Fill missing values. MUST be called AFTER dropping sparse columns."""
        fill_log = []
        
        # Numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if self.df[col].isna().sum() > 0:
                if numeric_strategy == 'mean':
                    fill_value = self.df[col].mean()
                elif numeric_strategy == 'median':
                    fill_value = self.df[col].median()
                else:
                    fill_value = 0
                
                self.df[col] = self.df[col].fillna(fill_value)
                fill_log.append(f"{col} -> {numeric_strategy} ({fill_value:.2f})")
        
        # Categorical columns
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if self.df[col].isna().sum() > 0:
                if categorical_strategy == 'mode':
                    mode_val = self.df[col].mode()
                    fill_value = mode_val[0] if len(mode_val) > 0 else 'Unknown'
                else:
                    fill_value = 'Unknown'
                
                self.df[col] = self.df[col].fillna(fill_value)
                fill_log.append(f"{col} -> {categorical_strategy} ('{fill_value}')")
        
        self.log_action(
            'Missing Value Imputation',
            f'Filled missing values: {", ".join(fill_log)}'
        )
        return self.df
    
    def clean_all(self) -> pd.DataFrame:
        """Execute the complete cleaning pipeline in the CORRECT order."""
        self.standardize_columns()
        self.remove_duplicates()
        self.drop_sparse_columns(threshold=0.5)
        self.fill_missing_values(numeric_strategy='mean', categorical_strategy='mode')
        return self.df
    
    def get_cleaning_report(self) -> str:
        """Generate a text report of all cleaning actions."""
        report = ["=== DATA CLEANING REPORT ===\n"]
        for i, entry in enumerate(self.cleaning_log, 1):
            report.append(f"{i}. {entry['action']}: {entry['details']}")
        report.append(f"\nFinal dataset: {len(self.df)} rows, {len(self.df.columns)} columns")
        return "\n".join(report)