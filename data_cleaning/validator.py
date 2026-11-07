import pandas as pd
import re
from typing import Dict

class DataValidator:
    """Validate data quality and common field formats."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        if pd.isna(email):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email)))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        if pd.isna(phone):
            return False
        cleaned = re.sub(r'[\s\-\(\)\.]', '', str(phone))
        return cleaned.isdigit() and len(cleaned) >= 10
    
    def validate_column(self, df: pd.DataFrame, column: str, validation_type: str) -> Dict:
        if column not in df.columns:
            return {'valid': False, 'errors': f"Column '{column}' not found"}
        
        valid_count = 0
        invalid_count = 0
        
        for idx, value in df[column].items():
            is_valid = False
            if validation_type == 'email':
                is_valid = self.validate_email(value)
            elif validation_type == 'phone':
                is_valid = self.validate_phone(value)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        return {
            'column': column,
            'validation_type': validation_type,
            'total_values': len(df),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'valid_percentage': round((valid_count / len(df)) * 100, 2)
        }