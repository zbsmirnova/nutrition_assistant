"""Independent positive regression: dot decimals are quantities, not dates."""
import json
import unittest
from test_w003_independent import ACTOR,ORIGIN,context,proposal
from nutrition_app.interpretation import resolve
from nutrition_contracts.parser import ParserOutput

class DecimalEvidenceQA(unittest.TestCase):
    def test_qa10_decimal_quantity_and_matching_fat_are_not_dates(self):
        cases=[('Съела 12.5 г творога 5% «Марка А»','12.5','5'),
               ('Съела 100 г творога 5.5% «Марка А»','100','5.5')]
        for text,grams,fat in cases:
            with self.subTest(text=text):
                ctx=context(text)
                ctx['candidates'][0].update(name='творог '+fat+'% «Марка А»',declared_fat_percent=fat)
                result=resolve(ACTOR,ORIGIN,ctx,ParserOutput.model_validate_json(json.dumps(
                    proposal(text,quantity={'amount':grams,'unit':'g'}))))
                self.assertEqual(result.status,'ready')
                self.assertEqual(result.command.command.food.components[0].quantity.edible_g,grams)

if __name__=='__main__':unittest.main(verbosity=2)
