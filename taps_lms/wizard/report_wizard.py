import base64
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class LmsPDFReport(models.TransientModel):
    _name = 'lms.pdf.report'
    _description = 'LMS pdf Report'

    date_from = fields.Date('Date from', required=True)
    date_to = fields.Date('Date to', required=True)
    image_1920 = fields.Image("Image")
    criteria_id = fields.Many2one('lms.criteria', string='Criteria') 
    session_ids = fields.Many2one('lms.title', string='Title')
    company_id = fields.Many2one('res.company', string='Company')
    venue = fields.Many2one('lms.session.venue', string='Venue')
    instructor_id = fields.Many2one('res.partner',string="Facilitator")
    participation_group = fields.Many2one('lms.participation.group', string='Participation Group')
    
    report_type = fields.Selection([
        ('training',	'Training Courses'),
        ('attendance',	'Attendance Report'),],
        string='Report Type', required=True,
        help='Report Type', default='attendance')

    mode_type = fields.Selection([
        ('criteria', 'By Criteria'),
        ('title', 'By Title'),
        ('venues', 'By Venue'),
        ('facilitator', 'By Facilitator'),
        ('pg', 'By Participation Group')],
        string='Report Mode', required=True, default='title')

    # generate PDF report
    def action_print_report(self):
        # data = {'date_from': self.date_from, 'date_to': self.date_to, 'course_ids': self.course_ids.ids,'report_type': self.report_type, 'responsible_id': self.responsible_id.id}
        if self.report_type:
            if self.mode_type == 'criteria':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : self.criteria_id.id,
                        'session_ids': False,
                        'venue' : False,
                        'instructor_id': False,
                        'participation_group' : False}
            if self.mode_type == 'title':
                data = {'date_from': self.date_from,
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': self.session_ids.ids,
                        'venue' : False,
                        'instructor_id': False,
                        'participation_group' : False}
            if self.mode_type == 'venues':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': False, 
                        'venue' : self.venue.id,
                        'instructor_id': False,
                        'participation_group' : False}
            if self.mode_type == 'facilitator':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': False, 
                        'venue' : False,
                        'instructor_id': self.instructor_id.id,
                        'participation_group' : False}
            if self.mode_type == 'pg':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': False, 
                        'venue' : False,
                        'instructor_id': False,
                        'participation_group' : self.participation_group.id}
            
        if self.report_type == 'training': 
            return self.env.ref('taps_lms.action_lms_pdf_report').report_action(self, data=data)
        if self.report_type == 'attendance': 
            return self.env.ref('taps_lms.action_lms_attendance_pdf_report').report_action(self, data=data)

    # Generate xlsx report
    def action_generate_xlsx_report(self):
        if self.report_type:
            if self.mode_type == 'criteria':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : self.criteria_id.id,
                        'session_ids': False,
                        'venue' : False,
                        'instructor_id': False,
                        'participation_group' : False}
            if self.mode_type == 'title':
                data = {'date_from': self.date_from,
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': self.session_ids.ids,
                        'venue' : False,
                        'instructor_id': False,
                        'participation_group' : False}
            if self.mode_type == 'venues':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': False, 
                        'venue' : self.venue.id,
                        'instructor_id': False,
                        'participation_group' : False}
            if self.mode_type == 'facilitator':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': False, 
                        'venue' : False,
                        'instructor_id': self.instructor_id.id,
                        'participation_group' : False}
            if self.mode_type == 'pg':
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to,
                        'report_type': self.report_type,
                        'criteria_id' : False,
                        'session_ids': False, 
                        'venue' : False,
                        'instructor_id': False,
                        'participation_group' : self.participation_group.id}
            
        if self.report_type == 'attendance': 
            return self.env.ref('taps_lms.action_lms_xlsx_report').report_action(self, data=data)
        # return self.env.ref('taps_lms.action_lms_xlsx_report').report_action(self, data=data)

class LmsAttendanceReportPDF(models.AbstractModel):
    _name = 'report.taps_lms.lms_pdf_template'
    _description = 'LMS pdf'

    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('start_date', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('start_date', '<=', data.get('date_to')))
        if data.get('criteria_id'):
            domain.append(('criteria_id', '=', (data.get('criteria_id'))))
        if data.get('session_ids'):
            domain.append(('name', '=', (data.get('session_ids'))))
        if data.get('venue'):
            domain.append(('venue', '=', data.get('venue')))
        if data.get('instructor_id'):
            domain.append(('instructor_id', '=', (data.get('instructor_id'))))
        if data.get('participation_group'):
            domain.append(('participation_group', '=', data.get('participation_group')))
        # raise UserError((domain))
        docs = self.env['lms.session'].search(domain)
        
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'lms.session',
            'docs': docs,
            # 'datas': data,
        }
