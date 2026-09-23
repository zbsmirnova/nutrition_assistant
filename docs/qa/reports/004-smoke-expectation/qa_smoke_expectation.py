"""Independent offline smoke expectation and confidentiality review."""
from copy import deepcopy
import io,json,os
from pathlib import Path
import sys,types,unittest
from unittest.mock import patch

SOURCE=Path(os.environ.get('SMOKE_QA_SOURCE','/private/tmp/nutrition-smoke-review-clgupvep'))
sys.path.insert(0,str(SOURCE))
from nutrition_app import nebius
from nutrition_app.__main__ import main
from nutrition_app.interpretation import ParserRejected,ParserRequest

TEXT='Съела 100 г творога 5% «Марка А»'
SECRET='synthetic-smoke-qa-secret'
PRIVATE='DO-NOT-PRINT-model-free-text'

def proposal(amount='100'):
    return {'schema_version':'1.0','actions':[{'kind':'add_food','action_id':'a1','evidence':TEXT,
        'depends_on':[],'unresolved':[],'food':{'kind':'candidate','candidate_kind':'product','candidate_ref':'c1'},
        'quantity':{'amount':amount,'unit':'g'},'weight_basis':'as_sold','date_hint':{'text':None},'meal':'unspecified'}]}

def client(module,output,calls=None):
    def send(body,timeout):
        if calls is not None:calls.append(body)
        raw=json.dumps({'id':PRIVATE,'choices':[{'index':0,'finish_reason':'stop','message':{
            'role':'assistant','content':json.dumps(output)}}]}).encode()
        return 200,{},raw
    return module.NebiusParser(module.NebiusConfig(SECRET,'qa/model'),request=send)

class SmokeQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name='nutrition_app._qa_smoke_base';cls.base=types.ModuleType(cls.name)
        cls.base.__package__='nutrition_app';cls.base.__file__=str(SOURCE/'nutrition_app/nebius.py')
        sys.modules[cls.name]=cls.base
        exec(compile(Path(__file__).with_name('baseline-nebius.py.txt').read_text(),cls.base.__file__,'exec'),cls.base.__dict__)
    @classmethod
    def tearDownClass(cls):sys.modules.pop(cls.name,None)
    def test_qa01_exact_base_false_rejection_fixed_without_request_identity_change(self):
        self.assertTrue(self.base.run_synthetic_smoke(client(self.base,proposal()))['expected_action_matched'])
        for amount in ['100.0','100.00','100.000000']:
            old_calls=[];new_calls=[]
            old=client(self.base,proposal(amount),old_calls);new=client(nebius,proposal(amount),new_calls)
            with self.assertRaises(ParserRejected):self.base.run_synthetic_smoke(old)
            self.assertTrue(nebius.run_synthetic_smoke(new)['expected_action_matched'])
            self.assertEqual(old_calls,new_calls);self.assertEqual(len(new_calls),1)
            self.assertEqual(old.version,new.version)
    def test_qa02_wrong_unresolved_nonlogging_and_max_action_proposals_still_fail(self):
        cases=[]
        for value in ['99','100.000001','101']:cases.append(proposal(value))
        bad=proposal();bad['actions'][0]['unresolved']=[{'path':'quantity.amount','reason':'missing'}];cases.append(bad)
        for reason in ['planned_food','general_chat','unsupported','ambiguous_intent']:
            cases.append({'schema_version':'1.0','actions':[{'kind':'non_logging','action_id':'a1','evidence':TEXT,
                'depends_on':[],'unresolved':[],'reason':reason}]})
        many=proposal();many['actions']=[dict(deepcopy(many['actions'][0]),action_id=f'a{i}') for i in range(1,33)];cases.append(many)
        for output in cases:
            with self.assertRaises(ParserRejected) as caught:nebius.run_synthetic_smoke(client(nebius,output))
            self.assertIn('schema_valid=true;',str(caught.exception))
    def test_qa03_cli_free_text_is_redacted_and_diagnostic_size_does_not_grow(self):
        cases=[]
        for count in [1,300]:
            output=proposal();output['actions'][0]['unresolved']=[{'path':f'{PRIVATE}-{i}', 'reason':'missing'} for i in range(count)]
            output['actions'][0]['unresolved'] += [{'path':'quantity.amount','reason':'ambiguous'}]
            cases.append((output,'other,quantity.amount'))
        for key,value in [('food',{'kind':'name','name':PRIVATE}),('date_hint',{'text':PRIVATE})]:
            output=proposal();output['actions'][0][key]=value;cases.append((output,'none'))
        sizes=[]
        for output,expected_fields in cases:
            calls=[];parser=client(nebius,output,calls)
            with patch('nutrition_app.__main__.NebiusParser',return_value=parser), \
                    patch('nutrition_app.__main__.engine_for') as engine, \
                    patch.dict(os.environ,{'NEBIUS_API_KEY':SECRET,'NUTRITION_LLM_MODEL':'qa/model'}), \
                    patch('sys.argv',['nutrition_app','nebius-smoke']), \
                    patch('sys.stdout',new_callable=io.StringIO) as stdout, \
                    patch('sys.stderr',new_callable=io.StringIO) as stderr:
                with self.assertRaises(SystemExit) as caught:main()
                self.assertEqual(caught.exception.code,1)
                emitted=stdout.getvalue()+stderr.getvalue();message=json.loads(stdout.getvalue())
                self.assertEqual(set(message),{'error','message'});self.assertEqual(message['error'],'parser_rejected')
                self.assertIn('unresolved_fields='+expected_fields,message['message'])
                for forbidden in [PRIVATE,SECRET,TEXT,'Марка А']:self.assertNotIn(forbidden,emitted)
                self.assertEqual(stderr.getvalue(),'');self.assertLess(len(emitted),500)
                self.assertEqual(len(calls),1);engine.assert_not_called();sizes.append(len(emitted))
        self.assertEqual(sizes[0],sizes[1])

if __name__=='__main__':unittest.main(verbosity=2)
