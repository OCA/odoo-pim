# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    field_is_searchable = fields.Boolean(
        compute="_compute_field_is_searchable",
        help="Whether the underlying field can be searched "
        "(stored in SQL or has a search method).",
    )

    e_com_visibility = fields.Boolean(
        string="E-Commerce Visibility",
        default=False,
        help="""If selected, the attribute will be shown in e-commerce website app.""",
    )
    e_com_filter = fields.Boolean(
        default=False,
        help="""If selected, the attribute will be shown as a filter
         in the e-commerce shop sidebar.""",
    )
    e_com_specification = fields.Boolean(
        default=False,
        help="""If selected, the attribute will be shown as specification
             in e-commerce website app product view.""",
    )
    e_com_searchable = fields.Boolean(
        string="E-Commerce Searchable",
        default=False,
        help="""If selected, the attribute will be included in e-commerce search.
        Disable for large text fields to improve search performance.""",
    )
    e_com_range_filter = fields.Boolean(
        string="E-Commerce Range Filter",
        default=False,
        help="""For numeric attributes (integer/float), show min/max range inputs
        instead of individual value selection in the shop filter.""",
    )
    e_com_multi_select = fields.Boolean(
        string="E-Commerce Multi-Select",
        default=False,
        help="""Allow selecting multiple values for this attribute filter.
        Products matching ANY selected value will be shown (OR logic).""",
    )
    e_com_show_count = fields.Boolean(
        string="E-Commerce Show Count",
        default=False,
        help="""Show the number of matching products next to each filter option.""",
    )

    @api.depends("name", "model_id")
    def _compute_field_is_searchable(self):
        for rec in self:
            if not rec.name or not rec.model_id:
                rec.field_is_searchable = False
                continue
            model_obj = self.env.get(rec.model_id.model)
            if model_obj is None:
                rec.field_is_searchable = False
                continue
            field = model_obj._fields.get(rec.name)
            rec.field_is_searchable = bool(
                field
                and (field.store or field.search or getattr(field, "sparse", None))
            )

    @api.constrains("e_com_filter")
    def _check_e_com_filter(self):
        for rec in self:
            if rec.e_com_filter and not rec.e_com_visibility:
                raise ValidationError(
                    self.env._(
                        "Cannot use attribute as filter "
                        "if it doesn't have E-Commerce Visibility enabled."
                    )
                )
            if rec.e_com_filter and not rec.field_is_searchable:
                raise ValidationError(
                    self.env._(
                        "Cannot use attribute '%s' as filter "
                        "because its field is neither stored nor has a search method.",
                        rec.field_description,
                    )
                )

    @api.constrains("e_com_specification")
    def _check_e_com_specification(self):
        for rec in self:
            if rec.e_com_specification and not rec.e_com_visibility:
                raise ValidationError(
                    self.env._(
                        "Cannot use attribute as specification "
                        "if it doesn't have E-Commerce Visibility enabled."
                    )
                )

    @api.constrains("e_com_searchable")
    def _check_e_com_searchable(self):
        for rec in self:
            if rec.e_com_searchable and not rec.e_com_visibility:
                raise ValidationError(
                    self.env._(
                        "Cannot make attribute searchable "
                        "if it doesn't have E-Commerce Visibility enabled."
                    )
                )
            if rec.e_com_searchable and not rec.field_is_searchable:
                raise ValidationError(
                    self.env._(
                        "Cannot make attribute '%s' searchable "
                        "because its field is neither stored nor has a search method.",
                        rec.field_description,
                    )
                )

    @api.constrains("e_com_range_filter", "e_com_multi_select", "e_com_show_count")
    def _check_filter_options(self):
        for rec in self:
            if (
                rec.e_com_range_filter or rec.e_com_multi_select or rec.e_com_show_count
            ) and not rec.e_com_filter:
                raise ValidationError(
                    self.env._(
                        "E-Commerce Range Filter, Multi-Select and Show Count "
                        "require the attribute to be enabled as a filter."
                    )
                )

    @api.onchange("e_com_visibility")
    def onchange_e_com_visibility(self):
        for rec in self:
            if rec.e_com_visibility:
                rec.write({"e_com_filter": True, "e_com_specification": True})
            else:
                rec.write(
                    {
                        "e_com_filter": False,
                        "e_com_specification": False,
                        "e_com_searchable": False,
                        "e_com_range_filter": False,
                        "e_com_multi_select": False,
                        "e_com_show_count": False,
                    }
                )

    @api.onchange("e_com_filter")
    def onchange_e_com_filter(self):
        for rec in self:
            if not rec.e_com_filter:
                rec.write(
                    {
                        "e_com_range_filter": False,
                        "e_com_multi_select": False,
                        "e_com_show_count": False,
                    }
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
                                if isinstance(prev_element, (list, tuple)):
                                    raise ValueError(
                                        f"'{element}' at pos {i} wrong position."
                                        f"Operators must precede exprs."
                                    )
                        elif isinstance(element, (list, tuple)):
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
                except (ValueError, TypeError) as e:
                    raise ValidationError(
                        self.env._("Invalid domain: %s", str(e))
                    ) from e
