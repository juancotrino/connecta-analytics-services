from typing import get_args

from app.core.big_query import BigQueryClient, bigquery, get_bigquery_type
from app.models.study import Study


class StudyRepository:
    def __init__(self):
        self.bq = BigQueryClient("business_data")
        self.ALLOWED_FILTERS = [
            "study_id",
            "status",
            "country",
            "client",
            "methodology",
            "study_type",
        ]

    def get_study(self, study_id: int) -> Study: ...

    def get_studies(self) -> list[Study]: ...

    def query_studies(self, limit: int, offset: int, **kwargs) -> list[Study]:
        query_params = []
        conditions = []

        for _filter in self.ALLOWED_FILTERS:  # Only use predefined filters
            if _filter in kwargs and kwargs[_filter]:
                param_values = kwargs[_filter]

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

    def create_study(self, study: Study) -> None: ...

    def update_study(self, study: Study) -> None: ...

    def delete_study(self, study_id: int) -> None: ...
