# models/party_hall_facility.py
from odoo import models, fields

class PartyHallFacility(models.Model):
    _name = 'party.hall.facility'
    _description = 'Party Hall Facility'

    name = fields.Char(string="Facility Name", required=True)
    icon = fields.Binary(string="Icon")  # optional: upload an icon for each facility
