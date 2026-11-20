"""Apresentação com dados sintéticos, sem consultar banco."""
from pathlib import Path
import unittest
from jinja2 import Environment, FileSystemLoader, select_autoescape


class MatrizDashboard(unittest.TestCase):
    def test_casas_vazia_singular_plural_e_link(self):
        env = Environment(loader=FileSystemLoader(Path(__file__).parents[1]/'app/paginas'),
                          autoescape=select_autoescape())
        macro = env.get_template('_celula_matriz_dashboard.html').module.celula_matriz
        for n in (0, 1, 2):
            with self.subTest(riscos=n):
                html = str(macro(dict(numero=n, faixa='Crítico'), '#b3261e', '#fff', '/lista?celula=5_5'))
                self.assertIn('Crítico', html)
                if n:
                    self.assertIn('dash-matriz-com-risco', html)
                    self.assertIn(f'<strong>{n}</strong> '+('risco<' if n==1 else 'riscos<'), html)
                    self.assertIn('href="/lista?celula=5_5"', html)
                else:
                    self.assertNotIn('<a ', html)
                    self.assertNotIn('<strong>', html)
                    self.assertNotIn('0 riscos', html)
