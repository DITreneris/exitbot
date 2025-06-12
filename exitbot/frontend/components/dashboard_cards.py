"""
Enhanced Dashboard Components for HR App

This module provides enhanced dashboard cards and visualizations for the HR dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def render_metric_card(title, value, delta=None, delta_suffix="vs previous period", icon=None, help_text=None):
    """
    Renders an enhanced metric card with animation and optional delta indicator
    
    Parameters:
    - title: Title of the metric
    - value: Main value to display
    - delta: Optional change value (can be positive or negative)
    - delta_suffix: Text to show after the delta value
    - icon: Optional icon to display (emoji or HTML)
    - help_text: Optional help text with additional information
    
    Returns:
    - None
    """
    
    # Determine delta color and symbol
    delta_color = ""
    delta_symbol = ""
    
    if delta is not None:
        if str(delta).startswith("+") or (isinstance(delta, (int, float)) and delta > 0):
            delta_color = "color: #10B981;"  # Success color
            delta_symbol = "↑"
        elif str(delta).startswith("-") or (isinstance(delta, (int, float)) and delta < 0):
            delta_color = "color: #EF4444;"  # Error color
            delta_symbol = "↓"
        else:
            delta_color = "color: #9CA3AF;"  # Neutral color
            delta_symbol = "→"
    
    # Construct help icon if help text is provided
    help_icon = f'<span class="dashboard-help" title="{help_text}">ⓘ</span>' if help_text else ''
    
    # Render the card with improved styling
    st.markdown(
        f"""
        <style>
        .metric-card {{
            height: 100%;
            padding: 1.25rem;
            border-radius: 0.5rem;
            background-color: white;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }}
        .metric-card:hover {{
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }}
        .metric-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}
        .metric-title {{
            color: #6B7280;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        .metric-icon {{
            font-size: 1.5rem;
            color: #3B82F6;
        }}
        .metric-value {{
            font-size: 1.875rem;
            font-weight: 700;
            color: #1F2937;
            margin-bottom: 0.5rem;
        }}
        .metric-delta {{
            font-size: 0.875rem;
            font-weight: 500;
        }}
        .metric-delta-suffix {{
            color: #6B7280;
            font-size: 0.75rem;
            margin-left: 0.25rem;
        }}
        </style>
        
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-title">
                    {title} {help_icon}
                </div>
                {f'<div class="metric-icon">{icon}</div>' if icon else ''}
            </div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-delta" style="{delta_color}">{delta_symbol} {delta} <span class="metric-delta-suffix">{delta_suffix}</span></div>' if delta is not None else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_interview_completion_chart(complete_count, incomplete_count, total_count):
    """
    Renders an animated completion donut chart
    
    Parameters:
    - complete_count: Number of completed interviews
    - incomplete_count: Number of incomplete interviews
    - total_count: Total number of interviews
    
    Returns:
    - None
    """
    
    # Calculate completion percentage
    completion_percentage = round((complete_count / total_count) * 100) if total_count > 0 else 0
    
    # Create a dataframe for the chart
    data = pd.DataFrame({
        'Status': ['Complete', 'Incomplete'],
        'Count': [complete_count, incomplete_count]
    })
    
    # Create donut chart with Plotly
    fig = px.pie(
        data,
        names='Status',
        values='Count',
        hole=0.7,
        color='Status',
        color_discrete_map={
            'Complete': '#10B981',  # Success color
            'Incomplete': '#E5E7EB'  # Light gray
        }
    )
    
    # Update layout for cleaner appearance
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        annotations=[
            dict(
                text=f"{completion_percentage}%",
                font=dict(size=24, color='#111827', family="Inter, sans-serif", weight="bold"),
                showarrow=False,
                x=0.5,
                y=0.5
            ),
            dict(
                text="Completion Rate",
                font=dict(size=12, color='#6B7280', family="Inter, sans-serif"),
                showarrow=False,
                x=0.5,
                y=0.4
            )
        ]
    )
    
    # Disable interactivity
    fig.update_traces(hoverinfo="skip", hovertemplate=None)
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_time_series_chart(data, title, x_column, y_column, color=None):
    """
    Renders an enhanced time series chart with animations and styling
    
    Parameters:
    - data: Pandas DataFrame with the data
    - title: Chart title
    - x_column: Column name for x-axis (typically date)
    - y_column: Column name for y-axis (metric to plot)
    - color: Optional color for the line
    
    Returns:
    - None
    """
    
    if color is None:
        color = '#3B82F6'  # Default to primary color
    
    # Create the line chart
    fig = px.line(
        data, 
        x=x_column, 
        y=y_column,
        title=title
    )
    
    # Enhance styling
    fig.update_traces(
        line=dict(color=color, width=3),
        mode='lines'
    )
    
    # Improve layout
    fig.update_layout(
        font=dict(family="Inter, sans-serif"),
        title=dict(
            text=title,
            font=dict(size=16, color='#111827'),
            x=0.05,
            xanchor='left'
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(
            showgrid=True,
            gridcolor='#F3F4F6',
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#F3F4F6',
            title=None
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified'
    )
    
    # Add a range slider for interactive data exploration
    fig.update_xaxes(rangeslider_visible=False)
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_department_breakdown(department_data):
    """
    Renders an enhanced horizontal bar chart for department breakdown
    
    Parameters:
    - department_data: DataFrame with department statistics
    
    Returns:
    - None
    """
    
    # Sort data by count descending
    sorted_data = department_data.sort_values('count', ascending=True)
    
    # Create the horizontal bar chart
    fig = px.bar(
        sorted_data,
        y='department',
        x='count',
        orientation='h',
        title='Interviews by Department',
        text='count'
    )
    
    # Enhance styling
    fig.update_traces(
        marker_color='#3B82F6',
        textposition='outside',
        textfont=dict(family="Inter, sans-serif", size=12),
        hovertemplate='<b>%{y}</b><br>Interviews: %{x}<extra></extra>'
    )
    
    # Improve layout
    fig.update_layout(
        font=dict(family="Inter, sans-serif"),
        title=dict(
            text='Interviews by Department',
            font=dict(size=16, color='#111827'),
            x=0.05,
            xanchor='left'
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(
            showgrid=True,
            gridcolor='#F3F4F6',
            title=None
        ),
        yaxis=dict(
            title=None,
            categoryorder='total ascending'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_sentiment_gauge(sentiment_score, title="Overall Sentiment"):
    """
    Renders a gauge chart for sentiment visualization
    
    Parameters:
    - sentiment_score: Score between -1 and 1
    - title: Chart title
    
    Returns:
    - None
    """
    
    # Normalize sentiment from [-1, 1] to [0, 1] for the gauge
    normalized_score = (sentiment_score + 1) / 2
    
    # Determine color based on sentiment
    if sentiment_score >= 0.3:
        color = '#10B981'  # Positive - green
    elif sentiment_score <= -0.3:
        color = '#EF4444'  # Negative - red
    else:
        color = '#F59E0B'  # Neutral - amber
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=normalized_score * 100,  # Convert to percentage for display
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 24, 'family': 'Inter, sans-serif'}
        },
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#F3F4F6"},
            'bar': {'color': color},
            'bgcolor': "#F9FAFB",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 33], 'color': "#FECACA"},  # Light red
                {'range': [33, 67], 'color': "#FEF3C7"},  # Light amber
                {'range': [67, 100], 'color': "#D1FAE5"}  # Light green
            ],
        },
        title={
            'text': title,
            'font': {'size': 16, 'family': 'Inter, sans-serif'}
        }
    ))
    
    # Update layout
    fig.update_layout(
        margin=dict(t=60, b=20, l=20, r=20),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif"),
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) 