import streamlit as st
import pandas as pd
import plotly.express as px
# Import visualization and preprocessing registries
# from config import *

preprocessing_registry = {
    "remove_nulls": {
        "function": lambda df, cols: df.dropna(subset=cols),
        "description": "Remove rows with missing values",
        "params": {"cols": {"type": "column_multi", "default": "all"}}
    },
    "fill_nulls": {
        "function": lambda df, cols, method, value: df.fillna({col: value if method == "value" else df[col].mean() if method == "mean" else df[col].median() if method == "median" else df[col].mode()[0] for col in cols}),
        "description": "Fill missing values using specified method",
        "params": {
            "cols": {"type": "column_multi", "default": "all"},
            "method": {"type": "select", "options": ["mean", "median", "mode", "value"], "default": "mean"},
            "value": {"type": "text", "default": "0", "description": "Value to use if 'value' method selected"}
        }
    },
    "filter_rows": {
        "function": lambda df, column, operator, value: df[eval(f"df['{column}'] {operator} {value}")],
        "description": "Filter rows based on condition",
        "params": {
            "column": {"type": "column", "default": ""},
            "operator": {"type": "select", "options": ["==", ">", "<", ">=", "<=", "!="], "default": "=="},
            "value": {"type": "text", "default": ""}
        }
    },
    "convert_type": {
        "function": lambda df, column, to_type: df.assign(**{column: df[column].astype(to_type) if to_type != "datetime" else pd.to_datetime(df[column], errors="coerce")}),
        "description": "Convert column data type",
        "params": {
            "column": {"type": "column", "default": ""},
            "to_type": {"type": "select", "options": ["int", "float", "str", "datetime", "category"], "default": "float"}
        }
    },
    "create_bins": {
        "function": lambda df, column, bins, labels=None: df.assign(**{f"{column}_binned": pd.cut(df[column], bins=bins, labels=labels)}),
        "description": "Create bins from a numeric column",
        "params": {
            "column": {"type": "column", "default": ""},
            "bins": {"type": "slider", "min": 2, "max": 10, "default": 4, "description": "Number of bins"},
            "labels": {"type": "text", "default": "", "description": "Comma-separated labels (optional)"}
        }
    },
    "normalize": {
        "function": lambda df, column, method: df.assign(**{f"{column}_norm": (df[column]-df[column].min())/(df[column].max()-df[column].min()) if method == "minmax" else (df[column]-df[column].mean())/df[column].std()}),
        "description": "Normalize numeric column",
        "params": {
            "column": {"type": "column", "default": ""},
            "method": {"type": "select", "options": ["minmax", "zscore"], "default": "minmax"}
        }
    },
    "pivot_table": {
        "function": lambda df, index, columns, values, aggfunc: pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc),
        "description": "Create a pivot table for heatmap visualization",
        "params": {
            "index": {"type": "column", "default": ""},
            "columns": {"type": "column", "default": ""},
            "values": {"type": "column", "default": ""},
            "aggfunc": {"type": "select", "options": ["mean", "sum", "count", "median"], "default": "mean"}
        }
    },
    "top_n_categories": {
        "function": lambda df, column, n: df[df[column].isin(df[column].value_counts().nlargest(n).index)],
        "description": "Keep only the top N categories",
        "params": {
            "column": {"type": "column", "default": ""},
            "n": {"type": "slider", "min": 1, "max": 20, "default": 5, "description": "Number of categories to keep"}
        }
    }
}

