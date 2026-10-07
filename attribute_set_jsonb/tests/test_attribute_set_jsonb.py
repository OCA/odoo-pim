# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests import TransactionCase
from odoo.tools import SQL, mute_logger

from ..hooks import post_init_hook

GIN_INDEX = "res_partner__x_custom_json_attrs_index"
_LOGGER = "odoo.addons.attribute_set_jsonb.models.attribute_attribute"


class TestAttributeSetJsonb(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.attribute = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_jsonb_color",
                "attribute_type": "char",
                "serialized": True,
                "model_id": cls.model_id,
                "attribute_group_id": cls.env["attribute.group"]
                .create({"name": "JSONB", "model_id": cls.model_id})
                .id,
            }
        )
        cls.serialization_field = cls.attribute.serialization_field_id
        cls.group = cls.attribute.attribute_group_id

    def _create_attribute(self, name, **vals):
        return self.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": name,
                "attribute_type": "char",
                "serialized": True,
                "model_id": self.model_id,
                "attribute_group_id": self.group.id,
                **vals,
            }
        )

    def _new_attribute(self, **vals):
        """An attribute not saved, to reach the guard clauses."""
        return self.env["attribute.attribute"].new(
            {"name": "x_jsonb_new", "model": "res.partner", **vals}
        )

    def _failing_execute(self, statement):
        """Patch the cursor so that queries containing statement fail in
        PostgreSQL, which aborts the transaction unless in a savepoint."""
        cr = self.env.cr
        execute = cr.execute

        def _execute(query, *args, **kwargs):
            if statement in str(query):
                return execute("SELECT 1 / 0")
            return execute(query, *args, **kwargs)

        return patch.object(cr, "execute", side_effect=_execute)

    def _query_one(self, query, *args):
        self.env.cr.execute(SQL(query, *args))
        row = self.env.cr.fetchone()
        return row and row[0]

    def _index_method(self, index_name):
        return self._query_one(
            "SELECT am.amname FROM pg_class i JOIN pg_am am ON am.oid = i.relam"
            " WHERE i.relname = %s AND i.relkind = 'i'",
            index_name,
        )

    def test_serialization_field_indexed(self):
        self.assertEqual(self.serialization_field.name, "x_custom_json_attrs")
        self.assertTrue(self.serialization_field.index)
        self.assertEqual(
            self._query_one(
                "SELECT udt_name FROM information_schema.columns"
                " WHERE table_name = 'res_partner'"
                " AND column_name = 'x_custom_json_attrs'"
            ),
            "jsonb",
        )
        self.assertEqual(self._index_method(GIN_INDEX), "gin")

    def test_serialized_value_stored(self):
        partner = self.env["res.partner"].create(
            {"name": "JSONB", "x_jsonb_color": "red"}
        )
        partner.flush_recordset()
        self.assertEqual(
            self._query_one(
                "SELECT x_custom_json_attrs->>'x_jsonb_color'"
                " FROM res_partner WHERE id = %s",
                partner.id,
            ),
            "red",
        )

    def test_post_init_hook_indexes_existing_field(self):
        self.serialization_field.write({"index": False})
        self.env.cr.execute(SQL("DROP INDEX %s", SQL.identifier(GIN_INDEX)))

        post_init_hook(self.env)

        self.assertTrue(self.serialization_field.index)
        self.assertEqual(self._index_method(GIN_INDEX), "gin")

    def test_expression_index(self):
        index_name = self.attribute._get_index_name()
        self.attribute.create_gin_index = True
        self.assertEqual(self._index_method(index_name), "btree")

        self.attribute.create_gin_index = False
        self.assertIsNone(self._index_method(index_name))

    def test_expression_index_on_create(self):
        attribute = self._create_attribute("x_jsonb_size", create_gin_index=True)
        self.assertEqual(self._index_method(attribute._get_index_name()), "btree")

    def test_expression_index_dropped_on_unlink(self):
        attribute = self._create_attribute("x_jsonb_brand", create_gin_index=True)
        index_name = attribute._get_index_name()
        attribute.unlink()
        self.assertIsNone(self._index_method(index_name))

    def test_expression_index_already_exists(self):
        self.attribute.create_gin_index = True
        with mute_logger(_LOGGER):
            self.assertTrue(self.attribute._create_expression_index())

    def test_expression_index_non_serialized(self):
        attribute = self._new_attribute(serialized=False)
        self.assertFalse(attribute._create_expression_index())

    def test_expression_index_missing_info(self):
        attribute = self._new_attribute(serialized=True)
        self.assertIsNone(attribute._get_index_name())
        self.assertIsNone(attribute._get_jsonb_column_name())
        self.assertFalse(attribute._drop_expression_index())
        with mute_logger(_LOGGER):
            self.assertFalse(attribute._create_expression_index())

    def test_expression_index_missing_table(self):
        attribute = self._new_attribute(
            serialized=True,
            model="x_jsonb.missing",
            serialization_field_id=self.serialization_field.id,
        )
        with mute_logger(_LOGGER):
            self.assertFalse(attribute._create_expression_index())

    def test_expression_index_missing_column(self):
        attribute = self._new_attribute(
            serialized=True,
            model="res.users",
            serialization_field_id=self.serialization_field.id,
        )
        with mute_logger(_LOGGER):
            self.assertFalse(attribute._create_expression_index())

    def test_table_name_without_model(self):
        self.assertIsNone(self._new_attribute(model=False)._get_table_name())

    def test_index_name(self):
        attribute = self._new_attribute(
            name="jsonb_" + "x" * 80,
            serialization_field_id=self.serialization_field.id,
        )
        index_name = attribute._get_index_name()
        self.assertTrue(index_name.startswith("idx_res_partner_jsonb_"))
        self.assertTrue(index_name.endswith("_expr"))
        self.assertLessEqual(len(index_name), 63)

    def test_expression_index_create_error(self):
        with self._failing_execute("CREATE INDEX"), mute_logger(_LOGGER, "odoo.sql_db"):
            self.assertFalse(self.attribute._create_expression_index())
        # the transaction is still usable
        self.assertEqual(self.env["res.partner"].search_count([("id", "=", 0)]), 0)

    def test_expression_index_drop_error(self):
        with self._failing_execute("DROP INDEX"), mute_logger(_LOGGER, "odoo.sql_db"):
            self.assertFalse(self.attribute._drop_expression_index())
        # the transaction is still usable
        self.assertEqual(self.env["res.partner"].search_count([("id", "=", 0)]), 0)

    def test_regenerate_all_indexes(self):
        self.attribute.create_gin_index = True
        index_name = self.attribute._get_index_name()
        self.env.cr.execute(SQL("DROP INDEX %s", SQL.identifier(index_name)))

        result = self.attribute.action_regenerate_all_indexes()

        self.assertEqual(self._index_method(index_name), "btree")
        self.assertEqual(result["params"]["type"], "success")

    def test_regenerate_all_indexes_failure(self):
        self.attribute.create_gin_index = True
        self.env.cr.execute(
            SQL("DROP INDEX %s", SQL.identifier(self.attribute._get_index_name()))
        )
        with self._failing_execute("CREATE INDEX"), mute_logger(_LOGGER, "odoo.sql_db"):
            result = self.attribute.action_regenerate_all_indexes()
        self.assertEqual(result["params"]["type"], "warning")
