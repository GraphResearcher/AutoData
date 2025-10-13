"""
CSV Exporter Tool - Export data ra CSV files.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

from core.config import config
from core.types import ToolResult, Comment

logger = logging.getLogger(__name__)


class CSVExporterTool:
    """Tool để export data ra CSV"""

    def __init__(self):
        self.csv_dir = config.CSV_DIR
        self.encoding = config.CSV_ENCODING
        self.delimiter = config.CSV_DELIMITER

    def export_comments(self, comments: List[Comment], filename: str = None) -> ToolResult:
        """
        Export comments ra CSV file.

        Args:
            comments: Danh sách Comments
            filename: Tên file CSV (optional)

        Returns:
            ToolResult với đường dẫn file CSV
        """
        try:
            if not comments:
                return ToolResult(
                    success=False,
                    error="No comments to export"
                )

            # Generate filename nếu không có
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"comments_{timestamp}.csv"

            if not filename.endswith('.csv'):
                filename += '.csv'

            filepath = self.csv_dir / filename

            # Convert comments to dict
            data = [comment.to_dict() for comment in comments]

            # Create DataFrame
            df = pd.DataFrame(data)

            # Reorder columns
            column_order = ['source', 'author', 'content', 'timestamp', 'likes', 'replies', 'sentiment', 'source_url']
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]

            # Export to CSV
            df.to_csv(
                filepath,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter
            )

            logger.info(f"Exported {len(comments)} comments to {filepath}")

            return ToolResult(
                success=True,
                data={
                    'filepath': str(filepath),
                    'filename': filename,
                    'count': len(comments),
                    'file_size': filepath.stat().st_size
                }
            )

        except Exception as e:
            logger.error(f"CSV export error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to export CSV: {str(e)}"
            )

    def export_dataframe(self, df: pd.DataFrame, filename: str) -> ToolResult:
        """
        Export pandas DataFrame ra CSV.

        Args:
            df: DataFrame cần export
            filename: Tên file CSV

        Returns:
            ToolResult với đường dẫn file
        """
        try:
            if not filename.endswith('.csv'):
                filename += '.csv'

            filepath = self.csv_dir / filename

            df.to_csv(
                filepath,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter
            )

            logger.info(f"Exported DataFrame to {filepath}")

            return ToolResult(
                success=True,
                data={
                    'filepath': str(filepath),
                    'filename': filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'file_size': filepath.stat().st_size
                }
            )

        except Exception as e:
            logger.error(f"DataFrame export error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to export DataFrame: {str(e)}"
            )

    def export_dict_list(self, data: List[Dict[str, Any]], filename: str) -> ToolResult:
        """
        Export danh sách dictionaries ra CSV.

        Args:
            data: Danh sách dictionaries
            filename: Tên file CSV

        Returns:
            ToolResult với đường dẫn file
        """
        try:
            df = pd.DataFrame(data)
            return self.export_dataframe(df, filename)
        except Exception as e:
            logger.error(f"Dict list export error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to export dict list: {str(e)}"
            )

    def append_to_csv(self, data: List[Dict[str, Any]], filename: str) -> ToolResult:
        """
        Append data vào CSV file có sẵn.

        Args:
            data: Data cần append
            filename: Tên file CSV

        Returns:
            ToolResult
        """
        try:
            if not filename.endswith('.csv'):
                filename += '.csv'

            filepath = self.csv_dir / filename

            df_new = pd.DataFrame(data)

            if filepath.exists():
                # Read existing CSV
                df_existing = pd.read_csv(filepath, encoding=self.encoding, sep=self.delimiter)
                # Append
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new

            # Save
            df_combined.to_csv(
                filepath,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter
            )

            logger.info(f"Appended {len(data)} rows to {filepath}")

            return ToolResult(
                success=True,
                data={
                    'filepath': str(filepath),
                    'appended_rows': len(data),
                    'total_rows': len(df_combined)
                }
            )

        except Exception as e:
            logger.error(f"Append CSV error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to append to CSV: {str(e)}"
            )

    def read_csv(self, filename: str) -> ToolResult:
        """
        Đọc CSV file.

        Args:
            filename: Tên file CSV

        Returns:
            ToolResult với DataFrame
        """
        try:
            if not filename.endswith('.csv'):
                filename += '.csv'

            filepath = self.csv_dir / filename

            if not filepath.exists():
                return ToolResult(
                    success=False,
                    error=f"CSV file not found: {filename}"
                )

            df = pd.read_csv(filepath, encoding=self.encoding, sep=self.delimiter)

            logger.info(f"Read CSV: {filepath} ({len(df)} rows)")

            return ToolResult(
                success=True,
                data={
                    'dataframe': df,
                    'rows': len(df),
                    'columns': list(df.columns)
                }
            )

        except Exception as e:
            logger.error(f"Read CSV error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to read CSV: {str(e)}"
            )


# Singleton instance
csv_exporter_tool = CSVExporterTool()