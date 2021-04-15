# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent
from odoo.addons.component_event import skip_if


class AttributeSetOwnerEventListener(AbstractComponent):
    _name = "attribute.set.owner.event.listener"
    _inherit = "base.event.listener"

    def _get_skip_if_condition(self, record, **kwargs):
        if not record.attribute_set_id:
            return True
        fields = kwargs["fields"]
        if "attribute_set_id" in fields or any(
            [
                field
                for field in fields
                if field
                in record.attribute_set_id.attribute_set_completeness_ids.mapped(
                    "field_id.name"
                )
            ]
        ):
            return False

        return True

    @skip_if(
        lambda self, record, **kwargs: self._get_skip_if_condition(record, **kwargs)
    )
    def on_record_write(self, record, fields=None):
        record._compute_completion_rate()
