# Copyright 2025 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestAttributeSetHierarchyView(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        model_id = cls.env.ref("base.model_res_partner").id
        AttributeSet = cls.env["attribute.set"]
        cls.parent_set = AttributeSet.create(
            {"name": "Parent Set", "model_id": model_id}
        )
        cls.child_set = AttributeSet.create(
            {"name": "Child Set", "model_id": model_id, "parent_id": cls.parent_set.id}
        )
        cls.grandchild_set = AttributeSet.create(
            {
                "name": "Grandchild Set",
                "model_id": model_id,
                "parent_id": cls.child_set.id,
            }
        )
        cls.sibling_set = AttributeSet.create(
            {
                "name": "Sibling Set",
                "model_id": model_id,
                "parent_id": cls.parent_set.id,
            }
        )
        group = cls.env["attribute.group"].create(
            {"name": "Test Group", "model_id": model_id}
        )
        cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_parent_attr",
                "attribute_type": "char",
                "model_id": model_id,
                "attribute_group_id": group.id,
                "attribute_set_ids": [(6, 0, [cls.parent_set.id])],
            }
        )

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