class LmsAttendanceReportPDF(models.AbstractModel):
    _name = 'report.taps_lms.lms_attendance_pdf_template'
    _description = 'LMS pdf'

    def _get_report_values(self, docids, data=None):
        domain = []            
        # if data.get('date_from'):
        #     domain.append(('start_date', '>=', data.get('date_from')))
        # if data.get('date_to'):
        #     domain.append(('start_date', '<=', data.get('date_to')))
            
        if data.get('criteria_id'):
            domain.append(('criteria_id', '=', (data.get('criteria_id'))))
        if data.get('session_ids'):
            domain.append(('name', '=', (data.get('session_ids'))))
        if data.get('venue'):
            domain.append(('venue', '=', data.get('venue')))
        if data.get('instructor_id'):
            domain.append(('instructor_id', '=', (data.get('instructor_id'))))
        if data.get('participation_group'):
            domain.append(('participation_group', '=', data.get('participation_group')))
        # raise UserError((domain))
        docs = self.env['lms.session'].search(domain)
        if data.get('date_from'):
            st_date = fields.Datetime.from_string(data.get('date_from'))
            docs = docs.filtered(lambda x: (x.start_date + timedelta(hours=6)).date() == st_date.date())
        
        # raise UserError((docs.id,domain))
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'lms.session'), ('res_id', '=', docs.id)])
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'lms.session',
            'docs': docs,
            'datas': attachment,
        }

class LmsXlsxReport(models.AbstractModel):
    _name = 'report.taps_lms.lms_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'LMS xlsx'

    def generate_xlsx_report(self, workbook, data, partners):
        domain = []
        if data.get('criteria_id'):
            domain.append(('criteria_id', '=', (data.get('criteria_id'))))
        if data.get('session_ids'):
            domain.append(('name', '=', (data.get('session_ids'))))
        if data.get('venue'):
            domain.append(('venue', '=', data.get('venue')))
        if data.get('instructor_id'):
            domain.append(('instructor_id', '=', (data.get('instructor_id'))))
        if data.get('participation_group'):
            domain.append(('participation_group', '=', data.get('participation_group')))
        # raise UserError((domain))
        docs = self.env['lms.session'].search(domain)
        # if data.get('date_from'):
        #     st_date = fields.Datetime.from_string(data.get('date_from'))
        #     docs = docs.filtered(lambda x: (x.start_date + timedelta(hours=6)).date() == st_date.date())

        sheet = workbook.add_worksheet('LMS Report')
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#fffbed', 'border': True})
        title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 20, 'bg_color': '#f2eee4', 'border': True})
        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
        header_row_style_1 = workbook.add_format({'align': 'center','num_format': 'dd-mm-yyyy hh:mm AM/PM'})
        header_row_style_2 = workbook.add_format({'align': 'center','num_format': '0.00'})
        header_row_style_3 = workbook.add_format({'align': 'center'})

        sheet.merge_range('A1:F1', 'LMS Report', title)

        # courses = self.env['lms.course'].search(domain)
        row = 3
        col = 0
        # Header row
        sheet.set_column(0, 4, 18)
        # sheet.write(row, col, 'Title', header_row_style)
        sheet.write(row, col, 'Plan date', header_row_style)
        sheet.write(row, col+1, 'Duration', header_row_style)
        sheet.write(row, col+2, 'No. of seats', header_row_style)
        sheet.write(row, col+3, 'Facilitator', header_row_style)
        sheet.write(row, col+4, 'Attendees', header_row_style)
        row += 2
        sheet.merge_range(f"A{row}:E{row}", docs[0].display_name, bold)
        for course in docs:
            
            # row += 1
            for doc in course.filtered(lambda x: x.id==course.id):
                
                # sheet.write(row, col, doc.name.display_name)
                sheet.write(row, col, doc.start_date, header_row_style_1)
                sheet.write(row, col+1, doc.duration, header_row_style_2)
                sheet.write(row, col+2, doc.seats, header_row_style_3)
                sheet.write(row, col+3, '; '.join([inst.name for inst in doc.instructor_id if inst]))
                sheet.write(row, col+4, doc.presents_count, header_row_style_3)
                row += 1
        # row += 1 
