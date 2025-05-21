# Copyright 2011 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    e_com_visibility = fields.Boolean(
        string="E-Commerce Visibility",
        default=False,
        help="""If selected the attribute will be shown in e-commerce website app.""",
    )

    @api.constrains("domain")
    def _validate_domain(self):
        """Validate that the domain input is a valid Odoo domain."""
        for record in self:
            if record.domain:
                try:
                    domain = safe_eval(record.domain)
                    # Normalize will raise an error if the domain is invalid
                    expression.normalize_domain(domain)
                    return True
                except Exception as e:
                    raise ValidationError(f"Invalid domain: {str(e)}") from e
