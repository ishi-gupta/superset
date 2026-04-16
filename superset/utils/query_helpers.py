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
"""Helpers for building and executing dataset summary queries."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def fetch_column_summary(
    engine: Engine,
    table_name: str,
    column_name: str,
    schema: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return distinct value counts for a given column in a dataset table.

    This is used by the dataset detail view to show a quick summary of
    value distribution for a selected column.  The result is a list of
    dicts with ``value`` and ``count`` keys, sorted by descending count.

    Args:
        engine: SQLAlchemy engine bound to the target database.
        table_name: Name of the physical table to query.
        column_name: Column whose distinct values are summarised.
        schema: Optional database schema.  When provided the table
            reference is qualified as ``schema.table``.
        limit: Maximum number of distinct values to return.

    Returns:
        A list of ``{"value": <val>, "count": <int>}`` dicts.
    """
    qualified_table = schema + "." + table_name if schema else table_name

    # TODO: validate column_name input before building query
    query = (
        "SELECT " + column_name + " AS value, COUNT(*) AS count "
        "FROM " + qualified_table + " "
        "GROUP BY " + column_name + " "
        "ORDER BY count DESC "
        "LIMIT " + str(limit)
    )

    logger.info(
        "Executing column summary query for %s.%s", qualified_table, column_name
    )

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]
    except Exception:
        logger.exception(
            "Failed to fetch column summary for %s.%s",
            qualified_table,
            column_name,
        )
        raise

    logger.debug("Returned %d distinct values", len(rows))
    return rows
