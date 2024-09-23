# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta


class MaintenanceNotifications(models.Model):
    _name = 'fleet.maintenance_notifications'

    last_service = fields.Float(string='Ultima Notificacion', help='Ultimo mantenimiento realizado',readonly=True)
    last_service_date = fields.Date(string='Fecha ultimo mantenimiento',readonly=True)
    next_service = fields.Float(string='Siguiente mantenimiento(km)', help='El sistema enviara una advertencia al pasar este monto en el odometro')
    next_service_limit = fields.Integer(string='Limite de advertencia(dias)',help='A cuantos días se creara la tarea')
    frequence = fields.Float(string='Frecuencia(km)', help='Frecuencia de mantenimiento')
    create_services = fields.Boolean(string='Crear servicio automaticamente', default = False)

    desc_default = fields.Char(string="Descripcion por defecto")
    proveedor_default = fields.Many2one(
        comodel_name='res.partner',
        string = 'Proveedor por defecto',
    )
    service_type_id = fields.Many2one(
        comodel_name='fleet.service.type',  # Modelo al que apunta el campo
        string='Tipo de Servicio',          # Etiqueta que se muestra en la interfaz
        help='Selecciona el tipo de servicio asociado a este vehículo.',
        required = True

    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',  # Modelo al que apunta el campo
        string='Vehiculo',          # Etiqueta que se muestra en la interfaz
        help='Selecciona el tipo de servicio asociado a este vehículo.',
        required = True,
        readonly=True,
    )

    @api.constrains('next_service')
    def _check_next_service(self):
        for record in self:
            if record.next_service <= record.last_service and record.next_service != 0:
                raise ValidationError("El valor de 'Siguiente mantenimiento' no puede ser menor a la ultima notificación.")

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    maintenance_ids = fields.One2many(
        comodel_name='fleet.maintenance_notifications',  # Modelo relacionado
        inverse_name='vehicle_id',  # Campo en el modelo relacionado que apunta a este modelo
        string='Notificaciones de Mantenimiento',  # Etiqueta que se muestra en la interfaz
        help='Lista de notificaciones de mantenimiento para este vehículo.',  # Ayuda que se muestra en la interfaz
    )

    def create_maintenance_activity(self,date,odometer_value,task):
        for record in self:
                date_deadline = fields.Date.today() + timedelta(days=task.next_service_limit)
                 # Crear la actividad de mantenimiento
                self.env['mail.activity'].create({
                    'res_model_id': 639,  # ID del modelo relacionado
                    'res_id': record.id,  # ID del registro relacionado
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,  # Tipo de actividad (ej. 'Hacer')
                    'summary': f'Se requiere {task.service_type_id.name}',  # Resumen de la actividad
                    'note': f'El odómetro de {record.model_id.name} ha superado los {odometer_value} km.',  # Nota de la actividad
                    'date_deadline': date_deadline,  # Fecha límite para la actividad
                    'user_id': record.manager_id.id,  # Asignar al encargados
                })
        
                # Enviar una notificación al usuario encargado
                record.message_post(
                    body= f'Se requiere {task.service_type_id.name}. El odómetro ha superado los {odometer_value} km. Se ha creado una actividad para realizar mantenimiento.',
                    partner_ids=[record.manager_id.partner_id.id],  # Enviar notificación al encargado
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
                task.last_service = odometer_value
                task.last_service_date = date
                if task.frequence != 0:
                    #task.next_service = task.next_service + task.frequence  
                    task.next_service = record.next_frequence(task.next_service,task.frequence,odometer_value)
                else:
                    task.next_service = 0
                if task.create_services:
                    record.create_service_log(date_deadline,task,odometer_value)
                    record.message_post(
                    body= f'Se ha creado un nuevo servicio del tipo  {task.service_type_id.name}',
                    partner_ids=[record.manager_id.partner_id.id],  # Enviar notificación al encargado
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
            
    def next_frequence(self,limit,freq,odometer):
        if limit+freq <= odometer:
            return self.next_frequence(limit+freq,freq,odometer)
        else:
            return limit+freq
            
    def create_service_log(self, date, task, odometer):
        # Crear un nuevo registro en fleet.vehicle.log.services
        self.env['fleet.vehicle.log.services'].create({
            'description':task.desc_default if task.desc_default else '',
            'vehicle_id': self.id,
            'date': date,  # Fecha de creación del servicio
            'odometer': 0,  # Valor del odómetro proporcionado como argumento
            #'cost': 0.0,  # Costo del servicio (puedes ajustar este valor)
            'service_type_id': task.service_type_id.id,  # Tipo de servicio
            'vendor_id':task.proveedor_default.id if task.proveedor_default.id else False,
            #'notes': 'Creado desde una notificación de mantenimiento',  # Notas adicionales
        })
                
class FleetVehicleService(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    def _set_odometer(self):
        for record in self:
            if not record.odometer:
                raise UserError(('No esta permitido vaciar el odometro'))
            odometer = self.env['fleet.vehicle.odometer'].create({
                'value': record.odometer,
                'date': record.date or fields.Date.context_today(record),
                'vehicle_id': record.vehicle_id.id
            })
            for task in record.vehicle_id.maintenance_ids:
                if odometer.value > task.next_service and task.next_service != 0:
                    record.vehicle_id.create_maintenance_activity(record.date,odometer.value,task)
            #if record.vehicle_id.next_service > 0:
             #   if odometer.value > record.vehicle_id.next_service:
              #      record.vehicle_id.create_maintenance_activity(record.date,odometer.value)
            self.odometer_id = odometer