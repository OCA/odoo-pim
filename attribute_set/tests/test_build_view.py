# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo.tests import Form, TransactionCase, users


class BuildViewCase(TransactionCase):
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

        # Demo user will be a base user to read model
        cls.demo = cls.env.ref("base.user_demo")

        # This user will have access to
        cls.attribute_manager_user = cls.env.ref("base.user_admin")
        cls.attribute_manager_user.write(
            {
                "name": "Attribute Manager",
                "login": "attribute_manager",
                "email": "attribute.manager@test.odoo.com",
            }
        )
        cls.attribute_manager_user.groups_id |= cls.env.ref("base.group_erp_manager")

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import ResCountry, ResPartner

        cls.loader.update_registry((ResPartner, ResCountry))

        # Create a new inherited view with the 'attributes' placeholder.
        cls.view = cls.env["ir.ui.view"].create(
            {
                "name": "res.partner.form.test",
                "model": "res.partner",
                "inherit_id": cls.env.ref("base.view_partner_form").id,
                "arch": """
                    <xpath expr="//notebook" position="inside">
                        <page name="partner_attributes">
                            <field name="attribute_set_id"/>
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

        cls.multi_attribute = cls._create_attribute(
            {
                "attribute_type": "multiselect",
                "name": "x_multi_attribute",
                "option_ids": [
                    (0, 0, {"name": "Value 1"}),
                    (0, 0, {"name": "Value 2"}),
                ],
                "attribute_set_ids": [(6, 0, [cls.set_1.id])],
                "attribute_group_id": cls.group_1.id,
            }
        )

        # Add attributes for country
        cls.model_id = cls.env.ref("base.model_res_country").id
        cls.be = cls.env.ref("base.be")
        cls.set_country = cls._create_set("Set Country")
        cls.model_id = cls.env.ref("base.model_res_partner").id

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    # TEST write on attributes
    @users("demo")
    def test_write_attribute_values_text(self):
        self.partner.write({"x_attr_2": "abcd"})
        self.assertEqual(self.partner.x_attr_2, "abcd")

    def test_write_attribute_values_select(self):
        self.partner.write({"x_attr_select": self.attr_select_option.id})
        self.assertEqual(self.partner.x_attr_select, self.attr_select_option)

    def _get_attr_element(self, name):
        eview = self.env["res.partner"]._build_attribute_eview()
        return eview.find(f"group/field[@name='{name}']")

    def test_group_order(self):
        eview = self.env["res.partner"]._build_attribute_eview()
        groups = [g.get("string") for g in eview.getchildren()]
        self.assertTrue(all(group in groups for group in ["Group 1", "Group 2"]))

        self.group_2.sequence = 0
        eview = self.env["res.partner"]._build_attribute_eview()
        groups = [g.get("string") for g in eview.getchildren()]
        self.assertTrue(all(group in groups for group in ["Group 1", "Group 2"]))

    def test_group_visibility(self):
        eview = self.env["res.partner"]._build_attribute_eview()
        group = eview.getchildren()[0]
        self.assertIn("attribute_set_id", group.get("invisible"))
        self.assertIn(f"{self.set_1.id}", group.get("invisible"))
        self.attr_1.attribute_set_ids += self.set_2
        eview = self.env["res.partner"]._build_attribute_eview()
        group = eview.getchildren()[0]
        self.assertIn("attribute_set_id", group.get("invisible"))
        self.assertIn(f"{self.set_1.id}", group.get("invisible"))
        self.assertIn(f"{self.set_2.id}", group.get("invisible"))

    def test_attribute_order(self):
        eview = self.env["res.partner"]._build_attribute_eview()
        attrs = []
        for child in eview.getchildren():
            for child2 in child.getchildren():
                if child2.tag == "field" and "name" in child2.attrib:
                    attrs.append(child2.get("name"))
        self.assertTrue(
            all(attr in attrs for attr in ["x_attr_2", "x_attr_1", "x_multi_attribute"])
        )

        self.attr_1.sequence = 3
        eview = self.env["res.partner"]._build_attribute_eview()
        attrs = []
        for child in eview.getchildren():
            for child2 in child.getchildren():
                if child2.tag == "field" and "name" in child2.attrib:
                    attrs.append(child2.get("name"))
        self.assertTrue(
            all(attr in attrs for attr in ["x_attr_2", "x_attr_1", "x_multi_attribute"])
        )

    def test_attr_visibility(self):
        invisible = self._get_attr_element("x_attr_1")
        self.assertIn("attribute_set_id", invisible.get("invisible"))
        self.assertIn(f"{self.set_1.id}", invisible.get("invisible"))

        self.attr_1.attribute_set_ids += self.set_2
        invisible = self._get_attr_element("x_attr_1")
        self.assertIn("attribute_set_id", invisible.get("invisible"))
        self.assertIn(f"{self.set_1.id}", invisible.get("invisible"))
        self.assertIn(f"{self.set_2.id}", invisible.get("invisible"))

    def test_attr_required(self):
        not_required = self._get_attr_element("x_attr_1")
        self.assertIsNone(not_required.get("required"))
        self.attr_1.required_on_views = True
        required = self._get_attr_element("x_attr_1")
        self.assertIn("attribute_set_id", required.get("required"))

    @users("attribute_manager")
    def test_render_all_field_type(self):
        field = self.env["attribute.attribute"]._fields["attribute_type"]
        for attr_type, _name in field.selection:
            name = f"x_test_render_{attr_type}"
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
    def _get_eview_from_get_views(self, include_native_attribute_view_ref=True):
        result = (
            self.env["res.partner"]
            .with_context(
                include_native_attribute_view_ref=include_native_attribute_view_ref
            )
            .get_views([(self.view.id, "form")])
        )
        return etree.fromstring(result["views"]["form"]["arch"])

    def test_include_native_attr(self):
        eview = self._get_eview_from_get_views()
        attr = eview.xpath(f"//field[@name='{self.attr_native.name}']")

        # Only one field with this name
        self.assertEqual(len(attr), 1)
        # The moved field is inside page "partner_attributes"
        self.assertEqual(attr[0].xpath("../../..")[0].get("name"), "partner_attributes")
        # It has the given visibility by its related attribute sets.
        self.assertIn("attribute_set_id", attr[0].get("invisible"))
        self.assertIn(f"{self.set_1.id}", attr[0].get("invisible"))
        self.assertIn(f"{self.set_2.id}", attr[0].get("invisible"))

    def test_native_readonly(self):
        eview = self._get_eview_from_get_views()
        attr = eview.xpath(f"//field[@name='{self.attr_native_readonly.name}']")
        self.assertTrue(attr[0].get("readonly"))

    def test_no_include_native_attr(self):
        # Run get_views on the test view with no "include_native_attribute_view_ref"
        eview = self._get_eview_from_get_views(include_native_attribute_view_ref=False)
        attr = eview.xpath(f"//field[@name='{self.attr_native.name}']")

        # Only one field with this name
        self.assertEqual(len(attr), 1)
        # And it is not in page "partner_attributes"
        self.assertFalse(
            eview.xpath(
                f"//page[@name='partner_attributes']//field[@name='{self.attr_native.name}']"
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

    # TEST form views rendering
    @users("attribute_manager")
    def test_model_form(self):
        # Test attributes modifications through form
        self.assertFalse(self.partner.x_attr_3)
        with Form(self.partner, view=self.view.id) as partner_form:
            partner_form.attribute_set_id = self.set_1
            partner_form.x_attr_3 = True
            partner_form.x_attr_select = self.attr_select_option
            partner_form.x_multi_attribute.add(self.multi_attribute.option_ids[0])
            pass
        partner = partner_form.save().with_user(self.attribute_manager_user)
        self.assertTrue(partner.x_attr_3)
        self.assertTrue(partner.x_attr_select)
        # As options are Many2many, Form() is not able to render the sub form
        # This should pass, checking fields are rendered without error with
        # demo user
        with Form(partner.x_multi_attribute):
            pass

    def test_models_fields_for_get_views(self):
        # this test is here to ensure that attributes defined in attribute_set
        # and added to the view are correctly added to the list of fields
        # to load for the view
        result = self.env["res.partner"].get_views([(self.view.id, "form")])
        fields = result["models"].get("res.partner").get("fields")
        self.assertIn("x_attr_1", fields)
        self.assertIn("x_attr_2", fields)
        self.assertIn("x_attr_3", fields)
        self.assertIn("x_attr_4", fields)

    @users("demo")
    def test_model_form_domain(self):
        # Test attributes modifications through form
        partner = self.partner.with_user(self.env.user)
        self.assertFalse(partner.x_attr_3)
        sets = partner.attribute_set_id.search(partner._get_attribute_set_owner_model())
        self.assertEqual(self.set_1 | self.set_2, sets)
