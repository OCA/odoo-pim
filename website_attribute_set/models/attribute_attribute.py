# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    e_com_visibility = fields.Boolean(
        string="E-Commerce Visibility",
        default=False,
        help="""If selected the attribute will be shown in e-commerce website app.""",
    )
    e_com_searchable = fields.Boolean(
        string="E-Commerce Searchable",
        default=False,
        help="""If selected the attribute will be included in e-commerce search.
        Disable for large text fields to improve search performance.""",
    )

    @api.constrains("domain")
    def _validate_domain(self):
        """Validate that the domain input is a valid Odoo domain."""
        for record in self:
            if record.domain:
                try:
                    domain = safe_eval(record.domain)
                    if not isinstance(domain, list):
                        continue

                    if not domain:  # Empty domain is valid
                        continue

                    for i, element in enumerate(domain):
                        if isinstance(element, str) and element in ["|", "&", "!"]:
                            if i > 0:
                                prev_element = domain[i - 1]
                                if isinstance(prev_element, list | tuple):
                                    raise ValueError(
                                        f"'{element}' at pos {i} wrong position."
                                        f"Operators must precede exprs."
                                    )
                        elif isinstance(element, list | tuple):
                            if len(element) < 2 or len(element) > 3:
                                raise ValueError(
                                    f"Domain at pos {i}, need 2-3, got {len(element)}"
                                )
                            field, operator = element[0], element[1]
                            if not isinstance(field, str):
                                raise ValueError(
                                    f"Field at pos {i}, must be str, got {type(field)}"
                                )
                            if not isinstance(operator, str):
                                raise ValueError(
                                    f"Op at pos {i}, must be str, got {type(operator)}"
                                )
                        else:
                            raise ValueError(
                                f"Domain elem must be op/cond list, got {type(element)}"
                            )
                except (Exception, TypeError, ValueError) as e:
                    raise ValidationError(
                        self.env._("Invalid domain: %s", str(e))
                    ) from e
