# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    
    last_service = fields.Float(string='Ultimo mantenimiento', help='Ultimo mantenimiento realizado')
    last_service_date = fields.Date(string='Fecha ultimo mantenimiento')
    next_service = fields.Float(string='Siguiente mantenimiento', help='El sistema enviara una advertencia al pasar este monto en el odometro')
    next_service_limit = fields.Integer(string='Limite de advertencia')
