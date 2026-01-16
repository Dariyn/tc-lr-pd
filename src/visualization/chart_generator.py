"""
Chart generation module for creating publication-ready visualizations.

This module provides the ChartGenerator class for creating static charts
(PNG/SVG) from analysis results. Charts are professional quality with
proper styling, labels, and legends suitable for stakeholder presentations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Union, Literal, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generate static charts for equipment analysis visualizations.

    Creates publication-ready charts in PNG or SVG format with professional
    styling, proper labels, legends, and formatting.
    """

    # Professional color scheme
    COLORS = {
        'primary': '#1f4788',  # Dark blue
        'secondary': '#f57c00',  # Orange
        'success': '#4caf50',  # Green
        'danger': '#f44336',  # Red
        'gray': '#757575',  # Gray
        'light_gray': '#f0f0f0',  # Light gray for alternating rows
    }

    # Category colors for equipment
    CATEGORY_COLORS = {
        'default': '#1f4788',
    }

    # Failure pattern category colors
    FAILURE_CATEGORY_COLORS = {
        'leak': '#2196f3',  # Blue
        'electrical': '#ff9800',  # Orange
        'mechanical': '#4caf50',  # Green
        'other': '#757575',  # Gray
    }

    def __init__(self, style: str = 'default', dpi: int = 300):
        """
        Initialize ChartGenerator with style and quality settings.

        Args:
            style: Matplotlib style to use (default: 'default')
            dpi: Dots per inch for output quality (default: 300 for print quality)
        """
        self.style = style
        self.dpi = dpi

        # Set matplotlib style
        if style != 'default':
            plt.style.use(style)

    def create_equipment_ranking_chart(
        self,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        top_n: int = 10,
        format: Literal['png', 'svg'] = 'png'
    ) -> None:
        """
        Create horizontal bar chart of top equipment by maintenance priority.

        Args:
            df: DataFrame with columns: equipment_name, priority_score,
                work_order_count, equipment_primary_category
            output_path: Path to save the chart
            top_n: Number of top equipment to display (default: 10)
            format: Output format - 'png' or 'svg' (default: 'png')
        """
        # Handle edge cases
        if df is None or len(df) == 0:
            logger.warning("Empty DataFrame provided for equipment ranking chart")
            self._create_empty_chart(output_path, "No equipment data available", format)
            return

        # Validate required columns
        required_cols = ['priority_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            self._create_empty_chart(output_path, f"Missing columns: {', '.join(missing_cols)}", format)
            return

        # Get top N equipment
        df_plot = df.head(min(top_n, len(df))).copy()

        # Use Equipment_ID if equipment_name not available
        if 'equipment_name' in df_plot.columns:
            name_col = 'equipment_name'
        elif 'Equipment_ID' in df_plot.columns:
            name_col = 'Equipment_ID'
        else:
            df_plot['name'] = [f"Equipment {i+1}" for i in range(len(df_plot))]
            name_col = 'name'

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Get colors by category if available
        if 'equipment_primary_category' in df_plot.columns:
            categories = df_plot['equipment_primary_category'].unique()
            category_colors = {}
            colors_list = ['#1f4788', '#f57c00', '#4caf50', '#9c27b0', '#00bcd4', '#ff5722']
            for i, cat in enumerate(categories):
                category_colors[cat] = colors_list[i % len(colors_list)]
            bar_colors = [category_colors[cat] for cat in df_plot['equipment_primary_category']]
        else:
            bar_colors = self.COLORS['primary']

        # Create horizontal bar chart (reverse order for top-to-bottom display)
        y_pos = range(len(df_plot))
        bars = ax.barh(y_pos, df_plot['priority_score'], color=bar_colors)

        # Add data labels (work order count if available)
        if 'work_order_count' in df_plot.columns:
            for i, (idx, row) in enumerate(df_plot.iterrows()):
                wo_count = int(row['work_order_count'])
                ax.text(
                    row['priority_score'] + 0.01,
                    i,
                    f"{wo_count} WOs",
                    va='center',
                    fontsize=9,
                    color='#333333'
                )

        # Set labels and title
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_plot[name_col])
        ax.set_xlabel('Priority Score', fontsize=11, fontweight='bold')
        ax.set_title('Top Equipment by Maintenance Priority', fontsize=14, fontweight='bold', pad=20)

        # Add grid for readability
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Invert y-axis to show highest priority at top
        ax.invert_yaxis()

        # Adjust layout
        plt.tight_layout()

        # Save chart
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, format=format, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Equipment ranking chart saved to {output_path}")

    def _create_empty_chart(
        self,
        output_path: Union[str, Path],
        message: str,
        format: Literal['png', 'svg'] = 'png'
    ) -> None:
        """
        Create a placeholder chart for empty data.

        Args:
            output_path: Path to save the chart
            message: Message to display
            format: Output format - 'png' or 'svg'
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(
            0.5, 0.5, message,
            ha='center', va='center',
            fontsize=14, color='#757575',
            transform=ax.transAxes
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, format=format, dpi=self.dpi, bbox_inches='tight')
        plt.close()
