from typing import get_args, TYPE_CHECKING

from app.core.big_query import BigQueryClient, bigquery, get_bigquery_type
from app.models.study import Study

if TYPE_CHECKING:
    import pandas as pd


class StudyRepository:
    def __init__(self):
        self.bq = BigQueryClient("business_data")
        self.ALLOWED_FILTERS = [
            "study_id",
            "study_name",
            "status",
            "country",
            "client",
            "methodology",
            "study_type",
        ]

    def get_study(self, study_id: int) -> Study:
        query = f"""
            SELECT *
            FROM `{self.bq.schema_id}.{self.bq.data_set}.study`
            WHERE study_id = @study_id
        """
        query_params = [bigquery.ScalarQueryParameter("study_id", "INT64", study_id)]
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = self.bq.client.query(query, job_config=job_config)

        return Study(**dict(query_job))

    def get_studies(self) -> list[Study]: ...

    def get_total_studies(self) -> int:
        query = f"""
            SELECT COUNT(study_id) AS total_studies
            FROM `{self.bq.schema_id}.{self.bq.data_set}.study`
        """
        return self.bq.fetch_data(query)["total_studies"][0]

    def query_studies(self, limit: int, offset: int, **kwargs) -> list[Study]:
        query_params = []
        conditions = []

        for _filter in self.ALLOWED_FILTERS:  # Only use predefined filters
            if _filter in kwargs and kwargs[_filter]:
                param_values = kwargs[_filter]
                if not isinstance(param_values, list):
                    param_values = [param_values]

                # Get the expected Python type from the Pydantic model
                py_type = get_args(Study.model_fields[_filter].annotation)[0]
                bq_type = get_bigquery_type(py_type)

                # Handle multiple values with IN clause
                param_placeholders = ", ".join(
                    [f"@{_filter}_{i}" for i in range(len(param_values))]
                )
                conditions.append(f"{_filter} IN ({param_placeholders})")

                # Append query parameters
                for i, value in enumerate(param_values):
                    query_params.append(
                        bigquery.ScalarQueryParameter(f"{_filter}_{i}", bq_type, value)
                    )

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT *
            FROM `{self.bq.schema_id}.{self.bq.data_set}.study`
            {where_clause}
            ORDER BY study_id DESC
            LIMIT @limit OFFSET @offset
        """

        query_params.extend(
            [
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
                bigquery.ScalarQueryParameter("offset", "INT64", offset),
            ]
        )

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = self.bq.client.query(query, job_config=job_config)

        return [Study(**dict(row)) for row in query_job]

    def create_study(self, study_df: "pd.DataFrame") -> None:
        self.bq.load_data("study", study_df)

    def update_study(self, study_id: int, study_df: "pd.DataFrame") -> None:
        self.delete_study(study_id)
        self.create_study(study_df)

    def delete_study(self, study_id: int) -> None:
        query = f"""
            DELETE `{self.bq.schema_id}.{self.bq.data_set}.study`
            WHERE study_id = @study_id
        """
        query_params = [
            bigquery.ScalarQueryParameter("study_id", "INT64", study_id),
        ]
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        self.bq.delete_data(query, job_config)

    def _get_last_id_number(self) -> int:
        last_study_number = self.bq.fetch_data(
            f"""
            SELECT MAX(study_id) AS study_id FROM `{self.bq.schema_id}.{self.bq.data_set}.study`
            """
        )["study_id"][0]

        return last_study_number
