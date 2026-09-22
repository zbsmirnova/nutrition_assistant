"""Independent W003 probes. No live APIs; each DB case owns a random schema."""
import os
from pathlib import Path
import sys
SOURCE=Path(os.environ.get('W003_SOURCE_ROOT','/private/tmp/nutrition-w003-review-eez3dwmt'))
sys.path.insert(0,str(SOURCE))
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
import json
from threading import Event
import unittest
from uuid import UUID,uuid4
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from alembic import command as alembic_command
from alembic.config import Config
from nutrition_app import schema as db
from nutrition_app.db import engine_for,database_url,migrate,ROOT
from nutrition_app.demo import seed_user,message,food_command
from nutrition_app.service import FoodService
from nutrition_app.conversation import ConversationWorker
from nutrition_app.interpretation import resolve,CONTEXT_VERSION,RESOLVER_VERSION
from nutrition_contracts.parser import ParserOutput

ACTOR=UUID('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
ORIGIN=UUID('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')
VERSION=UUID('cccccccc-cccc-4ccc-8ccc-cccccccccccc')
PRODUCT='творог 5% «Марка А»'
TEXT='Съела 100 г творога 5% «Марка А»'

def proposal(text,**changes):
    action={'kind':'add_food','action_id':'a1','evidence':text,'depends_on':[],'unresolved':[],
        'food':{'kind':'candidate','candidate_kind':'product','candidate_ref':'c1'},
        'quantity':{'amount':'100','unit':'g'},'weight_basis':'as_sold',
        'date_hint':{'text':None},'meal':'unspecified'}
    action.update(changes)
    return {'schema_version':'1.0','actions':[action]}

def context(text):
    return {'source_text':text,'local_date':'2026-09-22','time_zone':'Europe/Berlin',
        'context_revision':0,'context_version':CONTEXT_VERSION,'resolver_version':RESOLVER_VERSION,
        'schema_version':'1.0','has_reply':False,'forwarded':False,'catalog_overflow':False,
        'candidates':[{'ref':'c1','version_id':str(VERSION),'name':PRODUCT,
          'nutrition_basis':'per_100_g','weight_basis':'as_sold','food_kind':'dairy','declared_fat_percent':'5'}]}

class ResolverEvidenceQA(unittest.TestCase):
    def result(self,text,ctx=None,**changes):
        return resolve(ACTOR,ORIGIN,ctx or context(text),ParserOutput.model_validate_json(json.dumps(proposal(text,**changes))))
    def test_qa01_dairy_source_cannot_be_relabelled_as_general_food(self):
        text='Съела 100 г творога'
        ctx=context(text);ctx['candidates'][0].update(name='Хлеб',food_kind='general',declared_fat_percent=None)
        self.assertEqual(self.result(text,ctx).status,'unresolved')
    def test_qa02_explicit_other_brand_cannot_select_catalog_brand(self):
        text='Съела 100 г творога 5% «Марка Б»'
        self.assertEqual(self.result(text).status,'unresolved')
    def test_qa03_quantity_range_is_not_an_exact_portion(self):
        for text in ['Съела 80–100 г творога 5% «Марка А»','Съела 80—100 г творога 5% «Марка А»']:
            with self.subTest(text=text):self.assertEqual(self.result(text).status,'unresolved')
    def test_qa04_omitted_unsupported_relative_date_cannot_default_to_today(self):
        text='Съела 100 г творога 5% «Марка А» три дня назад'
        result=self.result(text)
        self.assertEqual(result.status,'unresolved')
        self.assertIsNone(result.pending_food_date)
    def test_qa05_cooked_source_cannot_use_raw_profile(self):
        text='Съела 100 г вареной курицы'
        ctx=context(text);ctx['candidates'][0].update(name='Курица',food_kind='general',
            declared_fat_percent=None,weight_basis='raw')
        self.assertEqual(self.result(text,ctx,weight_basis='raw').status,'unresolved')
    def test_qa06_exact_branded_quantity_remains_supported(self):
        result=self.result(TEXT)
        self.assertEqual(result.status,'ready')
        self.assertEqual(result.command.command.food.components[0].product_version_id,VERSION)
        self.assertEqual(result.command.command.food.components[0].quantity.edible_g,'100')
        self.assertEqual(result.command.command.food.effective_date,date(2026,9,22))

class Controlled:
    version='qa-w003-independent-v1'
    def __init__(self,output=None,callback=None):self.output=output;self.callback=callback;self.calls=0
    def parse(self,request):
        self.calls+=1
        if self.callback:self.callback(request)
        return json.dumps(self.output or proposal(request.source_text))

class WorkerRecoveryQA(unittest.TestCase):
    def setUp(self):
        url=database_url();self.assertIn(make_url(url).host,{'localhost','127.0.0.1','::1'})
        self.schema='nqa3_'+uuid4().hex;self.admin=engine_for(url);self.engine=None
        self.addCleanup(self.cleanup)
        with self.admin.begin() as c:c.execute(sa.schema.CreateSchema(self.schema))
        self.engine=engine_for(url,schema=self.schema);migrate(self.engine)
        self.seed=seed_user(self.engine,name=PRODUCT,food_kind='dairy',declared_fat_percent='5')
        self.actor=self.seed.user_id;self.service=FoodService(self.engine);self.worker=ConversationWorker(self.engine)
    def cleanup(self):
        if self.engine:self.engine.dispose()
        with self.admin.begin() as c:c.execute(sa.schema.DropSchema(self.schema,cascade=True,if_exists=True))
        self.admin.dispose()
    def source(self,number=1,text=TEXT):return self.service.accept_message(self.actor,message(self.seed,number,text=text))
    def rows(self,table):
        with self.engine.connect() as c:return list(c.execute(sa.select(table)).mappings())
    def test_qa07_stale_parser_failure_cannot_replace_newer_terminal_interpretation(self):
        origin=self.source();entered,release=Event(),Event()
        def delayed_failure(_):
            entered.set()
            if not release.wait(10):raise AssertionError('coordination timeout')
            raise RuntimeError('synthetic-private-error')
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(self.worker.run_one,self.actor,Controlled(callback=delayed_failure),origin=origin)
            try:
                self.assertTrue(entered.wait(5))
                with self.engine.begin() as c:c.execute(db.conversation_jobs.update().values(lease_until=sa.func.now()-timedelta(seconds=1)))
                nonlog={'schema_version':'1.0','actions':[{'kind':'non_logging','action_id':'a1','evidence':TEXT,
                    'depends_on':[],'unresolved':[],'reason':'planned_food'}]}
                winner=self.worker.run_one(self.actor,Controlled(nonlog),origin=origin)
                self.assertEqual(winner['status'],'non_logging')
            finally:release.set()
            self.assertEqual(future.result(timeout=10)['status'],'lost_claim')
        self.assertEqual(self.rows(db.conversation_jobs)[0]['status'],'non_logging')
        self.assertEqual(self.rows(db.food_entries),[])
    def test_qa08_frozen_command_resumes_with_different_adapter_and_no_parse(self):
        origin=self.source()
        def fault(point):
            if point=='after_prepare':raise RuntimeError('synthetic stop')
        with self.assertRaises(RuntimeError):self.worker.run_one(self.actor,Controlled(),origin=origin,fault=fault)
        frozen=self.rows(db.prepared_operations)[0]['command']
        parser=Controlled(callback=lambda _:self.fail('must not parse prepared work'))
        parser.version='different-adapter-version'
        result=ConversationWorker(self.engine).run_one(self.actor,parser,origin=origin)
        self.assertEqual(result['status'],'applied');self.assertEqual(parser.calls,0)
        self.assertEqual(self.rows(db.prepared_operations)[0]['command'],frozen)
        self.assertEqual(len(self.rows(db.food_entries)),1);self.assertEqual(len(self.rows(db.outbox)),1)
    def test_qa09_populated_migration_preserves_sent_receipt_and_pending_source(self):
        first,second=self.source(),self.source(2)
        original=self.service.apply(self.actor,food_command(self.seed,first,grams='100'))
        self.service.prepare(self.actor,food_command(self.seed,second,grams='100'))
        with self.engine.begin() as c:
            c.execute(db.outbox.update().values(status='sent',sent_at=sa.func.now(),telegram_message_id=7711,attempts=1))
        config=Config(str(ROOT/'alembic.ini'));config.set_main_option('script_location',str(ROOT/'migrations'))
        with self.engine.begin() as c:
            config.attributes['connection']=c;alembic_command.downgrade(config,'0003')
        migrate(self.engine)
        parser=Controlled(callback=lambda _:self.fail('legacy command must not parse'))
        for origin in [first,second]:self.assertEqual(self.worker.run_one(self.actor,parser,origin=origin)['status'],'applied')
        existing=[r for r in self.rows(db.outbox) if r['operation_id']==original.result.operation_id][0]
        self.assertEqual((existing['status'],existing['telegram_message_id'],existing['attempts']),('sent',7711,1))
        self.assertEqual(existing['payload'],original.model_dump(mode='json'))
        self.assertEqual(len(self.rows(db.food_entries)),2)
        self.assertEqual(parser.calls,0)

if __name__=='__main__':unittest.main(verbosity=2)
