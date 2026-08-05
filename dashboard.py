import logging
import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT + LOGGING
# ============================================================

load_dotenv()

logging.basicConfig(
    level=os.environ.get(
        "LOG_LEVEL",
        "INFO",
    )
)

logger = logging.getLogger(
    "aegis.dashboard"
)


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Aegis AI | Code Review",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# CONFIGURATION
# Supports:
# - Streamlit Cloud (st.secrets)
# - Render / other host environment variables
# - Local .env
# ============================================================

def get_config(name: str, default: str = "") -> str:
    """Resolve a config value, preferring st.secrets, then env vars."""

    try:
        if name in st.secrets:
            value = st.secrets[name]
            if value:
                return str(value)
    except Exception:
        # st.secrets raises if no secrets.toml exists at all (e.g. local dev)
        pass

    value = os.getenv(name)

    if value:
        return value

    return default


def require_config(name: str) -> str:
    """Resolve a mandatory config value, failing loudly if it's missing."""

    value = get_config(name)

    if not value:
        st.error(
            f"Missing required configuration: `{name}`. "
            "Set it in Streamlit secrets or as an environment variable."
        )
        st.stop()

    return value


BACKEND_URL = get_config(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

API_KEY = get_config("API_KEY").strip()

SUPABASE_URL = get_config("SUPABASE_URL").strip()

SUPABASE_KEY = get_config("SUPABASE_KEY").strip()


# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def init_db():

    try:

        from supabase import create_client

        if not SUPABASE_URL or not SUPABASE_KEY:

            logger.warning(
                "Supabase credentials "
                "are not configured."
            )

            return None

        return create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )

    except Exception:

        logger.exception(
            "Database connection failed."
        )

        return None


supabase = init_db()


# ============================================================
# LOAD ANALYTICS DATA
# ============================================================

@st.cache_data(
    ttl=30
)
def load_data():

    if not supabase:

        return pd.DataFrame()

    try:

        response = (
            supabase
            .table("reviews")
            .select(
                """
                repo_name,
                pr_number,
                overall_score,
                risk_level,
                issue_count,
                critical_count,
                high_count,
                medium_count,
                low_count,
                review_duration_ms,
                created_at
                """
            )
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )

        return pd.DataFrame(
            response.data or []
        )

    except Exception:

        logger.exception(
            "Failed to load "
            "review analytics."
        )

        return pd.DataFrame()


# ============================================================
# HELPERS
# ============================================================

def numeric_column(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in dataframe.columns:

        return pd.Series(
            dtype="float64"
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )


def count_risk(
    dataframe: pd.DataFrame,
    levels: list[str],
) -> int:

    if (
        "risk_level"
        not in dataframe.columns
    ):

        return 0

    return int(
        dataframe[
            "risk_level"
        ].isin(
            levels
        ).sum()
    )


# ============================================================
# LOAD DATA
# ============================================================

df_reviews = load_data()


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ Aegis AI"
)

st.caption(
    "AI-Powered DevSecOps Code Review "
    "& Pull Request Intelligence"
)

st.divider()


# ============================================================
# TABS
# ============================================================

tab_review, tab_analytics = st.tabs(
    [
        "🔍 Code Review",
        "📊 Review Analytics",
    ]
)


# ============================================================
# LIVE CODE REVIEW
# ============================================================

