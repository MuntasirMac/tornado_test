import os
import weasyprint
from jinja2 import Environment, FileSystemLoader

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(ROOT, 'assets')

TEMPLAT_SRC = os.path.join(ROOT, 'templates')
CSS_SRC = os.path.join(ROOT, 'static/css')
DEST_DIR = os.path.join(ROOT, 'output')

TEMPLATE = 'single_order_invoice.html'
CSS = 'style.css'
OUTPUT_FILENAME = 'single-order-invoice-report.pdf'

def pdf_render():
    print('start generate report...')
    env = Environment(loader=FileSystemLoader(TEMPLAT_SRC))
    template = env.get_template(TEMPLATE)
    css = os.path.join(CSS_SRC, CSS)

    # variables
    template_vars = { 'assets_dir': 'file://' + ASSETS_DIR}

    # rendering to html string
    rendered_string = template.render(template_vars)
    html = weasyprint.HTML(string=rendered_string)
    report = os.path.join(DEST_DIR, OUTPUT_FILENAME)
    # html.write_pdf(report, stylesheets=[css])
    html.write_pdf(report)
    print('file is generated successfully and under {}', DEST_DIR)


def pdf_assets(template, CSS=None):
    env = Environment(loader=FileSystemLoader(TEMPLAT_SRC))
    # CSS_SRC = os.path.join(ROOT, 'static/css')
    template = env.get_template(template)
    # css = os.path.join(CSS_SRC, CSS)
    return template, CSS


if __name__ == '__main__':
    pdf_render()