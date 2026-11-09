# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import common, new_test_user


class TestPimAccess(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        model = cls.env.ref("product.model_product_template")
        group = cls.env["attribute.group"].create(
            {"name": "PIM Group", "model_id": model.id}
        )
        cls.attribute = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "model_id": model.id,
                "attribute_group_id": group.id,
                "attribute_type": "select",
                "field_description": "PIM Select",
                "name": "x_pim_select",
                "option_ids": [(0, 0, {"name": "Option 1"})],
            }
        )
        cls.native_attribute = cls.env["attribute.attribute"].create(
            {
                "nature": "native",
                "field_id": cls.env.ref("product.field_product_template__type").id,
                "model_id": model.id,
                "attribute_group_id": group.id,
                "attribute_type": "select",
            }
        )
        cls.user = new_test_user(
            cls.env, login="pim_reader", groups="base.group_user,pim.group_pim_reader"
        )

    def _view_spec(self, view):
        """Mimic the web client: read only the fields present in the view."""
        arch = etree.fromstring(view["arch"])
        # Skip the fields of embedded x2many subviews, they belong to another model
        names = {
            node.get("name")
            for node in arch.iter("field")
            if not any(parent.tag == "field" for parent in node.iterancestors())
        }
        return {name: {} for name in names}

    def test_pim_reader_can_read_attributes(self):
        action = self.env.ref("pim.attribute_attribute_form_action")
        Attribute = self.env["attribute.attribute"].with_user(self.user)
        views = [(False, mode) for mode in action.view_mode.split(",")]
        result = Attribute.get_views(views + [(False, "search")])
        attributes = (self.attribute | self.native_attribute).with_user(self.user)
        # Values computed as superuser in setUpClass would hide missing rights
        self.env.invalidate_all()
        Attribute.web_search_read([], self._view_spec(result["views"]["list"]))
        self.env.invalidate_all()
        attributes.web_read(self._view_spec(result["views"]["form"]))
