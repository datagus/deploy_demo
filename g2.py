# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.3.0",
#     "marimo",
#     "openpyxl==3.1.5",
#     "pandas==3.1.1",
#     "pingouin==0.7.0",
# ]
# ///
import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import pingouin as pg

    return alt, mo, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1JfN7vBpVewr7uvYhm4GltBHQiBmSMyJkvTWT2rMqMko/"
    mode = "export/format=excel"


    url = base_url + doc_id + mode

    gsheet = pd.ExcelFile(url)
    mat_df = gsheet.parse("mat")
    por_df = gsheet.parse("por")
    return mat_df, por_df


@app.cell
def _(mat_df, pd, por_df):
    key_cols = ["school", "sex", "age", "address", "famsize", "Pstatus",
                    "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet"]
    grade_cols = ["G1", "G2", "G3"]

    df_merged = pd.merge(mat_df[key_cols+grade_cols], por_df[key_cols+grade_cols], on=key_cols, how="inner", suffixes=("_mat", "_por"))
    return (df_merged,)


@app.cell
def _(df_merged, mat_df, por_df):
    def clean_df(df, merged=False):

        relevant_cols = ["school", "sex", "Fedu"]

        if merged:
            relevant_cols.extend(["G3_por", "G3_mat"])
        else:
            relevant_cols.append("G3")

        schools = {"GP":"Gabriel Pereira", "MS":"Mousinho da Silveira"}
        sexes = {"F":"female", "M":"male"}
        fedus = {0:"low", 1:"low", 2:"low", 3:"high", 4:"high"}

        df=df.assign(
        school = df["school"].map(schools),
        sex = df["sex"].map(sexes),
        Fedu = df["Fedu"].map(fedus))

        return df[relevant_cols]

    mat_clean_df = clean_df(mat_df)
    por_clean_df = clean_df(por_df)
    both_clean_df = clean_df(df_merged, True)
    return both_clean_df, mat_clean_df, por_clean_df


@app.cell
def _(both_clean_df, mo):
    school = mo.ui.dropdown(options=both_clean_df["school"].unique().tolist()+["both"], value="both", label="school")
    sex = mo.ui.dropdown(options=both_clean_df["sex"].unique().tolist()+["both"], value="both", label="sex")
    fedu = mo.ui.dropdown(options=both_clean_df["Fedu"].unique().tolist()+["both"], value="both", label="Father Education")
    subject = mo.ui.dropdown(options=["both", "math", "portuguese"], value="both", label="subject")
    test_variable = mo.ui.dropdown(options=["sex", "school", "Father Education"], value="sex", label="test variable")
    return fedu, school, sex, subject, test_variable


@app.cell
def _(both_clean_df, fedu, mat_clean_df, por_clean_df, school, sex, subject):
    # setting dfs and variables for chart

    subject_title_string = ""
    sex_title_string = ""
    fedu_title_string = ""
    school_title_string = ""

    if subject.value == "both":
        df = both_clean_df
        subject_title_string = "both Math and Portuguese"

    elif subject.value == "math":
        df = mat_clean_df
        subject_title_string = "Math"

    else:
        df = por_clean_df
        subject_title_string = "Portuguese"

    if school.value != "both":
        df = df[df["school"]==school.value]
        school_title_string = f"only in school {school.value}"
    else:
        school_title_string = f"in both schools"

    if sex.value != "both":
        df = df[df["sex"]==sex.value]
        sex_title_string = f"only {sex.value}"
    else:
        sex_title_string = "both male and female"

    if fedu.value != "both":
        df = df[df["Fedu"]==fedu.value]
        fedu_title_string = f"only {fedu.value} Father Education"
    else:
        fedu_title_string = "low and high Father Education"

    # G3 = 0 is left out everywhere (histogram and test): these students had grades during the year and most likely did not take the final exam. We count them so the dashboard can say how many.
    if subject.value == "both":
        _has_zero = (df["G3_mat"] == 0) | (df["G3_por"] == 0)
    else:
        _has_zero = df["G3"] == 0

    num_zeros = int(_has_zero.sum())
    df = df[~_has_zero].reset_index(drop=True)

    title = "Distribution of the final grade G3"
    title_details = subject_title_string + ", " + school_title_string + ", " + sex_title_string + ", " + fedu_title_string
    return df, num_zeros, title, title_details


