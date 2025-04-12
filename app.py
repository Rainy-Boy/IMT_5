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
    "convert_comma_to_dot": {
        "function": lambda df, cols: df.assign(**{
            col: df[col].astype(str).str.replace(',', '.').apply(
                lambda x: pd.to_numeric(x, errors='coerce')
            ) for col in cols
        }),
        "description": "Convert comma decimal separators to dots (e.g., '76,5' → '76.5')",
        "params": {
            "cols": {"type": "column_multi", "default": [], "description": "Select columns with comma decimals"}
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
    delimiter_ui_options = [",", ";", "\\t", "|", "' '"]
    delimiter_options = [",", ";", "\t", "|", " "]
    delimiter = st.selectbox("Select delimiter", delimiter_ui_options, index=1)  # Default to semicolon

    delimiter = delimiter_options[delimiter_ui_options.index(delimiter)]
    
    if uploaded_file is not None:
        # Load data
        try:
            df = pd.read_csv(uploaded_file, delimiter=delimiter)
            
            # Display data preview
            st.subheader("Data Preview")
            st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
            st.dataframe(df.head())
            
            # Simple multiple preprocessing section
            if st.checkbox("Apply preprocessing"):
                st.subheader("Data Preprocessing")
                # Initialize preprocessing list in session state
                if "preprocessing_list" not in st.session_state:
                    st.session_state.preprocessing_list = []

                # Select preprocessing method
                preprocessing_type = st.selectbox("Select preprocessing method", list(preprocessing_registry.keys()))

                # Generate UI for preprocessing parameters
                params = {}
                for param_name, param_config in preprocessing_registry[preprocessing_type]["params"].items():
                    if param_config["type"] == "column":
                        params[param_name] = st.selectbox(f"Select column for {param_name}", df.columns, key=f"{preprocessing_type}_{param_name}")
                    elif param_config["type"] == "column_multi":
                        params[param_name] = st.multiselect(f"Select columns for {param_name}", df.columns, key=f"{preprocessing_type}_{param_name}")
                    elif param_config["type"] == "select":
                        options = param_config.get("options", [])
                        default_idx = options.index(param_config.get("default")) if "default" in param_config else 0
                        params[param_name] = st.selectbox(f"{param_name}", options, index=default_idx, key=f"{preprocessing_type}_{param_name}")
                    elif param_config["type"] == "text":
                        default = param_config.get("default", "")
                        params[param_name] = st.text_input(f"{param_name}", value=default, key=f"{preprocessing_type}_{param_name}")
                    elif param_config["type"] == "slider":
                        min_val = param_config.get("min", 0)
                        max_val = param_config.get("max", 100)
                        default = param_config.get("default", (min_val + max_val) // 2)
                        params[param_name] = st.slider(f"{param_name}", min_value=min_val, max_value=max_val, value=default, key=f"{preprocessing_type}_{param_name}")

                # Add to preprocessing list
                if st.button("Add to preprocessing list"):
                    st.session_state.preprocessing_list.append((preprocessing_type, params.copy()))
                    st.success(f"Added '{preprocessing_type}' to preprocessing list.")

                # Show current preprocessing steps
                if st.session_state.preprocessing_list:
                    st.markdown("### Preprocessing Steps:")
                    # Display and allow removal of specific preprocessing steps
                    for i, (ptype, pparams) in enumerate(st.session_state.preprocessing_list):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{i+1}. {ptype}** — `{pparams}`")
                        with col2:
                            if st.button("❌ Remove", key=f"remove_{i}"):
                                st.session_state.preprocessing_list.pop(i)
                                st.rerun()

                # Apply all preprocessing steps
                if st.button("Apply all preprocessing"):
                    original_df = df.copy()
                    try:
                        for step_type, step_params in st.session_state.preprocessing_list:
                            preprocessing_func = preprocessing_registry[step_type]["function"]

                            # Handle numeric conversion
                            if "value" in step_params and step_type == "fill_nulls" and step_params["method"] == "value":
                                try:
                                    step_params["value"] = float(step_params["value"])
                                except ValueError:
                                    pass

                            df = preprocessing_func(df, **step_params)

                        st.session_state.preprocessed_df = df
                        st.success(f"Applied {len(st.session_state.preprocessing_list)} preprocessing steps!")
                        st.write("Updated data preview:")
                        st.dataframe(df.head())

                    except Exception as e:
                        st.error(f"Error in preprocessing: {str(e)}")
                        df = original_df

                # Clear list
                if st.button("Clear preprocessing list"):
                    st.session_state.preprocessing_list.clear()
                    if "preprocessed_df" in st.session_state:
                        del st.session_state["preprocessed_df"]
                    st.success("Preprocessing list cleared.")
                    st.rerun()

            # Visualization selection
            working_df = st.session_state.get("preprocessed_df", df)

            st.subheader("Create Visualization")
            viz_type = st.selectbox("Select visualization type", list(viz_registry.keys()))
            
            # Display description
            st.write(viz_registry[viz_type]["description"])
            
            # Column selection for X and Y axes
            viz_params = {}
            
            # Dynamically create UI for required parameters (X and Y axes)
            for param in viz_registry[viz_type]["required_params"]:
                col_select = st.selectbox(f"Select column for {param}", working_df.columns)
                viz_params[param] = col_select
            
            # Create visualization
            if st.button("Generate Visualization"):
                try:
                    # Filter out None values
                    filtered_params = {k: v for k, v in viz_params.items() if v != "None"}
                    
                    # Create and display visualization
                    viz_function = viz_registry[viz_type]["function"]
                    fig = viz_function(working_df, **filtered_params)
                    st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"Error creating visualization: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

if __name__ == "__main__":
    main()