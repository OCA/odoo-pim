# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "attribute.set.owner.mixin"]


class ResCountry(models.Model):
    _name = "res.country"
    _inherit = ["res.country", "attribute.set.owner.mixin"]