@app.cell
def _(df, subject):
    # dataframe only for plot
    if subject.value == "both":
        plot_df = df.melt(
            id_vars=["school", "sex", "Fedu"],
            value_vars=["G3_mat", "G3_por"],
            var_name="subject", value_name="G3",
        )
        plot_df["subject"] = plot_df["subject"].map({"G3_mat": "math", "G3_por": "portuguese"})

    elif subject.value == "math":
        plot_df = df.assign(subject="math")
    else:
        plot_df = df.assign(subject="portuguese")
    return (plot_df,)


@app.cell
def _(df):
    num_studs = len(df)
    return (num_studs,)


@app.cell
def _(alt, num_studs, num_zeros, plot_df, title, title_details):
    ## Partially written by AI
    chart = alt.Chart(plot_df).mark_bar(opacity=0.5).encode(
        x=alt.X("G3:Q", bin=alt.Bin(step=1, extent=[0, 21]), title="G3 grade", axis=alt.Axis(format="d")),  ## whole numbers on the axis
        y=alt.Y("count():Q", stack=None, title="number of students"),
        color=alt.Color("subject:N", title="subject", scale=alt.Scale(domain=["math", "portuguese"],
                                        range=["#2a78d6", "#eb6834"]),
                       legend=alt.Legend(orient="bottom", direction="horizontal")),
    ).properties(width="container", height=350,
                 title=alt.TitleParams(text=title, subtitle=[
                     title_details,
                     f"{num_studs} students ({num_zeros} with G3 = 0 left out)",
                 ]))
    return (chart,)


@app.cell
def _(chart, mo):
    histogram = mo.vstack([chart])
    return (histogram,)


@app.cell
def _(fedu, mo, school, sex, subject, test_variable):
    selection = mo.vstack(
        [
            mo.md("### Filters"),
            sex,
            school,
            fedu
        ], 
        gap=1
    )

    subject_panel = mo.vstack(
        [
            mo.md("### Subject"),
            subject,
            mo.md("###Test Variable"),
            test_variable
        ], 
        gap=1
    )
    return selection, subject_panel


@app.cell
def _(fedu, school, sex):
    ## Partially written by AI: one description of the selected filters, used by both test cells
    _sex_text = "female and male students" if sex.value == "both" else f"{sex.value} students"
    _school_text = "both schools" if school.value == "both" else school.value
    _fedu_text = {
        "both": "with all levels of father's education",
        "low": "whose father has low education",
        "high": "whose father has high education",
    }[fedu.value]
    filter_description = f"{_sex_text} from {_school_text} {_fedu_text}"
    return (filter_description,)


