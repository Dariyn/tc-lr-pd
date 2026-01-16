"""
Chart generation module for creating publication-ready visualizations.

This module provides the ChartGenerator class for creating static charts
(PNG/SVG) from analysis results. Charts are professional quality with
proper styling, labels, and legends suitable for stakeholder presentations.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
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

    def create_seasonal_trend_chart(
        self,
        patterns_dict: Dict,
        output_path: Union[str, Path],
        format: Literal['png', 'svg'] = 'png'
    ) -> None:
        """
        Create line chart showing seasonal cost and work order trends.

        Args:
            patterns_dict: Dictionary with 'monthly' key containing DataFrame
                          with columns: period, total_cost, work_order_count
            output_path: Path to save the chart
            format: Output format - 'png' or 'svg' (default: 'png')
        """
        # Handle edge cases
        if not patterns_dict or 'monthly' not in patterns_dict:
            logger.warning("No monthly data in patterns dictionary")
            self._create_empty_chart(output_path, "No seasonal data available", format)
            return

        df = patterns_dict['monthly']

        if df is None or len(df) == 0:
            logger.warning("Empty monthly DataFrame")
            self._create_empty_chart(output_path, "No seasonal data available", format)
            return

        # Validate required columns
        if 'period' not in df.columns or 'total_cost' not in df.columns:
            logger.error("Missing required columns (period, total_cost)")
            self._create_empty_chart(output_path, "Missing required data columns", format)
            return

        # Handle single data point
        if len(df) == 1:
            logger.warning("Only single data point for seasonal trend")

        # Create figure with dual y-axes
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Month order for proper sorting
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']

        # Sort by month order
        df_plot = df.copy()
        df_plot['month_num'] = df_plot['period'].apply(
            lambda x: month_order.index(x) if x in month_order else -1
        )
        df_plot = df_plot.sort_values('month_num')

        # Plot total cost on primary y-axis
        color1 = self.COLORS['primary']
        ax1.plot(df_plot['period'], df_plot['total_cost'],
                color=color1, linewidth=2, marker='o', label='Total Cost')
        ax1.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Total Cost ($)', fontsize=11, fontweight='bold', color=color1)
        ax1.tick_params(axis='y', labelcolor=color1)

        # Format y-axis as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        # Plot work order count on secondary y-axis if available
        if 'work_order_count' in df_plot.columns:
            ax2 = ax1.twinx()
            color2 = self.COLORS['secondary']
            ax2.plot(df_plot['period'], df_plot['work_order_count'],
                    color=color2, linewidth=2, linestyle='--', marker='s',
                    label='Work Order Count')
            ax2.set_ylabel('Work Order Count', fontsize=11, fontweight='bold', color=color2)
            ax2.tick_params(axis='y', labelcolor=color2)

            # Add combined legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        else:
            ax1.legend(loc='upper right')

        # Set title
        ax1.set_title('Seasonal Cost and Work Order Trends', fontsize=14, fontweight='bold', pad=20)

        # Add grid
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_axisbelow(True)

        # Rotate x-axis labels for readability
        plt.xticks(rotation=45, ha='right')

        # Adjust layout
        plt.tight_layout()

        # Save chart
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, format=format, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Seasonal trend chart saved to {output_path}")

    def create_vendor_performance_chart(
        self,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        top_n: int = 10,
        format: Literal['png', 'svg'] = 'png'
    ) -> None:
        """
        Create grouped bar chart comparing vendor performance metrics.

        Args:
            df: DataFrame with columns: contractor, total_cost, avg_cost_per_wo,
                cost_per_day (optional)
            output_path: Path to save the chart
            top_n: Number of top vendors to display (default: 10)
            format: Output format - 'png' or 'svg' (default: 'png')
        """
        # Handle edge cases
        if df is None or len(df) == 0:
            logger.warning("Empty DataFrame for vendor performance chart")
            self._create_empty_chart(output_path, "No vendor data available", format)
            return

        # Validate required columns
        required_cols = ['contractor', 'total_cost']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            self._create_empty_chart(output_path, f"Missing columns: {', '.join(missing_cols)}", format)
            return

        # Handle single vendor
        if len(df) == 1:
            logger.info("Single vendor in dataset")

        # Get top N vendors
        df_plot = df.head(min(top_n, len(df))).copy()

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))

        # Prepare data for grouped bars
        x = range(len(df_plot))
        width = 0.25

        # Plot total cost
        bars1 = ax.bar([i - width for i in x], df_plot['total_cost'],
                      width, label='Total Cost', color=self.COLORS['primary'])

        # Plot average cost if available
        if 'avg_cost_per_wo' in df_plot.columns:
            # Normalize avg_cost to similar scale as total_cost for visibility
            max_total = df_plot['total_cost'].max()
            max_avg = df_plot['avg_cost_per_wo'].max()
            scale_factor = max_total / max_avg if max_avg > 0 else 1

            bars2 = ax.bar(x, df_plot['avg_cost_per_wo'] * scale_factor,
                         width, label=f'Avg Cost (scaled)', color=self.COLORS['secondary'])

        # Plot cost efficiency if available
        if 'cost_per_day' in df_plot.columns:
            max_eff = df_plot['cost_per_day'].max()
            eff_scale_factor = max_total / max_eff if max_eff > 0 else 1

            bars3 = ax.bar([i + width for i in x], df_plot['cost_per_day'] * eff_scale_factor,
                         width, label='Cost Efficiency (scaled)', color=self.COLORS['success'])

        # Set labels and title
        ax.set_xlabel('Vendor', fontsize=11, fontweight='bold')
        ax.set_ylabel('Cost ($)', fontsize=11, fontweight='bold')
        ax.set_title('Vendor Cost Performance Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(df_plot['contractor'], rotation=45, ha='right')

        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        # Add legend
        ax.legend(loc='upper right')

        # Add grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Adjust layout
        plt.tight_layout()

        # Save chart
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, format=format, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Vendor performance chart saved to {output_path}")

    def create_failure_pattern_chart(
        self,
        patterns_list: list,
        output_path: Union[str, Path],
        top_n: int = 10,
        format: Literal['png', 'svg'] = 'png'
    ) -> None:
        """
        Create horizontal bar chart of top failure patterns by impact score.

        Args:
            patterns_list: List of dictionaries with keys: pattern, impact_score,
                          occurrences, category
            output_path: Path to save the chart
            top_n: Number of top patterns to display (default: 10)
            format: Output format - 'png' or 'svg' (default: 'png')
        """
        # Handle edge cases
        if not patterns_list or len(patterns_list) == 0:
            logger.warning("Empty patterns list for failure pattern chart")
            self._create_empty_chart(output_path, "No failure pattern data available", format)
            return

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(patterns_list)

        # Validate required columns
        if 'pattern' not in df.columns or 'impact_score' not in df.columns:
            logger.error("Missing required columns (pattern, impact_score)")
            self._create_empty_chart(output_path, "Missing required data columns", format)
            return

        # Get top N patterns
        df_plot = df.head(min(top_n, len(df))).copy()

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Get colors by category if available
        if 'category' in df_plot.columns:
            bar_colors = [
                self.FAILURE_CATEGORY_COLORS.get(cat, self.FAILURE_CATEGORY_COLORS['other'])
                for cat in df_plot['category']
            ]
        else:
            bar_colors = self.COLORS['primary']

        # Create horizontal bar chart (reverse order for top-to-bottom display)
        y_pos = range(len(df_plot))
        bars = ax.barh(y_pos, df_plot['impact_score'], color=bar_colors)

        # Add annotation showing frequency count if available
        if 'occurrences' in df_plot.columns:
            for i, (idx, row) in enumerate(df_plot.iterrows()):
                count = int(row['occurrences'])
                ax.text(
                    row['impact_score'] + (row['impact_score'] * 0.02),
                    i,
                    f"{count}x",
                    va='center',
                    fontsize=9,
                    color='#333333'
                )

        # Set labels and title
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_plot['pattern'])
        ax.set_xlabel('Impact Score', fontsize=11, fontweight='bold')
        ax.set_title('High-Impact Failure Patterns', fontsize=14, fontweight='bold', pad=20)

        # Add grid for readability
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Invert y-axis to show highest impact at top
        ax.invert_yaxis()

        # Add legend for categories if present
        if 'category' in df_plot.columns:
            unique_categories = df_plot['category'].unique()
            legend_patches = [
                mpatches.Patch(
                    color=self.FAILURE_CATEGORY_COLORS.get(cat, self.FAILURE_CATEGORY_COLORS['other']),
                    label=cat.capitalize()
                )
                for cat in unique_categories
            ]
            ax.legend(handles=legend_patches, loc='lower right')

        # Adjust layout
        plt.tight_layout()

        # Save chart
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, format=format, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Failure pattern chart saved to {output_path}")

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
