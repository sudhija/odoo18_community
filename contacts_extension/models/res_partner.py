from odoo import models, fields

class BusinessCategory(models.Model):
    _name = 'business.category'
    _description = 'Business Category'

    name = fields.Char(string="Business Category", required=True)


class FCCircle(models.Model):
    _name = 'fc.circle'
    _description = 'FC Circle'

    name = fields.Char(string="FC Circle", required=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # taluk = fields.Char(string="Taluk")
    # district = fields.Char(string="District")

    business_category_id = fields.Many2one('business.category', string="Business Category")
    fc_circle_id = fields.Many2one('fc.circle', string="FC Circle")
    instagram_id = fields.Char(string="Instagram ID")
    passport_photo = fields.Binary(string="Passport Size Photo")
    visiting_card_photo = fields.Binary(string="Visiting Card Photo")
