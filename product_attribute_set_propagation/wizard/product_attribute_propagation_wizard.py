# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductAttributePropagationWizard(models.TransientModel):
    _name = "product.attribute.propagation.wizard"
    _description = "Propagate Product Attribute Values"

    propagation_model = fields.Selection(
        [
            ("product.template", "Product Template"),
            ("product.product", "Product Variant"),
        ],
        required=True,
    )
    source_product_tmpl_id = fields.Many2one(
        "product.template",
        string="Source Product",
        readonly=True,
    )
    source_product_id = fields.Many2one(
        "product.product",
        string="Source Variant",
        readonly=True,
    )
    attribute_set_id = fields.Many2one(
        "attribute.set",
        string="Attribute Set",
        compute="_compute_attribute_set_id",
    )
    target_product_tmpl_ids = fields.Many2many(
        "product.template",
        string="Target Products",
    )
    target_product_ids = fields.Many2many(
        "product.product",
        string="Target Variants",
    )
    available_attribute_ids = fields.Many2many(
        "attribute.attribute",
        "product_attribute_propagation_wizard_available_attr_rel",
        "wizard_id",
        "attribute_id",
        string="Available Attributes",
        compute="_compute_available_attribute_ids",
    )
    attribute_ids = fields.Many2many(
        "attribute.attribute",
        "product_attribute_propagation_wizard_attr_rel",
        "wizard_id",
        "attribute_id",
        string="Attributes to Propagate",
    )

    @api.depends("source_product_tmpl_id", "source_product_id", "propagation_model")
    def _compute_attribute_set_id(self):
        for wizard in self:
            if wizard.propagation_model == "product.template":
                wizard.attribute_set_id = wizard.source_product_tmpl_id.attribute_set_id
            elif wizard.propagation_model == "product.product":
                wizard.attribute_set_id = wizard.source_product_id.attribute_set_id
            else:
                wizard.attribute_set_id = False

    @api.depends("attribute_set_id", "propagation_model")
    def _compute_available_attribute_ids(self):
        for wizard in self:
            wizard.available_attribute_ids = (
                wizard.attribute_set_id.attribute_ids.filtered(
                    lambda a: a.model == wizard.propagation_model
                )
            )

    def action_clear_attributes(self):
        """Deselect all attributes so the user can pick only a few."""
        self.ensure_one()
        self.attribute_ids = [(5, 0)]
        return self._reopen_wizard()

    def action_select_default_attributes(self):
        """Prefill the attributes marked as propagated by default."""
        self.ensure_one()
        self.attribute_ids = self.available_attribute_ids.filtered(
            "default_is_propagated"
        )
        return self._reopen_wizard()

    def _reopen_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Propagate Attributes"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def _get_source_and_targets(self):
        """Return (source_record, target_records) based on propagation model."""
        self.ensure_one()
        if self.propagation_model == "product.template":
            return self.source_product_tmpl_id, self.target_product_tmpl_ids
        return self.source_product_id, self.target_product_ids

    def _get_propagation_vals(self, source, attributes):
        """Build a vals dict with attribute values from the source record."""
        vals = {}
        for attribute in attributes:
            field_name = attribute.name
            if field_name not in source._fields:
                continue
            value = source[field_name]
            if attribute.attribute_type == "multiselect":
                vals[field_name] = [(6, 0, value.ids)]
            elif attribute.attribute_type == "select":
                vals[field_name] = value.id if value else False
            else:
                vals[field_name] = value
        return vals

    def action_propagate(self):
        """Propagate selected attribute values from source to target products."""
        self.ensure_one()
        source, targets = self._get_source_and_targets()
        if not source:
            raise UserError(_("No source product specified."))
        if not source.attribute_set_id:
            raise UserError(
                _("The source product does not have an attribute set assigned.")
            )
        if not targets:
            raise UserError(_("Please select at least one target product."))
        if not self.attribute_ids:
            raise UserError(_("Please select at least one attribute to propagate."))
        attributes = self.attribute_ids.filtered(
            lambda a: a.model == self.propagation_model
        )
        vals = self._get_propagation_vals(source, attributes)
        if vals:
            targets.write(vals)
        for target in targets:
            target.message_post(
                body=_(
                    "Attribute values propagated from <a href=# "
                    "data-oe-model=%(model)s data-oe-id=%(id)s>%(name)s</a>.",
                    model=source._name,
                    id=source.id,
                    name=source.display_name,
                ),
            )
        return {"type": "ir.actions.act_window_close"}
