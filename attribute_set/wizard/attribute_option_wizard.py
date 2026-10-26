# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from lxml import etree

from odoo import api, fields, models


class AttributeOptionWizard(models.TransientModel):
    _name = "attribute.option.wizard"
    _rec_name = "attribute_id"
    _description = "Custom Attributes Option"

    attribute_id = fields.Many2one(
        "attribute.attribute",
        "Product Attribute",
        required=True,
        # if the context is passed in correctly by suffixing it with _view_ref
        # we will no longer need default_get method to assign attribute_id a value
        default=lambda self: self.env.context.get("attribute_id_view_ref", False),
        ondelete="cascade",
    )
    option_ids = fields.Many2many(
        "attribute.option",
        string="Attribute Options",
    )

    def validate(self):
        return True

    @api.model_create_multi
    def create(self, vals_list):
        attr_obj = self.env["attribute.attribute"]
        for vals in vals_list:
            attr = attr_obj.browse(vals["attribute_id"])

            opt_obj = self.env["attribute.option"]

            for op_id in [val[1] for val in vals.get("option_ids", [])]:
                model = attr.relation_model_id.model

                name = self.env[model].browse(op_id).display_name
                opt_obj.create(
                    {
                        "attribute_id": vals["attribute_id"],
                        "name": name,
                        "value_ref": f"{attr.relation_model_id.model},{op_id}",
                    }
                )
            if vals.get("option_ids"):
                del vals["option_ids"]
        return super().create(vals_list)

    @api.model
    def get_views(self, views, options=None):
        context = self.env.context
        res = super().get_views(views, options=options)
        if (
            "views" in res
            and "form" in res["views"]
            and context
            and context.get("attribute_id_view_ref")
        ):
            attr_obj = self.env["attribute.attribute"]
            attr = attr_obj.browse(context.get("attribute_id_view_ref"))
            model = attr.relation_model_id
            relation = model.model
            domain_ids = [op.value_ref.id for op in attr.option_ids if op.value_ref]
            res["models"][self._name]["fields"].update(
                {
                    "option_ids": {
                        "domain": [("id", "not in", domain_ids)],
                        "string": "Options",
                        "type": "many2many",
                        "relation": relation,
                        "required": True,
                    }
                }
            )
            eview = etree.fromstring(res["views"]["form"]["arch"])
            options = etree.Element("field", name="option_ids", widget="many2many_tags")
            placeholder = eview.xpath("//separator[@string='options_placeholder']")[0]
            placeholder.getparent().replace(placeholder, options)
            res["views"]["form"]["arch"] = etree.tostring(eview, pretty_print=True)

        return res
