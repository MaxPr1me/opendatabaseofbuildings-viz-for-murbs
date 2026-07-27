"""Excel workbook generation module — formatted reports with openpyxl.

Generates structured Excel workbooks with standard sheets for
data quality, MURB summaries, regional comparisons, and archetypes.
"""

from murb_geometry.excel.workbook import create_summary_workbook

__all__ = ["create_summary_workbook"]
