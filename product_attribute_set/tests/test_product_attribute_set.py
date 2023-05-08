# 2023 Copyright ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestProductAttributeSet(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Models
        cls.product_ctg_model = cls.env["product.category"]
        cls.product_tmpl_model = cls.env["product.template"]
        cls.attribute_set_model = cls.env["attribute.set"]
        cls.product_tmpl_odoo_model = cls.env.ref("product.model_product_template")

        # Instances
        cls.attribute_set_01 = cls.attribute_set_model.create(
            {"name": "Attribute Set 01", "model_id": cls.product_tmpl_odoo_model.id}
        )
        cls.attribute_set_02 = cls.attribute_set_model.create(
            {"name": "Attribute Set 02", "model_id": cls.product_tmpl_odoo_model.id}
        )
        cls.product_ctg_01 = cls.product_ctg_model.create({"name": "Category 01"})
        cls.product_ctg_02 = cls.product_ctg_model.create(
            {"name": "Category 02", "attribute_set_id": cls.attribute_set_02.id}
        )
        cls.product_tmpl_01 = cls.product_tmpl_model.create(
            {"name": "Product 01", "categ_id": cls.product_ctg_01.id}
        )
        cls.product_tmpl_02 = cls.product_tmpl_model.create(
            {
                "name": "Product 02",
                "categ_id": cls.product_ctg_01.id,
                "attribute_set_id": cls.attribute_set_02.id,
            }
        )

    def test_01_product_category_to_non_assigned_templates(self):
        """
        Should assign the value to only the first template as the second one already
        has a value.
        """
        self.product_ctg_01.attribute_set_id = self.attribute_set_01
        self.assertEqual(self.attribute_set_01, self.product_tmpl_01.attribute_set_id)
        self.assertNotEqual(self.attribute_set_01, self.product_tmpl_02)

    def test_02_category_change(self):
        """
        When the category changes, the attribute set value is also changed based on the
        value assigned in the category.
        """
        self.assertFalse(self.product_tmpl_01.attribute_set_id)
        self.product_tmpl_01.categ_id = self.product_ctg_02
        self.assertEqual(self.attribute_set_02, self.product_tmpl_01.attribute_set_id)
