from odoo.exceptions import MissingError
from odoo.fields import Many2one

# Override the Many2one field
# class Many2oneOverride(fields.Many2one):


def patch_convert_to_read(self, value, record, use_display_name=True):
    if use_display_name and value:
        try:
            return (value.id, value.sudo().display_name)
        except MissingError:
            return False
    elif value:
        return value.id
    # In general odoo assumes use_display_name is True if value is empty
    # If use_display_name is False is not in account or if value is empty
    # This fix will have a PR in odoo repositoy,
    # and if approved this fix code will be removed
    else:
        return False


Many2one.convert_to_read = patch_convert_to_read
