from odoo import api, models
from odoo.osv import expression


class AttributeSetOwnerMixin(models.AbstractModel):
    _name = "attribute.set.owner.mixin"
    _description = "Attribute set owner mixin"
    _inherit = "attribute.set.owner.mixin"

    @api.model
    def _get_domain_attribute_eview(self):
        domain = super()._get_domain_attribute_eview()
        if not self._context.get("include_native_attribute"):
            domain = expression.OR(
                [
                    domain,
                    [
                        ("model_id.model", "=", self._name),
                        ("attribute_set_ids", "!=", False),
                        ("nature", "=", "json_postgresql"),
                    ],
                ]
            )

        return domain
