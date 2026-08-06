# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user


class TestPimAccess(TransactionCase):
    """A PIM Manager must be able to manage attribute sets without the
    Settings / ERP Manager admin group, and a PIM Reader must not."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_product = cls.env.ref("product.model_product_template")
        cls.manager = new_test_user(
            cls.env,
            login="pim_manager",
            groups="base.group_user,pim.group_pim_manager",
        )
        cls.reader = new_test_user(
            cls.env,
            login="pim_reader",
            groups="base.group_user,pim.group_pim_reader",
        )

    def test_manager_is_not_admin(self):
        # The whole point: management without the admin (ERP Manager) group.
        self.assertFalse(self.manager.has_group("base.group_erp_manager"))

    def test_manager_can_create_attribute_set(self):
        attr_set = (
            self.env["attribute.set"]
            .with_user(self.manager)
            .create({"name": "PIM set", "model_id": self.model_product.id})
        )
        self.assertTrue(attr_set.id)
        # and edit / delete it
        attr_set.write({"name": "PIM set renamed"})
        attr_set.unlink()

    def test_manager_can_create_attribute_group(self):
        group = (
            self.env["attribute.group"]
            .with_user(self.manager)
            .create({"name": "PIM group", "model_id": self.model_product.id})
        )
        self.assertTrue(group.id)

    def test_reader_cannot_create_attribute_set(self):
        with self.assertRaises(AccessError):
            self.env["attribute.set"].with_user(self.reader).create(
                {"name": "Nope", "model_id": self.model_product.id}
            )
