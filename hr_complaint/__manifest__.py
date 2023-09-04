# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Employee Complaints',
    'version': '14.0.1.0.0',
	'license': 'AGPL-3',
    'author': 'One Click Software',
    'category': 'Human Resources',
    'website': 'http://oneclick.solutions',
    'summary': 'Performance Management, Complaints,',
    'depends': ['hr', 'mail', 'calendar'],
    'description': """
Employee Complaint Record
==========================
Creates forms and reports for reporting complaints against employees
""",
    "data": [
        'views/hr_complaint_view.xml',
        'report/hr_complaint_report.xml',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
