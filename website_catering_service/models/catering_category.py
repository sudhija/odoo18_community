# -*- coding: utf-8 -*-
from odoo import models, fields

class CateringCategory(models.Model):
    _name = 'catering.category'
    _description = 'Catering Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_ids = fields.Many2many(
        'product.template',
        'catering_category_product_rel',
        'category_id',
        'product_id',
        string='Products'
    )
    default_product_id = fields.Many2one('product.template', string='Default Product')
    website_published = fields.Boolean(string='Published on Website', default=True)
