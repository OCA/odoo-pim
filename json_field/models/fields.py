# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright 2023 ACSONE SA/NV

import copy
import json

from psycopg2.extras import Json as PsycopgJson

from odoo import fields


class Json(fields.Field):
    """JSON Field that contain unstructured information in jsonb PostgreSQL column.
    This field is still in beta
    Some features have not been implemented and won't be implemented in stable versions,
    including:
    * searching
    * indexing
    * mutating the values.
    """

    type = "json"
    column_type = ("jsonb", "jsonb")

    def convert_to_record(self, value, record):
        """Return a copy of the value"""
        return False if value is None else copy.deepcopy(value)

    def convert_to_cache(self, value, record, validate=True):
        if not value:
            return None
        return json.loads(json.dumps(value))

    def convert_to_column(self, value, record, values=None, validate=True):
        if not value:
            return None
        return PsycopgJson(value)

    def convert_to_export(self, value, record):
        if not value:
            return ""
        return json.dumps(value)


fields.Json = Json
