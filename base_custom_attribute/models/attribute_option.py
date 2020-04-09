# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AttributeOption(models.Model):
    _name = "attribute.option"
    _description = "Attribute Option"
    _order = "sequence"

    @api.model
    def _get_model_list(self):
        models = self.env["ir.model"].search([])
        return [(m.model, m.name) for m in models]

    name = fields.Char("Name", translate=True, required=True)

    value_ref = fields.Reference(_get_model_list, "Reference")

    attribute_id = fields.Many2one(
        "attribute.attribute", "Product Attribute", required=True, ondelete='cascade',
    )

    relation_model_id = fields.Many2one(
        "ir.model", "Relational Model", related="attribute_id.relation_model_id"
    )

    sequence = fields.Integer("Sequence")

    @api.onchange("name")
    def name_change(self):
        """Prevent the user from adding manually an option to m2o or m2m Attributes
        linked to another model (through 'relation_model_id')"""
        if self.attribute_id.relation_model_id:
            warning = {
                "title": _("Error!"),
                "message": _(
                    """Use the 'Load Attribute Options' button or specify a Domain
                    in order to define the available Options linked to the Relational\
                    Model"""
                ),
            }
            return {"warning": warning}
