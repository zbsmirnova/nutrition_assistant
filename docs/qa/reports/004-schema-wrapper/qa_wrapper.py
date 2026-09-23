"""Independent W004 wrapper checks using the downloaded provider contract, offline."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types
import unittest
from copy import deepcopy
from jsonschema import Draft202012Validator

SOURCE=Path(os.environ.get('WRAPPER_QA_SOURCE','/private/tmp/nutrition-wrapper-review-udd8hae1'))
sys.path.insert(0,str(SOURCE))
from nutrition_app import nebius
from nutrition_app.interpretation import ParserRequest,ParserRejected

HERE=Path(__file__).parent
SECRET='synthetic-wrapper-qa-token'
TEXT='Съела 100 г хлеба'

def request():
    return ParserRequest(TEXT,'2026-09-23','Europe/Berlin',({'ref':'c1','name':'Хлеб',
        'nutrition_basis':'per_100_g','weight_basis':'as_sold','food_kind':'general','declared_fat_percent':None,
        'user_id':'DO-NOT-SEND-OWNER','version_id':'DO-NOT-SEND-VERSION','observations':'DO-NOT-SEND-WEIGHT'},))

def response(candidate='c1'):
    output={'schema_version':'1.0','actions':[{'kind':'add_food','action_id':'a1','evidence':TEXT,
        'depends_on':[],'unresolved':[],'food':{'kind':'candidate','candidate_kind':'product','candidate_ref':candidate},
        'quantity':{'amount':'100','unit':'g'},'weight_basis':'as_sold','date_hint':{'text':None},'meal':'unspecified'}]}
    return json.dumps({'choices':[{'index':0,'finish_reason':'stop','message':{
        'role':'assistant','content':json.dumps(output)}}]}).encode()

class WrapperQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name='nutrition_app._qa_wrapper_baseline'
        cls.baseline=types.ModuleType(cls.name)
        cls.baseline.__file__=str(SOURCE/'nutrition_app/nebius.py');cls.baseline.__package__='nutrition_app'
        sys.modules[cls.name]=cls.baseline
        exec(compile((HERE/'baseline-nebius.py.txt').read_text(),cls.baseline.__file__,'exec'),cls.baseline.__dict__)
        cls.official_raw=(HERE/'provider-openapi.json').read_bytes()
        cls.official=json.loads(cls.official_raw)
    @classmethod
    def tearDownClass(cls):sys.modules.pop(cls.name,None)
    def parser(self,module,key=SECRET,raw=None):
        return module.NebiusParser(module.NebiusConfig(key,'qa/model'),request=lambda body,timeout:(200,{},response() if raw is None else raw))
    def test_qa01_official_provenance_contract_rejects_base_accepts_fix(self):
        digest=hashlib.sha256(self.official_raw).hexdigest()
        self.assertEqual(digest,'e6ba0e6dc303e48fb8eec5d62fcc29cfc2f552a7725a2ae0903719023961ddb5')
        fixture=json.loads((SOURCE/'tests/fixtures/nebius-response-format-openapi.json').read_text())
        self.assertEqual(fixture['source_sha256'],digest)
        self.assertEqual(fixture['api_version'],self.official['info']['version'])
        for name,definition in fixture['schema']['components']['schemas'].items():
            self.assertEqual(definition,self.official['components']['schemas'][name])
        ref=self.official['paths']['/v1/chat/completions']['post']['requestBody']['content']['application/json']['schema']['$ref']
        validator=Draft202012Validator({'$ref':ref,'components':self.official['components']})
        before=json.loads(self.parser(self.baseline)._payload(request()))
        after=json.loads(self.parser(nebius)._payload(request()))
        self.assertFalse(validator.is_valid(before))
        validator.validate(after)
        old_schema=before['response_format']['json_schema']
        self.assertNotIn('name',old_schema);self.assertNotIn('schema',old_schema)
        wrapper=after['response_format']['json_schema']
        self.assertEqual(wrapper['name'],'nutrition_parser_output');self.assertIs(wrapper['strict'],True)
        self.assertEqual(self.official['components']['schemas']['JsonSchemaResponseFormat']['required'],['name','schema'])
    def test_qa02_only_wrapper_changes_inner_schema_prompt_policy_privacy_preserved(self):
        before=json.loads(self.parser(self.baseline)._payload(request()))
        after=json.loads(self.parser(nebius)._payload(request()))
        old=before.pop('response_format');new=after.pop('response_format')
        self.assertEqual(old['json_schema'],new['json_schema']['schema'])
        self.assertEqual(before,after)
        for forbidden in [SECRET,'DO-NOT-SEND-OWNER','DO-NOT-SEND-VERSION','DO-NOT-SEND-WEIGHT']:
            self.assertNotIn(forbidden,json.dumps(after))
        self.assertEqual(self.parser(self.baseline).parse(request()),self.parser(nebius).parse(request()))
        for module in [self.baseline,nebius]:
            with self.assertRaises(ParserRejected):self.parser(module,raw=response('foreign-token')).parse(request())
    def test_qa03_identity_changes_from_base_but_not_with_key_rotation(self):
        old=self.parser(self.baseline);new=self.parser(nebius);rotated=self.parser(nebius,key='synthetic-rotated-token')
        self.assertNotEqual(old.version,new.version)
        self.assertEqual(new.version,rotated.version)
        self.assertEqual(new._payload(request()),rotated._payload(request()))
        self.assertNotIn(SECRET,new.version)

if __name__=='__main__':unittest.main(verbosity=2)
