import pandas as pd
import sys
from shiny import App, reactive
from shinyswatch import theme
from shinywidgets import render_widget
from shiny.express import input, render, ui
from itables.widget import ITable
from shared import app_dir, df
from itables.sample_dfs import get_dict_of_test_dfs

dept_options = ["All"] + sorted(df["Dept Name"].dropna().unique())
neg_body_options = ["All"] + sorted(df["Neg Body"].dropna().unique())
min_salary = int(df["Job Min Annual"].min())
max_salary = int(df["Job Max Annual"].max())

# Filtering function
def filter_data(selected_dept: str, selected_neg_body: str, salary_range: tuple[int, int]) -> pd.DataFrame:
    filtered = df
    if selected_dept != "All":
        filtered = filtered[filtered["Dept Name"] == selected_dept]
    if selected_neg_body != "All":
        filtered = filtered[filtered["Neg Body"] == selected_neg_body]
    min_salary, max_salary = salary_range

    filtered = filtered[
        (
            # Either Job Min Annual is >= min_salary
            (filtered["Job Min Annual"] >= min_salary)
            # OR Job Min Annual is NaN and Job Max Annual is >= min_salary
            | (filtered["Job Min Annual"].isna() & (filtered["Job Max Annual"] >= min_salary))
        )
        &
        (
            # Job Max Annual is NaN or <= max_salary
            (filtered["Job Max Annual"].isna() | (filtered["Job Max Annual"] <= max_salary))
        )
    ]

    return filtered

@reactive.calc
def filtered_data():
    return filter_data(
        input.dept_filter(),
        input.neg_body_filter(),
        input.salary_range()
    )

@reactive.calc
def formatted_data_for_table():
    d = filtered_data().copy()
    for col in ["Job Min Annual", "Job Max Annual"]:
        if col in d.columns:
            d[col] = d[col].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "")
    return d

ui.head_content(
    ui.tags.link(
        rel="icon",
        type="image/x-icon",
        sizes="16x16",
        href="favicon.ico"
    ),
    ui.tags.link(
        rel="stylesheet",
        href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css"
    ),
    ui.tags.script(
        async_="true",
        src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4337721684173660",
        crossorigin="anonymous"
    ),
    ui.tags.meta(
        name="google-adsense-account",
        content="ca-pub-4337721684173660"
    )
)

# UI layout
ui.page_opts(
    # title="Bermuda Government Salaries",
    fillable=True,
    id="page",
    theme=theme.yeti
)

with ui.sidebar():
    ui.input_slider(
       "salary_range",
       "Salary Range",
       min=min_salary,
       max=max_salary,
       value=(min_salary, max_salary),
       step=1000,
       sep=","
    ),
    ui.input_select(
        "dept_filter",
        "Department",
        choices=dept_options,
        selected="All"
    ),
    ui.input_select(
        "neg_body_filter",
        "Negotiating Body",
        choices=neg_body_options,
        selected="All"
    )

    ui.tags.p(
       "Source: ",
       ui.tags.a(
           "Public Officer Salaries 2024",
           href="https://www.gov.bm/sites/default/files/2024-08/Public-Officer-Salaries-2024.pdf",
           target="_blank",
           style="text-decoration: underline;"
       ),
       style="font-size: 0.8em; color: gray; margin-top: 1rem;"
    )

with ui.layout_columns(fill=False):
    with ui.value_box():
        "Median Salary"

        @render.express
        def median_salary():
            d = filtered_data()
            if d.empty:
                return "N/A"
            else:
                min_vals = d["Job Min Annual"]
                max_vals = d["Job Max Annual"]

                median_vals = pd.concat([
                    ((min_vals + max_vals) / 2).dropna(),
                    min_vals[max_vals.isna()],
                    max_vals[min_vals.isna()]
                ])

                f"${median_vals.median():,.0f}"

    with ui.value_box():
        "Average Salary"

        @render.express
        def avg_salary():
            d = filtered_data()
            if d.empty:
                "N/A"
            else:
                min_vals = d["Job Min Annual"]
                max_vals = d["Job Max Annual"]

                avg_vals = pd.concat([
                    ((min_vals + max_vals) / 2).dropna(),
                    min_vals[max_vals.isna()],
                    max_vals[min_vals.isna()]
                ])

                f"${avg_vals.mean():,.0f}"

    with ui.value_box():
        "Min Salary"

        @render.express
        def min_salary_():
            d = filtered_data()
            if d.empty:
                "N/A"
            else:
                combined_min = pd.concat([
                    d["Job Min Annual"].dropna(),
                    d["Job Max Annual"].dropna()
                ])

                "N/A" if combined_min.empty else f"${combined_min.min():,.0f}"

    with ui.value_box():
        "Max Salary"

        @render.express
        def max_salary_():
            d = filtered_data()
            if d.empty:
                "N/A"
            else:
                combined_max = pd.concat([
                    d["Job Min Annual"].dropna(),
                    d["Job Max Annual"].dropna()
                ])

                "N/A" if combined_max.empty else f"${combined_max.max():,.0f}"

# Table below the value boxes
with ui.layout_columns(fill=True):    
    with ui.card(full_screen=True, scrollable=True):
        @render_widget
        def my_table():
            return ITable(
            formatted_data_for_table(),
            style="width:100%; height: auto !important",
            showIndex=False,
            scrollY="45vh",
            scrollCollapse=True,
            lengthMenu=[25, 50, 100],
            paging=True
            )
        
        @reactive.effect
        def _():
            my_table.widget.update(
            formatted_data_for_table(),
            maxBytes="128KB",
            showIndex=False
        )
