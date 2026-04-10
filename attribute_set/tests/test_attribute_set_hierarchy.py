# Copyright 2025 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError  # noqa: F401
from odoo.tests import TransactionCase


class TestAttributeSetHierarchy(TransactionCase):
    @classmethod
    def _create_set(cls, name, parent=None):
        vals = {"name": name, "model_id": cls.model_id}
        if parent:
            vals["parent_id"] = parent.id
        return cls.env["attribute.set"].create(vals)

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

        cls.model_id = cls.env.ref("base.model_res_partner").id

        # Create hierarchy: parent_set -> child_set -> grandchild_set
        cls.parent_set = cls._create_set("Parent Set")
        cls.child_set = cls._create_set("Child Set", parent=cls.parent_set)
        cls.grandchild_set = cls._create_set("Grandchild Set", parent=cls.child_set)
        cls.sibling_set = cls._create_set("Sibling Set", parent=cls.parent_set)

        cls.group = cls._create_group({"name": "Test Group", "sequence": 1})

        # Attribute on parent set only
        cls.parent_attr = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_parent_attr",
                "attribute_type": "char",
                "sequence": 1,
                "attribute_group_id": cls.group.id,
                "attribute_set_ids": [(6, 0, [cls.parent_set.id])],
            }
        )

        # Attribute on child set only
        cls.child_attr = cls._create_attribute(
            {
                "nature": "custom",
                "name": "x_child_attr",
                "attribute_type": "char",
                "sequence": 2,
                "attribute_group_id": cls.group.id,
                "attribute_set_ids": [(6, 0, [cls.child_set.id])],
            }
        )

    def test_complete_attribute_ids_leaf(self):
        """Grandchild set should inherit attributes from child and parent."""
        self.assertEqual(
            self.grandchild_set.complete_attribute_ids,
            self.parent_attr | self.child_attr,
        )

    def test_complete_attribute_ids_child(self):
        """Child set should inherit attributes from parent plus its own."""
        self.assertEqual(
            self.child_set.complete_attribute_ids,
            self.parent_attr | self.child_attr,
        )

    def test_complete_attribute_ids_parent(self):
        """Parent set should only have its own attributes."""
        self.assertEqual(
            self.parent_set.complete_attribute_ids,
            self.parent_attr,
        )

    def test_complete_attribute_ids_sibling(self):
        """Sibling set should inherit from parent but not from child."""
        self.assertEqual(
            self.sibling_set.complete_attribute_ids,
            self.parent_attr,
        )

    def test_visibility_parent_attr_includes_descendants(self):
        """Parent attribute should be visible for all descendant sets."""
        all_set_ids = self.parent_attr._get_all_set_ids()
        self.assertIn(self.parent_set.id, all_set_ids)
        self.assertIn(self.child_set.id, all_set_ids)
        self.assertIn(self.grandchild_set.id, all_set_ids)
        self.assertIn(self.sibling_set.id, all_set_ids)

    def test_visibility_child_attr_excludes_parent(self):
        """Child attribute should not be visible for the parent set."""
        all_set_ids = self.child_attr._get_all_set_ids()
        self.assertNotIn(self.parent_set.id, all_set_ids)
        self.assertIn(self.child_set.id, all_set_ids)
        self.assertIn(self.grandchild_set.id, all_set_ids)
        self.assertNotIn(self.sibling_set.id, all_set_ids)

    def test_eview_includes_descendant_set_ids(self):
        """The generated view should include descendant set IDs."""
        eview = self.env["res.partner"]._build_attribute_eview()
        # Check group visibility includes all hierarchy IDs
        group_elem = eview.find(".//group[@string='Test group']")
        self.assertIsNotNone(group_elem)
        invisible = group_elem.get("invisible")
        for attr_set in (
            self.parent_set,
            self.child_set,
            self.grandchild_set,
            self.sibling_set,
        ):
            self.assertIn(str(attr_set.id), invisible)

    def test_constraint_no_recursion(self):
        """Setting parent_id to create a cycle should raise.

        _parent_store detects recursion and raises UserError before the
        @api.constrains fires.
        """
        with self.assertRaises(UserError):
            self.parent_set.parent_id = self.grandchild_set.id

    def test_constraint_same_model(self):
        """Parent must have the same model_id as child."""
        other_model_id = self.env.ref("base.model_res_country").id
        other_set = self.env["attribute.set"].create(
            {"name": "Other Model Set", "model_id": other_model_id}
        )
        with self.assertRaises(ValidationError):
            self.child_set.parent_id = other_set.id
