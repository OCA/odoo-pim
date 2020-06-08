# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeAttribute(models.Model):

    _inherit = "attribute.attribute"

    allow_mass_editing = fields.Boolean(default=False)

    def _get_mass_object(self):
        self.ensure_one()
        return self.env["mass.object"].search(
            [("attribute_group_id", "=", self.attribute_group_id.id)]
        )

    def _prepare_create_mass_object(self):
        self.ensure_one()
        group_id = self.attribute_group_id
        return {
            "attribute_group_id": group_id.id,
            "model_id": group_id.model_id.id,
            "name": group_id.name,
        }

    def _create_mass_object(self):
        data = self._prepare_create_mass_object()
        mass_object = self.env["mass.object"].create(data)
        mass_object.create_action()
        return mass_object

    def _remove_attribute_from_mass_object(self, mass_object):
        self.ensure_one()
        if self.field_id.id in mass_object.field_ids.ids:
            mass_object.field_ids = [(2, self.field_id.id)]
            if not mass_object.field_ids:
                mass_object.unlink_action()
                mass_object.unlink()

    @api.multi
    def write(self, vals):
        res = super(AttributeAttribute, self).write(vals)
        for attribute in self:
            mass_object = attribute._get_mass_object()
            if attribute.allow_mass_editing:
                if not mass_object:
                    mass_object = attribute._create_mass_object()

                if attribute.id not in mass_object.field_ids.ids:
                    mass_object.field_ids = [(4, attribute.field_id.id)]
            elif mass_object:
                attribute._remove_attribute_from_mass_object(mass_object)
        return res

    @api.multi
    def unlink(self):
        for attribute in self:
            mass_object = attribute._get_mass_object()
            if mass_object:
                attribute._remove_attribute_from_mass_object(mass_object)
        return super(AttributeAttribute, self).unlink()

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        attributes = super(AttributeAttribute, self).create(vals_list)
        edit_attributes = attributes.filtered(lambda att: att.allow_mass_editing)
        for attribute in edit_attributes:
            mass_object = attribute._get_mass_object()
            if not mass_object:
                mass_object = attribute._create_mass_object()

            if attribute.id not in mass_object.field_ids.ids:
                mass_object.field_ids = [(4, attribute.field_id.id)]
        return attributes
