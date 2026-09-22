"""Follow-up of D02: an upper-bound amount is not an exact eaten quantity."""
import json
import unittest
from qa_w003_independent import ACTOR,ORIGIN,context,proposal
from nutrition_app.interpretation import resolve
from nutrition_contracts.parser import ParserOutput

class QuantityBoundQA(unittest.TestCase):
    def test_qa11_upper_bound_is_not_an_exact_portion(self):
        text='Съела до 100 г творога 5% «Марка А»'
        result=resolve(ACTOR,ORIGIN,context(text),ParserOutput.model_validate_json(json.dumps(proposal(text))))
        self.assertEqual(result.status,'unresolved')
        self.assertIsNone(result.command)

if __name__=='__main__':unittest.main(verbosity=2)
