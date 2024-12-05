from odoo import models, fields, api, exceptions, _

class Demand(models.Model):
    _name = 'supplier.portal.demand'
    _description = 'Demand Request'

    # Demand Details
    demand_name = fields.Char(string='Demand Name', required=True)
    demand_description = fields.Text(string='Demand Description', required=True)
    budget = fields.Float(string='Budget')
    deadline = fields.Date(string='Deadline')

    # Binary Field for File Upload
    demand_file = fields.Binary(string='Demand File')
    demand_file_name = fields.Char(string='File Name')  # Optional: To store the file name

    # Link to Offers
    offer_ids = fields.One2many('supplier.portal.offer', 'demand_id', string='Offers')

    @api.model
    def create(self, vals):
        # Restrict demand creation to administrators
        if not self.env.user.has_group('base.group_system'):
            raise exceptions.AccessError(_("Only administrators can create demands."))
        return super(Demand, self).create(vals)

    def name_get(self):
        result = []
        for demand in self:
            result.append((demand.id, demand.demand_name))
        return result
