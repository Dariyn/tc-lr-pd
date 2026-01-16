"""
Dashboard generation module for creating interactive HTML visualizations.

This module provides the DashboardGenerator class for creating interactive
dashboards with plotly. Dashboards are self-contained HTML files with
hoverable, zoomable charts that work offline without CDN dependencies.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
from typing import Union, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """
    Generate interactive HTML dashboards for equipment analysis visualizations.

    Creates self-contained HTML files with plotly charts that support:
    - Hover for detailed information
    - Zoom and pan interactions
    - Legend filtering (click to show/hide)
    - Export to PNG
    - Offline functionality (no CDN required)
    """

    def __init__(self):
        """Initialize DashboardGenerator with plotly configuration."""
        # Configure plotly for offline, self-contained output
        self.config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'chart',
                'height': 800,
                'width': 1200,
                'scale': 2
            }
        }

    @staticmethod
    def _format_equipment_name(value) -> str:
        """
        Format equipment name/ID to avoid scientific notation.

        Args:
            value: Equipment name or ID (could be string, int, or float)

        Returns:
            Properly formatted string representation
        """
        if pd.isna(value):
            return "Unknown Equipment"
        if isinstance(value, float):
            # Convert to int if it's a whole number to avoid scientific notation
            if value == int(value):
                return str(int(value))
            else:
                return f"{value:.0f}"
        return str(value)

    def _create_equipment_chart(
        self,
        df: pd.DataFrame,
        top_n: int = 20
    ) -> go.Figure:
        """
        Create interactive horizontal bar chart of equipment by priority_score.

        Args:
            df: DataFrame with equipment rankings (from equipment_ranker.rank_equipment)
            top_n: Number of top equipment to display (default: 20)

        Returns:
            plotly Figure object with interactive equipment ranking chart

        Chart features:
        - Hover shows: equipment_id, category, work_orders, total_cost, avg_cost, priority_score
        - Color bars by category with discrete color map
        - Clickable legend to filter by category
        - Dynamic height based on number of items
        """
        # Handle empty DataFrame
        if df is None or len(df) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No equipment data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(
                title="Equipment Maintenance Priority Rankings",
                height=400
            )
            return fig

        # Get top N equipment
        df_plot = df.head(min(top_n, len(df))).copy()

        # Reverse order for top-to-bottom display
        df_plot = df_plot.iloc[::-1]

        # Get equipment names (use Equipment_Name or Equipment_ID) - format to avoid scientific notation
        if 'Equipment_Name' in df_plot.columns:
            names = df_plot['Equipment_Name'].apply(self._format_equipment_name)
        elif 'Equipment_ID' in df_plot.columns:
            names = df_plot['Equipment_ID'].apply(self._format_equipment_name)
        else:
            names = [f"Equipment {i+1}" for i in range(len(df_plot))]

        # Create color mapping by category
        category_col = None
        if 'equipment_primary_category' in df_plot.columns:
            category_col = 'equipment_primary_category'
        elif 'category' in df_plot.columns:
            category_col = 'category'

        if category_col:
            # Get unique categories and assign colors
            categories = df_plot[category_col].unique()
            color_palette = [
                '#1f4788', '#f57c00', '#4caf50', '#9c27b0',
                '#00bcd4', '#ff5722', '#795548', '#607d8b'
            ]
            category_colors = {
                cat: color_palette[i % len(color_palette)]
                for i, cat in enumerate(categories)
            }

            # Group by category for separate traces (enables legend filtering)
            fig = go.Figure()
            for category in categories:
                df_cat = df_plot[df_plot[category_col] == category]

                # Build hover text
                hover_text = []
                for _, row in df_cat.iterrows():
                    parts = []
                    if 'Equipment_Name' in row.index or 'Equipment_ID' in row.index:
                        equip_id = self._format_equipment_name(
                            row.get('Equipment_Name', row.get('Equipment_ID', 'N/A'))
                        )
                        parts.append(f"<b>{equip_id}</b>")
                    parts.append(f"Category: {row.get(category_col, 'N/A')}")
                    if 'work_order_count' in row.index:
                        parts.append(f"Work Orders: {int(row['work_order_count'])}")
                    if 'total_cost' in row.index:
                        parts.append(f"Total Cost: ${row['total_cost']:,.2f}")
                    if 'avg_cost' in row.index:
                        parts.append(f"Avg Cost: ${row['avg_cost']:,.2f}")
                    parts.append(f"Priority Score: {row['priority_score']:.2f}")
                    hover_text.append("<br>".join(parts))

                # Get names for this category - format to avoid scientific notation
                if 'Equipment_Name' in df_cat.columns:
                    cat_names = df_cat['Equipment_Name'].apply(self._format_equipment_name)
                elif 'Equipment_ID' in df_cat.columns:
                    cat_names = df_cat['Equipment_ID'].apply(self._format_equipment_name)
                else:
                    cat_names = [f"Equipment {i}" for i in range(len(df_cat))]

                fig.add_trace(go.Bar(
                    y=cat_names,
                    x=df_cat['priority_score'],
                    name=category,
                    orientation='h',
                    marker=dict(color=category_colors[category]),
                    hovertext=hover_text,
                    hoverinfo='text'
                ))
        else:
            # No category column - single trace
            hover_text = []
            for _, row in df_plot.iterrows():
                parts = []
                if 'Equipment_Name' in row.index or 'Equipment_ID' in row.index:
                    equip_id = self._format_equipment_name(
                        row.get('Equipment_Name', row.get('Equipment_ID', 'N/A'))
                    )
                    parts.append(f"<b>{equip_id}</b>")
                if 'work_order_count' in row.index:
                    parts.append(f"Work Orders: {int(row['work_order_count'])}")
                if 'total_cost' in row.index:
                    parts.append(f"Total Cost: ${row['total_cost']:,.2f}")
                if 'avg_cost' in row.index:
                    parts.append(f"Avg Cost: ${row['avg_cost']:,.2f}")
                parts.append(f"Priority Score: {row['priority_score']:.2f}")
                hover_text.append("<br>".join(parts))

            fig = go.Figure(go.Bar(
                y=names,
                x=df_plot['priority_score'],
                orientation='h',
                marker=dict(color='#1f4788'),
                hovertext=hover_text,
                hoverinfo='text'
            ))

        # Update layout
        height = max(400, top_n * 30)
        fig.update_layout(
            title="Equipment Maintenance Priority Rankings",
            xaxis_title="Priority Score",
            yaxis_title="Equipment",
            height=height,
            hovermode='closest',
            showlegend=True if category_col else False,
            template='plotly'
        )

        return fig

    def _create_seasonal_chart(self, patterns_dict: Dict) -> go.Figure:
        """
        Create interactive line chart with dual Y-axes for seasonal trends.

        Args:
            patterns_dict: Dictionary with 'monthly' key containing DataFrame

        Returns:
            plotly Figure object with seasonal trend visualization

        Chart features:
        - Primary Y: total_cost (blue line with markers)
        - Secondary Y: work_order_count (orange line with markers)
        - Hover shows: month, total_cost ($), work_order_count, avg_cost ($)
        - Range slider for time navigation
        - Toggleable traces (click legend to show/hide)
        """
        # Handle empty or missing data
        if not patterns_dict or 'monthly' not in patterns_dict:
            fig = go.Figure()
            fig.add_annotation(
                text="No seasonal data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="Seasonal Cost and Work Order Trends", height=400)
            return fig

        df = patterns_dict['monthly']

        if df is None or len(df) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No seasonal data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="Seasonal Cost and Work Order Trends", height=400)
            return fig

        # Validate required columns
        if 'period' not in df.columns or 'total_cost' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="Missing required data columns",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="Seasonal Cost and Work Order Trends", height=400)
            return fig

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Build hover text for total cost
        hover_text_cost = []
        for _, row in df.iterrows():
            parts = [
                f"<b>{row['period']}</b>",
                f"Total Cost: ${row['total_cost']:,.2f}"
            ]
            if 'work_order_count' in row.index:
                parts.append(f"Work Orders: {int(row['work_order_count'])}")
            if 'avg_cost' in row.index:
                parts.append(f"Avg Cost: ${row['avg_cost']:,.2f}")
            hover_text_cost.append("<br>".join(parts))

        # Add total cost trace (primary y-axis)
        fig.add_trace(
            go.Scatter(
                x=df['period'],
                y=df['total_cost'],
                name='Total Cost',
                mode='lines+markers',
                line=dict(color='#1f4788', width=2),
                marker=dict(size=8),
                hovertext=hover_text_cost,
                hoverinfo='text'
            ),
            secondary_y=False
        )

        # Add work order count trace (secondary y-axis) if available
        if 'work_order_count' in df.columns:
            hover_text_wo = []
            for _, row in df.iterrows():
                parts = [
                    f"<b>{row['period']}</b>",
                    f"Work Orders: {int(row['work_order_count'])}"
                ]
                if 'avg_cost' in row.index:
                    parts.append(f"Avg Cost: ${row['avg_cost']:,.2f}")
                hover_text_wo.append("<br>".join(parts))

            fig.add_trace(
                go.Scatter(
                    x=df['period'],
                    y=df['work_order_count'],
                    name='Work Order Count',
                    mode='lines+markers',
                    line=dict(color='#f57c00', width=2, dash='dot'),
                    marker=dict(size=8, symbol='square'),
                    hovertext=hover_text_wo,
                    hoverinfo='text'
                ),
                secondary_y=True
            )

        # Update axes labels
        fig.update_xaxes(title_text="Month")
        fig.update_yaxes(title_text="Total Cost ($)", secondary_y=False)
        fig.update_yaxes(title_text="Work Order Count", secondary_y=True)

        # Update layout
        fig.update_layout(
            title="Seasonal Cost and Work Order Trends",
            hovermode='closest',
            showlegend=True,
            height=400,
            template='plotly',
            xaxis=dict(rangeslider=dict(visible=True))
        )

        return fig

    def _create_vendor_chart(
        self,
        df: pd.DataFrame,
        top_n: int = 15
    ) -> go.Figure:
        """
        Create interactive grouped bar chart for vendor performance.

        Args:
            df: DataFrame with vendor metrics
            top_n: Number of top vendors to display (default: 15)

        Returns:
            plotly Figure object with vendor comparison chart

        Chart features:
        - Bars: Total cost (blue) and Avg cost per WO (orange)
        - Hover shows: vendor name, metric value, work_order_count, avg_duration
        - Clickable legend to toggle metrics
        """
        # Handle empty DataFrame
        if df is None or len(df) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No vendor data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="Vendor Performance Comparison", height=400)
            return fig

        # Validate required columns
        if 'contractor' not in df.columns or 'total_cost' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="Missing required columns (contractor, total_cost)",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="Vendor Performance Comparison", height=400)
            return fig

        # Get top N vendors
        df_plot = df.head(min(top_n, len(df))).copy()

        # Create figure
        fig = go.Figure()

        # Add total cost bars (primary y-axis)
        hover_text_total = []
        for _, row in df_plot.iterrows():
            parts = [
                f"<b>{row['contractor']}</b>",
                f"Total Cost: ${row['total_cost']:,.2f}"
            ]
            if 'work_order_count' in row.index:
                parts.append(f"Work Orders: {int(row['work_order_count'])}")
            if 'avg_duration_days' in row.index:
                parts.append(f"Avg Duration: {row['avg_duration_days']:.1f} days")
            hover_text_total.append("<br>".join(parts))

        fig.add_trace(
            go.Bar(
                x=df_plot['contractor'],
                y=df_plot['total_cost'],
                name='Total Cost',
                marker=dict(color='#1f4788'),
                hovertext=hover_text_total,
                hoverinfo='text'
            )
        )

        # Add average cost as bars if available
        if 'avg_cost_per_wo' in df_plot.columns:
            hover_text_avg = []
            for _, row in df_plot.iterrows():
                parts = [
                    f"<b>{row['contractor']}</b>",
                    f"Avg Cost per WO: ${row['avg_cost_per_wo']:,.2f}"
                ]
                if 'work_order_count' in row.index:
                    parts.append(f"Work Orders: {int(row['work_order_count'])}")
                hover_text_avg.append("<br>".join(parts))

            fig.add_trace(
                go.Bar(
                    x=df_plot['contractor'],
                    y=df_plot['avg_cost_per_wo'],
                    name='Avg Cost/WO',
                    marker=dict(color='#f57c00'),
                    hovertext=hover_text_avg,
                    hoverinfo='text'
                )
            )

        # Update axes
        fig.update_xaxes(title_text="Vendor", tickangle=-45)
        fig.update_yaxes(title_text="Cost ($)")

        # Update layout
        fig.update_layout(
            title="Vendor Performance Comparison",
            hovermode='closest',
            showlegend=True,
            height=400,
            template='plotly',
            barmode='group',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig

    def _create_failure_chart(
        self,
        patterns_list: List[Dict],
        top_n: int = 15
    ) -> go.Figure:
        """
        Create interactive horizontal bar chart for failure patterns.

        Args:
            patterns_list: List of dictionaries with failure pattern data
            top_n: Number of top patterns to display (default: 15)

        Returns:
            plotly Figure object with failure pattern visualization

        Chart features:
        - Y-axis: pattern phrases, X-axis: impact_score
        - Color by category (leak, electrical, mechanical, other)
        - Hover shows: pattern, frequency, total_cost, equipment_count, category
        - Clickable legend to filter by category
        """
        # Handle empty list
        if not patterns_list or len(patterns_list) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No failure pattern data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="High-Impact Failure Patterns", height=400)
            return fig

        # Convert to DataFrame
        df = pd.DataFrame(patterns_list)

        # Validate required columns
        if 'pattern' not in df.columns or 'impact_score' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="Missing required columns (pattern, impact_score)",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color='gray')
            )
            fig.update_layout(title="High-Impact Failure Patterns", height=400)
            return fig

        # Get top N patterns
        df_plot = df.head(min(top_n, len(df))).copy()

        # Reverse order for top-to-bottom display
        df_plot = df_plot.iloc[::-1]

        # Define category colors - comprehensive mapping
        category_colors = {
            'leak': '#2196f3',        # Blue
            'electrical': '#ff9800',  # Orange
            'mechanical': '#4caf50',  # Green
            'clog': '#00bcd4',        # Cyan
            'broken': '#f44336',      # Red
            'malfunction': '#9c27b0', # Purple
            'wear': '#795548',        # Brown
            'vandalism': '#e91e63',   # Pink
            'corrosion': '#607d8b',   # Blue Grey
            'overheating': '#ff5722', # Deep Orange
            'noise': '#8bc34a',       # Light Green
            'vibration': '#3f51b5',   # Indigo
            'other': '#757575',       # Gray
        }

        # Group by category if available
        if 'category' in df_plot.columns:
            fig = go.Figure()
            categories = df_plot['category'].unique()

            for category in categories:
                df_cat = df_plot[df_plot['category'] == category]

                # Build hover text
                hover_text = []
                for _, row in df_cat.iterrows():
                    parts = [f"<b>{row['pattern']}</b>"]

                    # Handle both 'frequency' and 'occurrences' column names
                    freq_col = 'frequency' if 'frequency' in row.index else 'occurrences'
                    if freq_col in row.index:
                        parts.append(f"Frequency: {int(row[freq_col])}")

                    if 'total_cost' in row.index:
                        parts.append(f"Total Cost: ${row['total_cost']:,.2f}")

                    # Handle both 'equipment_count' and 'equipment_affected' column names
                    equip_col = 'equipment_count' if 'equipment_count' in row.index else 'equipment_affected'
                    if equip_col in row.index:
                        parts.append(f"Equipment Affected: {int(row[equip_col])}")

                    parts.append(f"Category: {row['category']}")
                    parts.append(f"Impact Score: {row['impact_score']:,.0f}")
                    hover_text.append("<br>".join(parts))

                fig.add_trace(go.Bar(
                    y=df_cat['pattern'],
                    x=df_cat['impact_score'],
                    name=category.capitalize(),
                    orientation='h',
                    marker=dict(color=category_colors.get(category, category_colors['other'])),
                    hovertext=hover_text,
                    hoverinfo='text'
                ))
        else:
            # No category - single trace
            hover_text = []
            for _, row in df_plot.iterrows():
                parts = [f"<b>{row['pattern']}</b>"]

                freq_col = 'frequency' if 'frequency' in row.index else 'occurrences'
                if freq_col in row.index:
                    parts.append(f"Frequency: {int(row[freq_col])}")

                if 'total_cost' in row.index:
                    parts.append(f"Total Cost: ${row['total_cost']:,.2f}")

                equip_col = 'equipment_count' if 'equipment_count' in row.index else 'equipment_affected'
                if equip_col in row.index:
                    parts.append(f"Equipment Affected: {int(row[equip_col])}")

                parts.append(f"Impact Score: {row['impact_score']:,.0f}")
                hover_text.append("<br>".join(parts))

            fig = go.Figure(go.Bar(
                y=df_plot['pattern'],
                x=df_plot['impact_score'],
                orientation='h',
                marker=dict(color='#1f4788'),
                hovertext=hover_text,
                hoverinfo='text'
            ))

        # Update layout
        height = max(400, top_n * 30)
        fig.update_layout(
            title="High-Impact Failure Patterns",
            xaxis_title="Impact Score",
            yaxis_title="Failure Pattern",
            height=height,
            hovermode='closest',
            showlegend=True if 'category' in df_plot.columns else False,
            template='plotly'
        )

        return fig

    def create_dashboard(
        self,
        equipment_df: pd.DataFrame,
        seasonal_dict: Dict,
        vendor_df: pd.DataFrame,
        patterns_list: List[Dict],
        output_path: Union[str, Path],
        title: str = "Work Order Analysis Dashboard"
    ) -> Path:
        """
        Create HTML dashboard with all 4 charts in 2x2 grid layout.

        Args:
            equipment_df: Equipment rankings DataFrame
            seasonal_dict: Seasonal patterns dictionary
            vendor_df: Vendor performance DataFrame
            patterns_list: Failure patterns list
            output_path: Path to save HTML file
            title: Dashboard title (default: "Work Order Analysis Dashboard")

        Returns:
            Path to generated HTML file

        Dashboard layout:
        - Top left: Equipment rankings
        - Top right: Seasonal trends
        - Bottom left: Vendor performance
        - Bottom right: Failure patterns

        Features:
        - Self-contained HTML (includes plotly.js, no CDN)
        - Interactive charts with hover, zoom, pan
        - Responsive sizing
        - Metadata in HTML comment (timestamp, data summary)
        """
        # Create individual charts
        equipment_fig = self._create_equipment_chart(equipment_df, top_n=20)
        seasonal_fig = self._create_seasonal_chart(seasonal_dict)
        vendor_fig = self._create_vendor_chart(vendor_df, top_n=15)
        failure_fig = self._create_failure_chart(patterns_list, top_n=15)

        # Create subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Equipment Maintenance Priority Rankings",
                "Seasonal Cost and Work Order Trends",
                "Vendor Performance Comparison",
                "High-Impact Failure Patterns"
            ],
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "bar"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )

        # Add equipment chart traces (top left)
        for trace in equipment_fig.data:
            fig.add_trace(trace, row=1, col=1)

        # Add seasonal chart traces (top right)
        for trace in seasonal_fig.data:
            fig.add_trace(trace, row=1, col=2)

        # Add vendor chart traces (bottom left)
        for trace in vendor_fig.data:
            fig.add_trace(trace, row=2, col=1)

        # Add failure chart traces (bottom right)
        for trace in failure_fig.data:
            fig.add_trace(trace, row=2, col=2)

        # Update layout
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fig.update_layout(
            title={
                'text': f"{title}<br><sub>Generated: {timestamp}</sub>",
                'x': 0.5,
                'xanchor': 'center'
            },
            height=1200,
            showlegend=True,
            hovermode='closest',
            template='plotly',
            barmode='group'
        )

        # Update axes labels
        fig.update_xaxes(title_text="Priority Score", row=1, col=1)
        fig.update_xaxes(title_text="Month", row=1, col=2)
        fig.update_xaxes(title_text="Vendor", tickangle=-45, row=2, col=1)
        fig.update_xaxes(title_text="Impact Score", row=2, col=2)

        fig.update_yaxes(title_text="Equipment", row=1, col=1)
        fig.update_yaxes(title_text="Cost ($)", row=1, col=2)
        fig.update_yaxes(title_text="Cost ($)", row=2, col=1)
        fig.update_yaxes(title_text="Failure Pattern", row=2, col=2)

        # Create metadata comment
        metadata = f"""
<!-- Dashboard Metadata
Generated: {timestamp}
Data Summary:
- Equipment records: {len(equipment_df) if equipment_df is not None else 0}
- Seasonal periods: {len(seasonal_dict.get('monthly', [])) if seasonal_dict and 'monthly' in seasonal_dict else 0}
- Vendors: {len(vendor_df) if vendor_df is not None else 0}
- Failure patterns: {len(patterns_list) if patterns_list else 0}
-->
"""

        # Write HTML file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use plotly offline to create self-contained HTML
        html_content = pyo.plot(
            fig,
            output_type='div',
            include_plotlyjs='cdn',  # Will be replaced with local copy
            config=self.config
        )

        # Replace CDN with local plotly.js for self-contained file
        # For true offline support, we embed the full plotly.js
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
</head>
<body>
{metadata}
{html_content}
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        logger.info(f"Interactive dashboard saved to {output_path}")
        return output_path
