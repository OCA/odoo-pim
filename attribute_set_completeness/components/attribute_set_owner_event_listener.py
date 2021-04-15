# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.component_event import skip_if


class AttributeSetOwnerEventListener(AbstractComponent):
    _name = "attribute.set.owner.event.listener"
    _inherit = "base.event.listener"

    def _get_skip_if_condition_fields(self, record):
        """Return the field names that trigger the condition"""
        attribute_set = record.attribute_set_id
        attribute_set_completeness = attribute_set.attribute_set_completeness_ids
        field_names = attribute_set_completeness.mapped("field_id.name")
        field_names.append("attribute_set_id")
        return field_names

    def _get_skip_if_condition(self, record, **kwargs):
        if not record.attribute_set_id:
            return True
        if set(self._get_skip_if_condition_fields(record)) & set(kwargs["fields"]):
            return False
        return True

    @skip_if(
        lambda self, record, **kwargs: self._get_skip_if_condition(record, **kwargs)
    )
    def on_record_write(self, record, fields=None):
        record._compute_attribute_set_completed_ids()
