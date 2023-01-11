# Copyright 2023 ForgeFlow S.L.  <https://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.base_sparse_field.models.models import IrModelFields


def post_load_hook():
    def _instanciate_attrs(self, field_data):
        attrs = super(IrModelFields, self)._instanciate_attrs(field_data)
        if attrs and field_data.get("serialization_field_id"):
            serialization_record_id = field_data["serialization_field_id"]
            try:
                serialization_record = self.browse(serialization_record_id)
                attrs["sparse"] = serialization_record.name
            except AttributeError:
                # due to https://github.com/OCA/odoo-pim/issues/134
                # because depends_context isn't filled yet
                attrs["sparse"] = None
        return attrs

    IrModelFields._instanciate_attrs = _instanciate_attrs
