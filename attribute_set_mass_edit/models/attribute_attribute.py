# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeAttribute(models.Model):

    _inherit = "attribute.attribute"

    allow_mass_editing = fields.Boolean()
    mass_editing_ids = fields.One2many(
        comodel_name="mass.editing", compute="_compute_mass_editing_ids"
    )

    def _get_mass_editing_ids_domain(self):
        return [("attribute_group_id", "in", self.mapped("attribute_group_id").ids)]

    @api.depends()
    def _compute_mass_editing_ids(self):
        objects = self.env["mass.editing"].search(self._get_mass_editing_ids_domain())
        for attribute in self:
            attribute.mass_editing_ids = objects.filtered(
                lambda o, g=attribute.attribute_group_id: o.attribute_group_id.id
                == g.id
            )

    def _prepare_create_mass_editing(self):
        self.ensure_one()
        group_id = self.attribute_group_id
        return {
            "attribute_group_id": group_id.id,
            "model_id": group_id.model_id.id,
            "name": group_id.name,
        }

    def _create_mass_editing(self):
        """
        Create Mass Editing if not exists, use create multi
        :return:
        """
        mass_obj = self.env["mass.editing"]
        attributes_without_mass = self.filtered(lambda a: not a.mass_editing_ids)
        mass_editings = mass_obj
        for attribute in attributes_without_mass:
            new_mass_editing = mass_obj.new(attribute._prepare_create_mass_editing())
            # TODO: we should use tests.Form IMO
            new_mass_editing.onchange_name()
            mass_editings |= mass_obj.create(
                new_mass_editing._convert_to_write(new_mass_editing._cache)
            )
        mass_editings.enable_mass_operation()
        return True

    def _remove_attribute_from_mass_editing(self):
        """
        If attribute field is in mass_editing, remove it
        Then, if no fields are present in mass editing, remove the action
        and the mass editing
        :return:
        """
        mass_editing_to_remove = self.env["mass.editing"].browse()
        for attribute in self:
            for mass_editing in attribute.mass_editing_ids.filtered(
                lambda m, f=attribute.field_id: f in m.mapped("line_ids.field_id")
            ):
                mass_editing.line_ids.filtered(
                    lambda l: l.field_id == attribute.field_id
                ).unlink()
                if not mass_editing.line_ids:
                    mass_editing_to_remove |= mass_editing
        mass_editing_to_remove.unlink()
        self.refresh()

    def _prepare_mass_editing_line(self):
        return {
            "field_id": self.field_id.id,
        }

    def _manage_mass_editings(self):
        """
        Create mass editing if allowed and if not, remove existing ones
        :return:
        """
        allowed_attributes = self.filtered("allow_mass_editing")
        allowed_attributes._create_mass_editing()
        # As mass_editing_ids is computed non stored
        allowed_attributes.refresh()
        for allowed_attribute in allowed_attributes:
            if (
                allowed_attribute.field_id.id
                not in allowed_attribute.mass_editing_ids.mapped(
                    "line_ids.field_id"
                ).ids
            ):
                allowed_attribute.mass_editing_ids.write(
                    {
                        "line_ids": [
                            (0, 0, allowed_attribute._prepare_mass_editing_line())
                        ]
                    }
                )
        not_allowed_attributes = self - allowed_attributes
        not_allowed_attributes._remove_attribute_from_mass_editing()

    def write(self, vals):
        """
        Create Mass Editing for attributes that allow it
        :param vals:
        :return:
        """
        res = super(AttributeAttribute, self).write(vals)
        self._manage_mass_editings()
        return res

    def unlink(self):
        self._remove_attribute_from_mass_editing()
        return super(AttributeAttribute, self).unlink()

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals):
        attributes = super(AttributeAttribute, self).create(vals)
        attributes._manage_mass_editings()
        return attributes
