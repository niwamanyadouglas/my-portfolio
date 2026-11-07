import pandas as pd
import numpy as np
from typing import Dict, Any

class DataAnalyzer:
    """Generate statistics and insights about the dataset."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive summary statistics."""
        return {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'total_cells': len(self.df) * len(self.df.columns),
            'duplicate_rows': int(self.df.duplicated().sum()),
            'missing_values': {
                'total': int(self.df.isna().sum().sum()),
                'by_column': self.df.isna().sum().to_dict()
            },
            'data_types': {k: str(v) for k, v in self.df.dtypes.to_dict().items()},
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / 1024**2, 2)
        }
    
    def get_quality_score(self) -> float:
        """Calculate a data quality score (0-100)."""
        total_cells = self.df.size
        if total_cells == 0:
            return 0.0
        
        missing_penalty = (self.df.isna().sum().sum() / total_cells) * 40
        duplicate_penalty = (self.df.duplicated().sum() / len(self.df)) * 30
        
        score = 100 - missing_penalty - duplicate_penalty
        return round(max(0, min(100, score)), 2)