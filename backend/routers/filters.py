"""
Filter endpoints providing dynamic date bounds and distinct dimensions.
"""

from functools import lru_cache
from fastapi import APIRouter
from src.db import query_df

router = APIRouter(prefix="/api/filters", tags=["Filters"])

@lru_cache(maxsize=1)
def _fetch_filters_cached():
    date_bounds = query_df("SELECT MIN(Transaction_Date) AS min_d, MAX(Transaction_Date) AS max_d FROM vw_line_margin;").iloc[0]
    categories = query_df("SELECT DISTINCT Product_Category FROM Dim_Product ORDER BY 1;")['Product_Category'].tolist()
    segments = query_df("SELECT DISTINCT Customer_Segment FROM Dim_Customer ORDER BY 1;")['Customer_Segment'].tolist()
    regions = query_df("SELECT DISTINCT Sales_Region FROM Dim_Customer ORDER BY 1;")['Sales_Region'].tolist()
    
    return {
        "date_bounds": {
            "min_date": str(date_bounds['min_d']),
            "max_date": str(date_bounds['max_d'])
        },
        "categories": categories,
        "segments": segments,
        "regions": regions
    }

@router.get("")
def get_filters():
    return _fetch_filters_cached()
