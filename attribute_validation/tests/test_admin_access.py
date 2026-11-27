from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAdminAccess(TransactionCase):
    """A Settings admin can reach the validation rules menu out of the box."""

    def test_admin_implies_validation_manager(self):
        admin = self.env.ref("base.user_admin")
        self.assertTrue(
            admin.has_group("attribute_validation.group_validation_manager"),
            "Administrators must imply Validation Manager so the menu shows.",
        )
        # The menu action's model must be readable by the admin (else the menu
        # is filtered out). This raises AccessError if it is not.
        self.env["attribute.validation.rule"].with_user(admin).search([], limit=1)

    def test_groups_share_privilege_and_category(self):
        privilege = self.env.ref("attribute_validation.privilege_attribute_validation")
        category = self.env.ref(
            "attribute_validation.module_category_attribute_validation"
        )
        self.assertEqual(privilege.category_id, category)
        for xmlid in ("group_validation_user", "group_validation_manager"):
            group = self.env.ref(f"attribute_validation.{xmlid}")
            self.assertEqual(
                group.privilege_id,
                privilege,
                f"{xmlid} should sit under the Attribute Validation privilege.",
            )