@app.cell
def _(
    df,
    fedu,
    filter_description,
    mo,
    pg,
    school,
    sex,
    subject,
    test_variable,
):
    ## Partially written by AI: one helper runs the test and writes the sentence for every case,
    ## so Math, Portuguese and both use exactly the same rules and wording

    # column in the data, the two groups, and readable names for each group
    _groups = {
        "sex": ("sex", "female", "male"),
        "school": ("school", "Gabriel Pereira", "Mousinho da Silveira"),
        "Father Education": ("Fedu", "low", "high"),
    }
    _names = {
        "female": "female students",
        "male": "male students",
        "Gabriel Pereira": "students of Gabriel Pereira",
        "Mousinho da Silveira": "students of Mousinho da Silveira",
        "low": "students whose father has low education",
        "high": "students whose father has high education",
    }
    _col, _value1, _value2 = _groups[test_variable.value]
    _name1, _name2 = _names[_value1], _names[_value2]

    # what the filter of the test variable is set to
    _filter_value = {"sex": sex.value, "school": school.value, "Father Education": fedu.value}[test_variable.value]

    def _test_text(data1, data2, label):
        ## run the test and explain the result for people without statistics training
        n1, n2 = len(data1), len(data2)

        if n1 < 2 or n2 < 2:
            # a test needs at least two students in each group
            return mo.callout(mo.md(
                f"**{label}:** not enough students for a test "
                f"({_name1}: n = {n1}, {_name2}: n = {n2}). Please select fewer filters."
            ), kind="warn")

        mean1, mean2 = round(data1.mean(), 2), round(data2.mean(), 2)

        if n1 > 30 and n2 > 30:
            p_value = pg.ttest(data1, data2, correction=False)["p_val"].values[0]
            test_text = ("**Test used:** independent t-test (parametric). Both groups have more than 30 students, "
                         "so their mean grades are approximately normally distributed (central limit theorem).")
        else:
            p_value = pg.mwu(data1, data2)["p_val"].values[0]
            test_text = ("**Test used:** Mann-Whitney U test (non-parametric). At least one group has 30 students or fewer, "
                         "so we do not rely on normally distributed means and compare the ranks of the grades instead.")

        if mean1 > mean2:
            higher_text = f"{_name1} scored higher on average"
        elif mean2 > mean1:
            higher_text = f"{_name2} scored higher on average"
        else:
            higher_text = "both groups have the same average"

        p_text = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
        if p_value < 0.05:
            sig_text = (f"Because {p_text} is below 0.05, the difference **is statistically significant**: "
                        "it is unlikely to be just chance.")
        else:
            sig_text = (f"Because {p_text} is not below 0.05, the difference **is not statistically significant**: "
                        "it could be just chance.")

        return mo.md(
            ## one full sentence: "Among <selected students>, <group> scored higher on average."
            f"**{label}:** Among {filter_description}, {higher_text}. "
            f"The mean final grade was **{mean1}** for {_name1} (n = {n1}) "
            f"and **{mean2}** for {_name2} (n = {n2}). {sig_text}\n\n{test_text}"
        )

    def _groups_of(grade):
        ## same students as in the histogram (filtered, without G3 = 0)
        return df.loc[df[_col] == _value1, grade], df.loc[df[_col] == _value2, grade]

    if _filter_value != "both":
        ## the filter of the test variable leaves only one group, so there is nothing to compare
        test_outputs = [mo.callout(mo.md(
            f"The test compares the two groups of **{test_variable.value}**, but this filter is set to "
            f"**{_filter_value}**, so only one group is left. Set the **{test_variable.value}** filter "
            f"to **both** or choose another test variable."
        ), kind="warn")]
    elif subject.value == "math":
        test_outputs = [_test_text(*_groups_of("G3"), "Mathematics")]
    elif subject.value == "portuguese":
        test_outputs = [_test_text(*_groups_of("G3"), "Portuguese")]
    else:
        # both: one test per subject, Math and Portuguese grades are never mixed
        test_outputs = [
            _test_text(*_groups_of("G3_mat"), "Mathematics"),
            _test_text(*_groups_of("G3_por"), "Portuguese"),
        ]
    return (test_outputs,)


