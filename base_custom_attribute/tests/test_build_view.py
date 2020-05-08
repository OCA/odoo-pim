# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import ast

from odoo_test_helper import FakeModelLoader

from odoo.tests import SavepointCase


class BuildViewCase(SavepointCase):
    @classmethod
    def _create_set(cls, name):
        return cls.env["attribute.set"].create({"name": name, "model_id": cls.model_id})

    @classmethod
    def _create_group(cls, vals):
        vals["model_id"] = cls.model_id
        return cls.env["attribute.group"].create(vals)

    @classmethod
    def _create_attribute(cls, vals):
        vals["model_id"] = cls.model_id
        return cls.env["attribute.attribute"].create(vals)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import ResPartner

        cls.loader.update_registry((ResPartner,))
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.set_1 = cls._create_set("Set 1")
        cls.set_2 = cls._create_set("Set 2")
        cls.group_1 = cls._create_group({"name": "Group 1", "sequence": 1})
        cls.group_2 = cls._create_group({"name": "Group 2", "sequence": 2})
        cls.attr_1 = cls._create_attribute(
            {
                "is_custom": True,
                "name": "x_attr_1",
                "attribute_type": "char",
                "sequence": 1,
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id])],
            }
        )
        cls.attr_2 = cls._create_attribute(
            {
                "is_custom": True,
                "name": "x_attr_2",
                "attribute_type": "text",
                "sequence": 2,
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id])],
            }
        )
        cls.attr_3 = cls._create_attribute(
            {
                "is_custom": True,
                "name": "x_attr_3",
                "attribute_type": "boolean",
                "sequence": 1,
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id, cls.set_2.id])],
            }
        )
        cls.attr_4 = cls._create_attribute(
            {
                "is_custom": True,
                "name": "x_attr_4",
                "attribute_type": "date",
                "sequence": 2,
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id, cls.set_2.id])],
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(BuildViewCase, cls).tearDownClass()

    def _check_attrset_visiblility(self, attrs, set_ids):
        attrs = ast.literal_eval(attrs)
        self.assertIn("invisible", attrs)
        domain = attrs["invisible"][0]
        self.assertEqual("attribute_set_id", domain[0])
        self.assertEqual("not in", domain[1])
        self.assertEqual(
            set(set_ids),
            set(domain[2]),
            "Expected {}, get {}".format(set(set_ids), set(domain[2])),
        )

    def _get_attr_element(self, name):
        views = self.env["res.partner"]._build_attribute_view()
        return views.find("group/field[@name='{}']".format(name))

    def test_group_order(self):
        views = self.env["res.partner"]._build_attribute_view()
        groups = [g.get("string") for g in views.getchildren()]
        self.assertEqual(groups, ["Group 1", "Group 2"])

        self.group_1.sequence = 3
        views = self.env["res.partner"]._build_attribute_view()
        groups = [g.get("string") for g in views.getchildren()]
        self.assertEqual(groups, ["Group 2", "Group 1"])

    def test_group_visibility(self):
        views = self.env["res.partner"]._build_attribute_view()
        group = views.getchildren()[0]
        self._check_attrset_visiblility(group.get("attrs"), [self.set_1.id])

        self.attr_1.attribute_set_ids += self.set_2
        views = self.env["res.partner"]._build_attribute_view()
        group = views.getchildren()[0]
        self._check_attrset_visiblility(
            group.get("attrs"), [self.set_1.id, self.set_2.id]
        )

    def test_attribute_order(self):
        views = self.env["res.partner"]._build_attribute_view()
        attrs = [
            item.get("name")
            for item in views.getchildren()[0].getchildren()
            if item.tag == "field"
        ]
        self.assertEqual(attrs, ["x_attr_1", "x_attr_2"])

        self.attr_1.sequence = 3
        views = self.env["res.partner"]._build_attribute_view()
        attrs = [
            item.get("name")
            for item in views.getchildren()[0].getchildren()
            if item.tag == "field"
        ]
        self.assertEqual(attrs, ["x_attr_2", "x_attr_1"])

    def test_attr_visibility(self):
        attrs = self._get_attr_element("x_attr_1").get("attrs")
        self._check_attrset_visiblility(attrs, [self.set_1.id])

        self.attr_1.attribute_set_ids += self.set_2
        attrs = self._get_attr_element("x_attr_1").get("attrs")
        self._check_attrset_visiblility(attrs, [self.set_1.id, self.set_2.id])

    def test_attr_required(self):
        required = self._get_attr_element("x_attr_1").get("required")
        self.assertEqual(required, "False")

        self.attr_1.required_on_views = True
        required = self._get_attr_element("x_attr_1").get("required")
        self.assertEqual(required, "True")

    def test_render_all_field_type(self):
        field = self.env["attribute.attribute"]._fields["attribute_type"]
        for attr_type, _name in field.selection:
            name = "x_test_render_{}".format(attr_type)
            self._create_attribute(
                {
                    "is_custom": True,
                    "name": name,
                    "attribute_type": attr_type,
                    "sequence": 1,
                    "attribute_group_id": self.group_1.id,
                    "attribute_set_ids": [(6, 0, [self.set_1.id])],
                }
            )
            attr = self._get_attr_element(name)
            self.assertIsNotNone(attr)
            if attr_type == "text":
                self.assertTrue(attr.get("nolabel"))
                previous = attr.getprevious()
                self.assertEqual(previous.tag, "b")
            else:
                self.assertFalse(attr.get("nolabel", False))
