# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    allow_mass_editing = fields.Boolean()
    mass_editing_line_ids = fields.One2many(
        comodel_name="mass.editing.line", inverse_name="attribute_id"
    )

    def _get_mass_editing_ids(self):
        return self.mapped("mass_editing_line_ids").mapped("server_action_id")

    def _create_mass_editing(self):
        """
        Create Mass Editing if not exists, use create multi
        :return:
        """
        actions_server_obj = self.env["ir.actions.server"]
        attributes_without_mass = self.filtered(lambda a: not a.mass_editing_line_ids)
        attribute_groups = self.env["attribute.group"].search(
            [("id", "in", attributes_without_mass.mapped("attribute_group_id").ids)]
        )
        mass_editings = actions_server_obj
        for attribute_group in attribute_groups.filtered(
            lambda g: not g.mass_edit_action_ids
        ):
            vals = attribute_group._prepare_create_mass_editing()
            vals = actions_server_obj.play_onchanges(vals, vals.keys())
            mass_editings |= actions_server_obj.create(vals)

        for attribute in self:
            for mass_edit in attribute_groups.mapped("mass_edit_action_ids").filtered(
                lambda m: m.mass_edit_attribute_group_id == attribute.attribute_group_id
            ):
                mass_edit.write(
                    {
                        "mass_edit_line_ids": [
                            (0, 0, attribute._prepare_mass_editing_line())
                        ]
                    }
                )
        mass_editings.create_action()
        return True

    def _remove_attribute_from_mass_editing(self):
        """
        If attribute field is in mass_editing, remove it
        Then, if no fields are present in mass editing, remove the action
        and the mass editing
        :return:
        """
        mass_editing_to_remove = self.env["ir.actions.server"].browse()
        # fetch them before unlinking lines to find them easily
        mass_edits = self._get_mass_editing_ids()
        self.mapped("mass_editing_line_ids").unlink()
        for mass_editing in mass_edits:
            if not mass_editing.mass_edit_line_ids:
                mass_editing_to_remove |= mass_editing
        mass_editing_to_remove.unlink()

    def _prepare_mass_editing_line(self):
        return {
            "field_id": self.field_id.id,
            "attribute_id": self.id,
        }

    def _manage_mass_editings(self):
        """
        Create mass editing if allowed and if not, remove existing ones
        :return:
        """
        allowed_attributes = self.filtered("allow_mass_editing")
        allowed_attributes._create_mass_editing()
        not_allowed_attributes = self - allowed_attributes
        if not_allowed_attributes:
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
