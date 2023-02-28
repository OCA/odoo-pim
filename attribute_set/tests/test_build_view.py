# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import ast

from lxml import etree
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

        # Create a new inherited view with the 'attributes' placeholder.
        cls.view = cls.env["ir.ui.view"].create(
            {
                "name": "res.partner.form.test",
                "model": "res.partner",
                "inherit_id": cls.env.ref("base.view_partner_form").id,
                "arch": """
                    <xpath expr="//notebook" position="inside">
                        <page name="partner_attributes">
                            <separator name="attributes_placeholder" />
                        </page>
                    </xpath>
                """,
            }
        )
        # Create some attributes
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.set_1 = cls._create_set("Set 1")
        cls.set_2 = cls._create_set("Set 2")
        cls.group_1 = cls._create_group({"name": "Group 1", "sequence": 1})
        cls.group_2 = cls._create_group({"name": "Group 2", "sequence": 2})
        cls.attr_1 = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_attr_1",
                "attribute_type": "char",
                "sequence": 1,
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id])],
            }
        )
        cls.attr_2 = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_attr_2",
                "attribute_type": "text",
                "sequence": 2,
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id])],
            }
        )
        cls.attr_3 = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_attr_3",
                "attribute_type": "boolean",
                "sequence": 1,
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id, cls.set_2.id])],
            }
        )
        cls.attr_4 = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_attr_4",
                "attribute_type": "date",
                "sequence": 2,
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id, cls.set_2.id])],
            }
        )
        cls.attr_select = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_attr_select",
                "attribute_type": "select",
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id])],
            }
        )
        cls.attr_select_option = cls.env["attribute.option"].create(
            {"name": "Option 1", "attribute_id": cls.attr_select.id}
        )
        cls.attr_native = cls._create_attribute(
            {
                "nature": "native",
                "field_id": cls.env.ref("base.field_res_partner__category_id").id,
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id, cls.set_2.id])],
            }
        )
        cls.attr_native_readonly = cls._create_attribute(
            {
                "nature": "native",
                "field_id": cls.env.ref("base.field_res_partner__create_uid").id,
                "attribute_group_id": cls.group_2.id,
                "attribute_set_ids": [(6, 0, [cls.set_1.id, cls.set_2.id])],
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(BuildViewCase, cls).tearDownClass()

    # TEST write on attributes
    def test_write_attribute_values_text(self):
        self.partner.write({"x_attr_2": "abcd"})
        self.assertEqual(self.partner.x_attr_2, "abcd")

    def test_write_attribute_values_select(self):
        self.partner.write({"x_attr_select": self.attr_select_option.id})
        self.assertEqual(self.partner.x_attr_select, self.attr_select_option)

    # TEST render partner's view with attribute's place_holder
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

    def _check_attrset_required(self, attrs, set_ids):
        attrs = ast.literal_eval(attrs)
        self.assertIn("required", attrs)
        domain = attrs["required"][0]
        self.assertEqual("attribute_set_id", domain[0])
        self.assertEqual("in", domain[1])
        self.assertEqual(
            set(set_ids),
            set(domain[2]),
            "Expected {}, get {}".format(set(set_ids), set(domain[2])),
        )

    def _get_attr_element(self, name):
        eview = self.env["res.partner"]._build_attribute_eview()
        return eview.find("group/field[@name='{}']".format(name))

    def test_group_order(self):
        eview = self.env["res.partner"]._build_attribute_eview()
        groups = [g.get("string") for g in eview.getchildren()]
        self.assertEqual(groups, ["Group 1", "Group 2"])

        self.group_2.sequence = 0
        eview = self.env["res.partner"]._build_attribute_eview()
        groups = [g.get("string") for g in eview.getchildren()]
        self.assertEqual(groups, ["Group 2", "Group 1"])

    def test_group_visibility(self):
        eview = self.env["res.partner"]._build_attribute_eview()
        group = eview.getchildren()[0]
        self._check_attrset_visiblility(group.get("attrs"), [self.set_1.id])

        self.attr_1.attribute_set_ids += self.set_2
        eview = self.env["res.partner"]._build_attribute_eview()
        group = eview.getchildren()[0]
        self._check_attrset_visiblility(
            group.get("attrs"), [self.set_1.id, self.set_2.id]
        )

    def test_attribute_order(self):
        eview = self.env["res.partner"]._build_attribute_eview()
        attrs = [
            item.get("name")
            for item in eview.getchildren()[0].getchildren()
            if item.tag == "field"
        ]
        self.assertEqual(attrs, ["x_attr_1", "x_attr_2"])

        self.attr_1.sequence = 3
        eview = self.env["res.partner"]._build_attribute_eview()
        attrs = [
            item.get("name")
            for item in eview.getchildren()[0].getchildren()
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
        attrs = self._get_attr_element("x_attr_1").get("attrs")
        attrs = ast.literal_eval(attrs)
        self.assertNotIn("required", attrs)

        self.attr_1.required_on_views = True
        attrs = self._get_attr_element("x_attr_1").get("attrs")
        self._check_attrset_required(attrs, [self.set_1.id])

    def test_render_all_field_type(self):
        field = self.env["attribute.attribute"]._fields["attribute_type"]
        for attr_type, _name in field.selection:
            name = "x_test_render_{}".format(attr_type)
            self._create_attribute(
                {
                    "nature": "custom",
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

    # TEST on NATIVE ATTRIBUTES
    def _get_eview_from_fields_view_get(self, include_native_attribute=True):
        fields_view = (
            self.env["res.partner"]
            .with_context({"include_native_attribute": include_native_attribute})
            .fields_view_get(
                view_id=self.view.id, view_type="form", toolbar=False, submenu=False
            )
        )
        return etree.fromstring(fields_view["arch"])

    def test_include_native_attr(self):
        eview = self._get_eview_from_fields_view_get()
        attr = eview.xpath("//field[@name='{}']".format(self.attr_native.name))

        # Only one field with this name
        self.assertEqual(len(attr), 1)
        # The moved field is inside page "partner_attributes"
        self.assertEqual(attr[0].xpath("../../..")[0].get("name"), "partner_attributes")
        # It has the given visibility by its related attribute sets.
        self._check_attrset_visiblility(
            attr[0].get("attrs"), [self.set_1.id, self.set_2.id]
        )

    def test_native_readonly(self):
        eview = self._get_eview_from_fields_view_get()
        attr = eview.xpath("//field[@name='{}']".format(self.attr_native_readonly.name))
        self.assertTrue(attr[0].get("readonly"))

    def test_no_include_native_attr(self):
        # Run fields_view_get on the test view with no "include_native_attribute"
        eview = self._get_eview_from_fields_view_get(include_native_attribute=False)
        attr = eview.xpath("//field[@name='{}']".format(self.attr_native.name))

        # Only one field with this name
        self.assertEqual(len(attr), 1)
        # And it is not in page "partner_attributes"
        self.assertFalse(
            eview.xpath(
                "//page[@name='partner_attributes']//field[@name='{}']".format(
                    self.attr_native.name
                )
            )
        )

    # TESTS UNLINK
    def test_unlink_custom_attribute(self):
        attr_1_field_id = self.attr_1.field_id.id
        self.attr_1.unlink()
        self.assertFalse(self.env["ir.model.fields"].browse([attr_1_field_id]).exists())

    def test_unlink_native_attribute(self):
        attr_native_field_id = self.attr_native.field_id.id
        self.attr_native.unlink()
        self.assertTrue(
            self.env["ir.model.fields"].browse([attr_native_field_id]).exists()
        )
