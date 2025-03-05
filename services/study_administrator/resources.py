from big_query import BigQueryClient

filters = ["study_id", "status", "country", "client", "methodology", "study_type"]

bq = BigQueryClient("business_data")


def get_studies(limit: int = 50, offset: int = 0, **kwargs) -> list[dict]:
    # Dictionary mapping statuses to emojis
    status_emojis = {
        "Propuesta": "💡 Propuesta",
        "En ejecución": "🔨 En ejecución",
        "Cancelado": "❌ Cancelado",
        "No aprobado": "🚫 No aprobado",
        "Finalizado": "✅ Finalizado",
    }

    kwargs_statements = []
    for _filter in filters:
        if kwargs.get(_filter):
            if _filter == "study_id":
                filter_list = ", ".join(
                    [str(element) for element in kwargs.get(_filter)]
                )
                kwargs_statements.append(f"{_filter} IN ({filter_list})")
            else:
                filter_list = "', '".join(kwargs.get(_filter))
                kwargs_statements.append(f"{_filter} IN ('{filter_list}')")

    kwargs_query = " AND ".join(kwargs_statements)
    if kwargs_statements:
        kwargs_query = f"WHERE {kwargs_query}"

    query = f"""
        SELECT * FROM `{bq.schema_id}.{bq.data_set}.study`
        {kwargs_query}
        ORDER BY study_id DESC
        LIMIT {limit} OFFSET {offset}
    """

    studies_data = bq.fetch_data(query)

    studies_data["status"] = studies_data["status"].apply(
        lambda x: status_emojis.get(x, x)
    )
    studies_data = (
        studies_data.rename(columns={"study_id": "Study ID"})
        .set_index("Study ID")
        .sort_index(ascending=False)
    )
    studies_data["creation_date"] = (
        studies_data["creation_date"]
        .dt.tz_localize("UTC")
        .dt.tz_convert("America/Bogota")
        .dt.tz_localize(None)
    )
    studies_data["last_update_date"] = (
        studies_data["last_update_date"]
        .dt.tz_localize("UTC")
        .dt.tz_convert("America/Bogota")
        .dt.tz_localize(None)
    )
    return studies_data.reset_index().to_dict(orient="records")