with tab_review:

    st.subheader(
        "Live Code Review"
    )

    st.write(
        "Paste a code snippet or diff for an "
        "AI-assisted engineering review."
    )

    st.caption(
        "Aegis analyzes security, performance, "
        "quality, and reliability before validating "
        "findings and calculating a deterministic score."
    )

    code_input = st.text_area(
        "Paste Python / code diff here:",
        height=320,
        placeholder=(
            "Paste code or a code diff here..."
        ),
    )

    col_run, col_info = st.columns(
        [1, 4]
    )

    with col_run:

        run_review = st.button(
            "Run Aegis Review",
            type="primary",
            use_container_width=True,
        )

    with col_info:

        st.caption(
            "AI-generated findings should still "
            "be reviewed before production changes."
        )


    # ========================================================
    # RUN REVIEW
    # ========================================================

    if run_review:

        if not code_input.strip():

            st.warning(
                "Paste some code first."
            )

        elif not API_KEY:

            st.error(
                "API_KEY is not configured "
                "for the dashboard."
            )

        else:

            with st.spinner(
                "Aegis is reviewing the code..."
            ):

                try:

                    response = requests.post(
                        (
                            f"{BACKEND_URL}"
                            "/manual-review"
                        ),
                        json={
                            "code": code_input
                        },
                        headers={
                            "X-API-Key": API_KEY
                        },

                        # Connection timeout,
                        # then read timeout. LLM-backed
                        # reviews can take a while.
                        timeout=(
                            10,
                            300,
                        ),
                    )


                    # ========================================
                    # SUCCESS
                    # ========================================

                    if response.ok:

                        payload = (
                            response.json()
                        )

                        score = payload.get(
                            "score"
                        )

                        risk = payload.get(
                            "risk_level",
                            "Unknown",
                        )

                        issue_count = (
                            payload.get(
                                "issue_count",
                                0,
                            )
                        )

                        counts = (
                            payload.get(
                                "counts",
                                {},
                            )
                        )

                        feedback = payload.get(
                            "feedback"
                        ) or "No review was returned."


                        # ====================================
                        # TOP METRICS
                        # ====================================

                        metric_1, metric_2, metric_3 = (
                            st.columns(3)
                        )

                        metric_1.metric(
                            "Code Score",
                            (
                                f"{score}/100"
                                if score is not None
                                else "N/A"
                            ),
                        )

                        metric_2.metric(
                            "Risk Level",
                            risk or "Unknown",
                        )

                        metric_3.metric(
                            "Accepted Findings",
                            issue_count,
                        )


                        # ====================================
                        # SEVERITY SUMMARY
                        # ====================================

                        severity_1, severity_2, \
                            severity_3, severity_4 = (
                                st.columns(4)
                            )

                        severity_1.metric(
                            "Critical",
                            counts.get(
                                "critical",
                                0,
                            ),
                        )

                        severity_2.metric(
                            "High",
                            counts.get(
                                "high",
                                0,
                            ),
                        )

                        severity_3.metric(
                            "Medium",
                            counts.get(
                                "medium",
                                0,
                            ),
                        )

                        severity_4.metric(
                            "Low",
                            counts.get(
                                "low",
                                0,
                            ),
                        )


                        st.success(
                            "Analysis complete."
                        )

                        st.divider()


                        # ====================================
                        # MARKDOWN REPORT
                        # ====================================

                        st.markdown(feedback)

                        with st.expander(
                            "View raw markdown"
                        ):
                            st.code(
                                feedback,
                                language="markdown",
                            )

                        st.download_button(
                            "Download Report",
                            feedback,
                            file_name="review.md",
                            mime="text/markdown",
                        )


                    # ========================================
                    # API ERROR
                    # ========================================

                    else:

                        try:

                            error_payload = (
                                response.json()
                            )

                            detail = (
                                error_payload.get(
                                    "detail",
                                    response.text,
                                )
                            )

                        except ValueError:

                            detail = (
                                response.text
                            )

                        st.error(
                            (
                                "Aegis API returned "
                                f"{response.status_code}."
                            )
                        )

                        with st.expander(
                            "API error details"
                        ):
                            st.code(str(detail))


                # ============================================
                # NETWORK ERROR
                # ============================================

                except requests.RequestException as exc:

                    logger.exception(
                        "Backend request failed."
                    )

                    st.error(
                        (
                            "Could not reach the "
                            "Aegis API. "
                            f"{exc}"
                        )
                    )


# ============================================================
# REVIEW ANALYTICS
# ============================================================