@app.cell
def _(df, filter_description, mo, pg, subject):
    ## Partially written with AI: paired test for students taking both subjects,
    ## with the same rule as the other tests: more than 30 students -> paired t-test, otherwise Wilcoxon
    paired_result = None

    if subject.value == "both":
        _grades = df[["G3_mat", "G3_por"]].dropna()
        _n = len(_grades)

        if _n < 2:
            paired_result = mo.callout(mo.md(
                "**Math vs. Portuguese:** not enough students for a paired test. Please select fewer filters."
            ), kind="warn")
        elif (_grades["G3_mat"] == _grades["G3_por"]).all():
            # every student has the same grade in both subjects, so there is nothing to test
            paired_result = mo.callout(mo.md(
                "**Math vs. Portuguese:** all selected students have the same grade in both subjects."
            ), kind="info")
        else:
            if _n > 30:
                _p = pg.ttest(_grades["G3_mat"], _grades["G3_por"], paired=True)["p_val"].iloc[0]
                _test_text = (
                    "**Test used:** paired t-test (parametric). Every student has a Math and a Portuguese grade, "
                    "so we compare the two grades of the same student. With more than 30 students, the mean "
                    "difference is approximately normally distributed (central limit theorem)."
                )
            else:
                _p = pg.wilcoxon(_grades["G3_mat"], _grades["G3_por"])["p_val"].iloc[0]
                _test_text = (
                    "**Test used:** Wilcoxon signed-rank test (non-parametric). Every student has a Math and a "
                    "Portuguese grade, so we compare the two grades of the same student. With 30 students or fewer, "
                    "we do not rely on a normally distributed mean difference and compare ranks instead."
                )

            _mean_mat = round(_grades["G3_mat"].mean(), 2)
            _mean_por = round(_grades["G3_por"].mean(), 2)
            if _mean_por > _mean_mat:
                _higher = "these students scored higher in Portuguese than in Math on average"
            elif _mean_mat > _mean_por:
                _higher = "these students scored higher in Math than in Portuguese on average"
            else:
                _higher = "these students have the same average in both subjects"

            _p_text = "p < 0.001" if _p < 0.001 else f"p = {_p:.3f}"
            if _p < 0.05:
                _sig = (f"Because {_p_text} is below 0.05, the difference **is statistically significant**: "
                        "it is unlikely to be just chance.")
            else:
                _sig = (f"Because {_p_text} is not below 0.05, the difference **is not statistically significant**: "
                        "it could be just chance.")

            paired_result = mo.md(
                "### Paired comparison of Math and Portuguese\n\n"
                f"Among {filter_description} ({_n} students taking both subjects), {_higher}. "
                f"The mean final grade was **{_mean_mat}** in Math and **{_mean_por}** in Portuguese. {_sig}\n\n"
                f"{_test_text}\n\n"
                "**Important:** Math and Portuguese are different exams with different teachers, "
                "so a difference in grades does not necessarily mean the students are better at one subject."
            )
    return (paired_result,)


@app.cell
def _(mo, num_zeros, paired_result, test_outputs):
    ## say how many students with G3 = 0 are left out in the current selection, and why
    _count = "no students" if num_zeros == 0 else ("1 student" if num_zeros == 1 else f"{num_zeros} students")
    _note = mo.md(
        "*Note: students with a final grade of 0 are left out of the histogram and all tests. "
        "They had grades during the year and most likely did not take the final exam, so a 0 is not a real result. "
        f"In this selection that is {_count}.*"
    )

    ## order: group tests, then the paired test, and the note last because it applies to everything
    _paired = [paired_result] if paired_result is not None else []
    summary_panel = mo.vstack(test_outputs + _paired + [_note], gap=1)
    return (summary_panel,)


@app.cell
def _(histogram, mo, selection, subject_panel, summary_panel):
    ## Partially written by AI
    mo.vstack(
        [
            mo.callout(
                mo.center(
                    mo.md("""# Group 2 · Student performance dashboard
                    ## Members: Max Mausolf, Ko-Hsin Lo, Dorcas Adejunmobi""")
                ),
                "success",
            ),

            mo.hstack(
                [selection, histogram, subject_panel],
                widths=[1, 3.5, 1.5],
                gap=2,
                align="start",
            ),

            #summary
            mo.center(summary_panel),
        ],
        gap=2,
    )
    return


if __name__ == "__main__":
    app.run()
