# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestPimCategoryAccess(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env["product.public.category"].create({"name": "Pumps"})
        cls.pim_user = new_test_user(
            cls.env, login="pim_user", groups="base.group_user,pim.group_pim_user"
        )
        cls.pim_reader = new_test_user(
            cls.env, login="pim_reader", groups="base.group_user,pim.group_pim_reader"
        )

    def test_pim_user_can_edit_category_description(self):
        category = self.category.with_user(self.pim_user)
        form = category.get_views([(False, "form")])["views"]["form"]
        self.assertNotIn('edit="False"', form["arch"])
        category.web_save({"website_description": "<p>Pumps</p>"}, {})
        self.assertEqual(self.category.website_description, "<p>Pumps</p>")

    def test_pim_reader_cannot_edit_category(self):
        with self.assertRaises(AccessError):
            self.category.with_user(self.pim_reader).write({"name": "Valves"})