viz_registry = {
    "Bar Chart": {
        "function": px.bar,
        "required_params": ["x", "y"],
        "optional_params": {
            "color": {"type": "column", "description": "Color bars by category"},
            "barmode": {"type": "select", "options": ["group", "stack"], "default": "group"},
            "orientation": {"type": "select", "options": ["v", "h"], "default": "v", "description": "Vertical or horizontal bars"}
        },
        "description": "Compare values across categories",
        "data_requirements": {"y": "numeric"}
    },
    "Line Chart": {
        "function": px.line,
        "required_params": ["x", "y"],
        "optional_params": {
            "color": {"type": "column", "description": "Create separate lines by category"},
            "line_shape": {"type": "select", "options": ["linear", "spline"], "default": "linear"},
            "markers": {"type": "checkbox", "default": False, "description": "Show markers"}
        },
        "description": "Show trends over a continuous axis (often time)",
        "data_requirements": {"y": "numeric"}
    },
    "Scatter Plot": {
        "function": px.scatter,
        "required_params": ["x", "y"],
        "optional_params": {
            "color": {"type": "column", "description": "Color points by category"},
            "size": {"type": "column", "description": "Size points by value"},
            "trendline": {"type": "select", "options": ["None", "ols", "lowess"], "default": "None"}
        },
        "description": "Show relationship between two numeric variables",
        "data_requirements": {"x": "numeric", "y": "numeric"}
    },
    "Histogram": {
        "function": px.histogram,
        "required_params": ["x"],
        "optional_params": {
            "nbins": {"type": "slider", "min": 5, "max": 100, "default": 20, "description": "Number of bins"},
            "color": {"type": "column", "description": "Group histogram by category"},
            "marginal": {"type": "select", "options": ["None", "box", "violin", "rug"], "default": "None"}
        },
        "description": "Show distribution of a single variable",
        "data_requirements": {"x": "numeric"}
    },
    "Box Plot": {
        "function": px.box,
        "required_params": ["x", "y"],
        "optional_params": {
            "color": {"type": "column", "description": "Group boxes by another category"},
            "notched": {"type": "checkbox", "default": False, "description": "Show confidence interval notches"},
            "points": {"type": "select", "options": ["all", "outliers", "suspectedoutliers", "False"], "default": "outliers"}
        },
        "description": "Show distribution statistics across categories",
        "data_requirements": {"y": "numeric"}
    },
    "Pie Chart": {
        "function": px.pie,
        "required_params": ["names", "values"],
        "optional_params": {
            "hole": {"type": "slider", "min": 0, "max": 0.8, "default": 0, "description": "Create a donut chart (0 for pie)"},
            "pull": {"type": "column", "description": "Pull sectors out from center"}
        },
        "description": "Show proportion of total for categories",
        "data_requirements": {"values": "numeric"}
    }
}

def main():
    st.title("CSV Data Visualizer")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    # Delimiter selection
    delimiter_options = [",", ";", "\t", "|", " "]
    delimiter = st.selectbox("Select delimiter", delimiter_options, index=1)  # Default to semicolon
    
    if uploaded_file is not None:
        # Load data
        try:
            df = pd.read_csv(uploaded_file, delimiter=delimiter)
            
            # Display data preview
            st.subheader("Data Preview")
            st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
            st.dataframe(df.head())
            
            # Preprocessing section (simplified)
            if st.checkbox("Apply preprocessing"):
                preprocessing_type = st.selectbox("Select preprocessing method", list(preprocessing_registry.keys()))
                
                # Generate UI for preprocessing parameters
                params = {}
                for param_name, param_config in preprocessing_registry[preprocessing_type]["params"].items():
                    if param_config["type"] == "column":
                        params[param_name] = st.selectbox(f"Select column for {param_name}", df.columns)
                    elif param_config["type"] == "column_multi":
                        params[param_name] = st.multiselect(f"Select columns", df.columns)
                
                # Apply preprocessing when button is clicked
                if st.button("Apply"):
                    try:
                        preprocessing_func = preprocessing_registry[preprocessing_type]["function"]
                        df = preprocessing_func(df, **params)
                        st.success("Preprocessing applied!")
                    except Exception as e:
                        st.error(f"Error in preprocessing: {str(e)}")
            
            # Visualization selection
            st.subheader("Create Visualization")
            viz_type = st.selectbox("Select visualization type", list(viz_registry.keys()))
            
            # Display description
            st.write(viz_registry[viz_type]["description"])
            
            # Column selection for X and Y axes
            viz_params = {}
            
            # Dynamically create UI for required parameters (X and Y axes)
            for param in viz_registry[viz_type]["required_params"]:
                col_select = st.selectbox(f"Select column for {param}", df.columns)
                viz_params[param] = col_select
            
            # Advanced options in expander
            # with st.expander("Advanced Options"):
            #     for param_name, param_config in viz_registry[viz_type].get("optional_params", {}).items():
            #         if param_config["type"] == "column":
            #             viz_params[param_name] = st.selectbox(
            #                 param_config["description"], 
            #                 ["None"] + list(df.columns)
            #             )
            #         elif param_config["type"] == "select":
            #             viz_params[param_name] = st.selectbox(
            #                 param_config["description"],
            #                 param_config["options"],
            #                 index=param_config["options"].index(param_config["default"])
            #             )
            
            # Create visualization
            if st.button("Generate Visualization"):
                try:
                    # Filter out None values
                    filtered_params = {k: v for k, v in viz_params.items() if v != "None"}
                    
                    # Create and display visualization
                    viz_function = viz_registry[viz_type]["function"]
                    fig = viz_function(df, **filtered_params)
                    st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"Error creating visualization: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

if __name__ == "__main__":
    main()