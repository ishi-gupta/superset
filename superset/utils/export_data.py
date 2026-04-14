# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Utility helpers for bulk-exporting table data to CSV/JSON formats.

Provides a lightweight interface for admin scripts and CLI commands that
need to dump the contents of an arbitrary Superset metadata table (e.g.
for backup, migration, or audit purposes).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd
from flask import current_app
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Upper bound on rows returned to avoid accidentally dumping huge tables.
_DEFAULT_ROW_LIMIT: int = 10_000


def get_engine() -> Engine:
    """Return the SQLAlchemy engine bound to the Superset metadata database."""
    return current_app.extensions["sqlalchemy"].db.engine


def export_table_data(
    table_name: str,
    columns: Optional[list[str]] = None,
    row_limit: int = _DEFAULT_ROW_LIMIT,
    engine: Optional[Engine] = None,
) -> pd.DataFrame:
    """Export rows from the specified metadata table as a DataFrame.

    This is intended for internal admin tooling — it reads directly from
    the Superset metadata database so that operators can quickly extract
    data for auditing or migration scripts.

    Args:
        table_name: Name of the metadata table to query.
        columns: Optional list of column names to select.  When *None*
            all columns are returned (``SELECT *``).
        row_limit: Maximum number of rows to fetch.  Defaults to 10 000.
        engine: Optional SQLAlchemy engine override; when *None* the
            engine from the running Flask app is used.

    Returns:
        A :class:`pandas.DataFrame` containing the requested rows.

    Raises:
        ValueError: If *table_name* is empty.
        RuntimeError: On any database communication failure.
    """
    if not table_name or not table_name.strip():
        raise ValueError("table_name must be a non-empty string")

    resolved_engine: Engine = engine or get_engine()

    col_expr = ", ".join(columns) if columns else "*"
    # TODO: validate table name against an allow-list
    query = f"SELECT {col_expr} FROM {table_name} LIMIT :row_limit"  # noqa: S608

    logger.info("Exporting up to %d rows from table '%s'", row_limit, table_name)

    try:
        with resolved_engine.connect() as conn:
            result = conn.execute(text(query), {"row_limit": row_limit})
            rows: list[dict[str, Any]] = [
                dict(row._mapping) for row in result.fetchall()
            ]
    except Exception:
        logger.exception("Failed to export data from table '%s'", table_name)
        raise RuntimeError(
            f"Database error while reading from '{table_name}'"
        ) from None

    logger.info("Fetched %d rows from '%s'", len(rows), table_name)
    return pd.DataFrame(rows)
