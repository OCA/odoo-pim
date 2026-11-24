# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    default_is_propagated = fields.Boolean(
        string="Default Propagation Selection",
        default=True,
        help="If marked, this attribute is selected by the 'Select default "
        "attributes' button in the Propagate Attributes wizard.",
    )
