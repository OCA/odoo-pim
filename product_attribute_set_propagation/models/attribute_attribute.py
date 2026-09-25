# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    default_is_propagated = fields.Boolean(
        string="Propagate by Default",
        default=True,
        help="If marked, this attribute will be propagated "
        "by default in the Propagate Attributes product feature.",
    )