with tab_analytics:

    st.subheader(
        "Review Analytics"
    )

    st.caption(
        "Structured metrics generated from "
        "automated GitHub pull-request reviews."
    )


    # ========================================================
    # EMPTY STATE
    # ========================================================

    if df_reviews.empty:

        st.info(
            "No pull-request reviews yet. "
            "Analytics will appear after Aegis AI "
            "processes its first GitHub pull request."
        )

        st.markdown(
            """
### Start collecting review data

1. Configure `GITHUB_WEBHOOK_SECRET`.
2. Configure `GITHUB_TOKEN`.
3. Start Redis.
4. Start the Celery worker.
5. Configure the GitHub webhook.
6. Open or update a pull request.

Aegis will then review the PR and store
structured analytics in Supabase.
"""
        )


    # ========================================================
    # ANALYTICS AVAILABLE
    # ========================================================

    else:

        data = (
            df_reviews.copy()
        )


        # ====================================================
        # NORMALIZE CREATED_AT
        # ====================================================

        if (
            "created_at"
            in data.columns
        ):

            data[
                "created_at"
            ] = pd.to_datetime(
                data[
                    "created_at"
                ],
                errors="coerce",
                utc=True,
            )


        # ====================================================
        # CORE METRICS
        # ====================================================

        total_reviews = len(
            data
        )

        if (
            "repo_name"
            in data.columns
        ):

            active_repositories = int(
                data[
                    "repo_name"
                ].nunique()
            )

        else:

            active_repositories = 0


        scores = numeric_column(
            data,
            "overall_score",
        )

        valid_scores = (
            scores.dropna()
        )

        if not valid_scores.empty:

            average_score = (
                valid_scores.mean()
            )

        else:

            average_score = None


        high_risk_reviews = count_risk(
            data,
            [
                "High",
                "Critical",
            ],
        )

        findings = numeric_column(
            data,
            "issue_count",
        ).dropna()

        average_findings = (
            findings.mean()
            if not findings.empty
            else None
        )

        highest_score = (
            valid_scores.max()
            if not valid_scores.empty
            else None
        )

        lowest_score = (
            valid_scores.min()
            if not valid_scores.empty
            else None
        )

        success_rate = (
            100 * (total_reviews - high_risk_reviews) / total_reviews
            if total_reviews
            else None
        )


        # ====================================================
        # TOP KPI CARDS
        # ====================================================

        kpi_1, kpi_2, kpi_3, kpi_4 = (
            st.columns(4)
        )

        kpi_1.metric(
            "PRs Reviewed",
            total_reviews,
        )

        kpi_2.metric(
            "Average Score",
            (
                f"{average_score:.1f}/100"
                if average_score is not None
                else "N/A"
            ),
        )

        kpi_3.metric(
            "High-Risk PRs",
            high_risk_reviews,
        )

        kpi_4.metric(
            "Repositories",
            active_repositories,
        )


        kpi_5, kpi_6, kpi_7, kpi_8 = (
            st.columns(4)
        )

        kpi_5.metric(
            "Avg Findings / PR",
            (
                f"{average_findings:.1f}"
                if average_findings is not None
                else "N/A"
            ),
        )

        kpi_6.metric(
            "Highest Score",
            (
                f"{highest_score:.0f}/100"
                if highest_score is not None
                else "N/A"
            ),
        )

        kpi_7.metric(
            "Lowest Score",
            (
                f"{lowest_score:.0f}/100"
                if lowest_score is not None
                else "N/A"
            ),
        )

        kpi_8.metric(
            "Success Rate",
            (
                f"{success_rate:.0f}%"
                if success_rate is not None
                else "N/A"
            ),
            help="Share of reviewed PRs that were not High or Critical risk.",
        )


        st.divider()


        # ====================================================
        # SCORE TREND
        # ====================================================

        if (
            "created_at"
            in data.columns
            and
            "overall_score"
            in data.columns
        ):

            trend_data = (
                data[
                    [
                        "created_at",
                        "overall_score",
                    ]
                ]
                .copy()
            )

            trend_data[
                "overall_score"
            ] = pd.to_numeric(
                trend_data[
                    "overall_score"
                ],
                errors="coerce",
            )

            trend_data = (
                trend_data
                .dropna(
                    subset=[
                        "created_at",
                        "overall_score",
                    ]
                )
                .sort_values(
                    "created_at"
                )
            )


            if not trend_data.empty:

                st.markdown(
                    "### 📈 Code Score Trend"
                )

                trend_chart = (
                    trend_data
                    .set_index(
                        "created_at"
                    )[
                        [
                            "overall_score"
                        ]
                    ]
                )

                st.line_chart(
                    trend_chart,
                    use_container_width=True,
                )


        # ====================================================
        # FINDINGS BY SEVERITY
        # ====================================================

        severity_columns = [
            "critical_count",
            "high_count",
            "medium_count",
            "low_count",
        ]

        available_severity_columns = [
            column
            for column in severity_columns
            if column in data.columns
        ]


        if available_severity_columns:

            severity_totals = (
                data[
                    available_severity_columns
                ]
                .apply(
                    pd.to_numeric,
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )

            severity_totals.index = [
                name
                .replace(
                    "_count",
                    "",
                )
                .replace(
                    "_",
                    " ",
                )
                .title()

                for name
                in severity_totals.index
            ]


            st.markdown(
                "### 🚨 Findings by Severity"
            )

            st.bar_chart(
                severity_totals,
                use_container_width=True,
            )


        # ====================================================
        # RISK DISTRIBUTION
        # ====================================================

        if (
            "risk_level"
            in data.columns
        ):

            risk_distribution = (
                data[
                    "risk_level"
                ]
                .dropna()
                .value_counts()
            )


            if not risk_distribution.empty:

                st.markdown(
                    "### 🛡️ Risk Distribution"
                )

                st.bar_chart(
                    risk_distribution,
                    use_container_width=True,
                )


        # ====================================================
        # REPOSITORY PERFORMANCE
        # ====================================================

        if (
            "repo_name"
            in data.columns
        ):

            repo_data = (
                data.copy()
            )

            repo_data[
                "overall_score"
            ] = numeric_column(
                repo_data,
                "overall_score",
            )


            repository_summary = (
                repo_data
                .groupby(
                    "repo_name",
                    dropna=False,
                )
                .agg(
                    Reviews=(
                        "repo_name",
                        "size",
                    ),

                    Average_Score=(
                        "overall_score",
                        "mean",
                    ),
                )
                .reset_index()
            )


            repository_summary = (
                repository_summary.rename(
                    columns={
                        "repo_name": (
                            "Repository"
                        ),
                        "Average_Score": (
                            "Average Score"
                        ),
                    }
                )
            )


            repository_summary[
                "Average Score"
            ] = (
                repository_summary[
                    "Average Score"
                ]
                .round(1)
            )


            st.markdown(
                "### 📦 Repository Overview"
            )

            st.dataframe(
                repository_summary,
                use_container_width=True,
                hide_index=True,
            )


        # ====================================================
        # REVIEW PERFORMANCE
        # ====================================================

        durations = numeric_column(
            data,
            "review_duration_ms",
        ).dropna()


        if not durations.empty:

            average_duration_seconds = (
                durations.mean()
                / 1000
            )

            st.markdown(
                "### ⚡ Review Performance"
            )

            perf_1, perf_2 = (
                st.columns(2)
            )

            perf_1.metric(
                "Average Review Time",
                (
                    f"{average_duration_seconds:.1f}s"
                ),
            )

            perf_2.metric(
                "Fastest Review",
                (
                    f"{durations.min() / 1000:.1f}s"
                ),
            )


        # ====================================================
        # RECENT REVIEWS
        # ====================================================

        st.markdown(
            "### 🕒 Recent Reviews"
        )

        repo_search = st.text_input(
            "Search repository",
            placeholder="e.g. my-org/my-repo",
        )

        wanted_columns = [
            "created_at",
            "repo_name",
            "pr_number",
            "overall_score",
            "risk_level",
            "issue_count",
            "critical_count",
            "high_count",
            "medium_count",
            "low_count",
            "review_duration_ms",
        ]

        visible_columns = [
            column
            for column in wanted_columns
            if column in data.columns
        ]


        if visible_columns:

            recent_reviews = (
                data[
                    visible_columns
                ].copy()
            )

            if (
                repo_search
                and "repo_name" in recent_reviews.columns
            ):

                recent_reviews = recent_reviews[
                    recent_reviews["repo_name"]
                    .astype(str)
                    .str.contains(
                        repo_search,
                        case=False,
                        na=False,
                    )
                ]

            if (
                "created_at"
                in recent_reviews.columns
            ):

                recent_reviews = (
                    recent_reviews
                    .sort_values(
                        "created_at",
                        ascending=False,
                    )
                )


            # Convert milliseconds into a more readable value.

            if (
                "review_duration_ms"
                in recent_reviews.columns
            ):

                recent_reviews[
                    "review_duration_ms"
                ] = (
                    pd.to_numeric(
                        recent_reviews[
                            "review_duration_ms"
                        ],
                        errors="coerce",
                    )
                    / 1000
                ).round(1)

                recent_reviews = (
                    recent_reviews.rename(
                        columns={
                            "review_duration_ms": (
                                "review_seconds"
                            )
                        }
                    )
                )


            recent_reviews = (
                recent_reviews.rename(
                    columns={
                        "created_at": "Reviewed At",
                        "repo_name": "Repository",
                        "pr_number": "PR",
                        "overall_score": "Score",
                        "risk_level": "Risk",
                        "issue_count": "Findings",
                        "critical_count": "Critical",
                        "high_count": "High",
                        "medium_count": "Medium",
                        "low_count": "Low",
                        "review_seconds": (
                            "Review Time (s)"
                        ),
                    }
                )
            )


            st.dataframe(
                recent_reviews,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download CSV",
                recent_reviews.to_csv(index=False),
                file_name="aegis_reviews.csv",
                mime="text/csv",
            )

        else:

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Aegis AI — Made by Paras  ;Powered by FastAPI, LangGraph, Gemini, "
    "Supabase, and Streamlit."
)
