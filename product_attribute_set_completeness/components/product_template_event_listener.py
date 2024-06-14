# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductTemplateEventListener(Component):
    _name = "product.template.event.listener"
    _inherit = ["attribute.set.owner.event.listener"]

    _apply_on = ["product.template"]
