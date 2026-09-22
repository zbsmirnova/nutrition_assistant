"""Independent W002 checks; offline protocol and isolated PostgreSQL probes."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from threading import Barrier
import unittest
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from nutrition_app import schema as db
from nutrition_app.db import ROOT,database_url,engine_for,migrate
from nutrition_app.demo import food_command,message,seed_user
from nutrition_app.errors import Conflict
from nutrition_app.outbox import Delivery,OutboxWorker
from nutrition_app.telegram import TelegramClient,TelegramError,TelegramIngress,TelegramPoller,TelegramSender,TelegramUnavailable,link_account


def wire(seed,number=1):
    msg=message(seed,number)
    return {'update_id':number,'message':{'message_id':number,
        'from':{'id':seed.telegram_user_id,'is_bot':False},
        'chat':{'id':seed.telegram_user_id,'type':'private'},
        'date':int(msg.sent_at.timestamp()),'text':'Synthetic transport probe'}}


class API:
    bot_id=101
    def __init__(self,updates):
        self.updates=updates
        self.calls=[]
    def call(self,method,payload,*,timeout=15):
        self.calls.append((method,payload))
        assert method=='getUpdates'
        return self.updates


class ReceiptProtocolQA(unittest.TestCase):
    def test_qa01_receipt_chat_identity_requires_integer_not_coercive_equality(self):
        outcome=json.loads((ROOT/'contracts/v1/examples/01_add_food.json').read_text())['results'][0]
        item=Delivery(id=uuid4(),claim_token=uuid4(),user_id=uuid4(),private_chat_id=1,payload=outcome,bot_id=101)
        for claimed in (True,1.0,'1'):
            with self.subTest(claimed=repr(claimed)):
                client=TelegramClient('101:synthetic',101,request=lambda *args:(200,
                    {'ok':True,'result':{'message_id':7,'chat':{'id':claimed}}}))
                with self.assertRaises(TelegramUnavailable):
                    TelegramSender(client).send(item)


class TransportDatabaseQA(unittest.TestCase):
    def setUp(self):
        url=database_url()
        self.assertIn(make_url(url).host,{'127.0.0.1','localhost','::1'})
        self.schema='nqa2_'+uuid4().hex
        self.admin=engine_for(url)
        self.engine=None
        self.addCleanup(self.cleanup)
        with self.admin.begin() as connection:
            connection.execute(sa.schema.CreateSchema(self.schema))
        self.engine=engine_for(url,schema=self.schema)
        migrate(self.engine)
        self.seed=seed_user(self.engine)
    def cleanup(self):
        if self.engine:self.engine.dispose()
        with self.admin.begin() as connection:
            connection.execute(sa.schema.DropSchema(self.schema,cascade=True,if_exists=True))
        self.admin.dispose()
    def rows(self,table):
        with self.engine.connect() as connection:
            return list(connection.execute(sa.select(table)).mappings())
    def cursor(self):
        return self.rows(db.telegram_poll_cursors)[0]['next_update_id']
    def no_food(self):
        for table in (db.food_entries,db.applied_operations,db.outbox):
            self.assertEqual(len(self.rows(table)),0)

    def test_qa02_checkpoint_database_failure_keeps_source_and_releases_lock(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("""CREATE FUNCTION qa_checkpoint_fail() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'QA deliberate checkpoint failure'; END; $$""")
            connection.exec_driver_sql('CREATE TRIGGER qa_failure BEFORE UPDATE ON telegram_poll_cursors '
                                       'FOR EACH ROW EXECUTE FUNCTION qa_checkpoint_fail()')
        api=API([wire(self.seed,77)])
        with self.assertRaises(DBAPIError):
            TelegramPoller(self.engine,api).poll_once(timeout=0)
        original=self.rows(db.inbox_updates)[0]['id']
        self.assertEqual(self.cursor(),0)
        self.no_food()
        with self.engine.begin() as connection:
            connection.exec_driver_sql('DROP TRIGGER qa_failure ON telegram_poll_cursors')
        # A different poller can acquire the released session lock and replay.
        result=TelegramPoller(self.engine,api).poll_once(timeout=0)
        self.assertEqual(result['next_update_id'],78)
        self.assertEqual(api.calls[-1][1]['offset'],0)
        self.assertEqual([r['id'] for r in self.rows(db.inbox_updates)],[original])

    def test_qa03_partial_batch_failure_replays_committed_prefix_once(self):
        first,second=wire(self.seed,11),wire(self.seed,12)
        second['message']['date']=True
        api=API([second,first])
        with self.assertRaises(TelegramError):
            TelegramPoller(self.engine,api).poll_once(timeout=0)
        self.assertEqual(self.cursor(),0)
        before=self.rows(db.inbox_updates)
        self.assertEqual(len(before),1)
        self.assertEqual(before[0]['telegram_update_id'],11)
        api.updates=[wire(self.seed,11),wire(self.seed,12)]
        self.assertEqual(TelegramPoller(self.engine,api).poll_once(timeout=0)['next_update_id'],13)
        after=self.rows(db.inbox_updates)
        self.assertEqual(len(after),2)
        self.assertIn(before[0]['id'],[r['id'] for r in after])
        self.no_food()

    def test_qa04_reply_and_forward_metadata_cannot_change_on_replay(self):
        update=wire(self.seed)
        update['message'].update(reply_to_message={'message_id':55},forward_origin={'type':'hidden_user'})
        ingress=TelegramIngress(self.engine,101)
        source=ingress.accept(update)
        for field,value in [('reply_to_message',{'message_id':56}),('forward_origin',None)]:
            changed=deepcopy(update)
            if value is None:changed['message'].pop(field)
            else:changed['message'][field]=value
            with self.assertRaises(Conflict):ingress.accept(changed)
        stored=self.rows(db.inbox_updates)
        self.assertEqual(len(stored),1)
        self.assertEqual(stored[0]['id'],source)
        self.assertEqual(stored[0]['reply_to_message_id'],55)
        self.assertTrue(stored[0]['forwarded'])
        self.no_food()

    def test_qa05_sender_runs_after_commit_without_domain_or_claim_row_locks(self):
        service=__import__('nutrition_app.service',fromlist=['FoodService']).FoodService(self.engine)
        source=service.accept_message(self.seed.user_id,message(self.seed))
        outcome=service.apply(self.seed.user_id,food_command(self.seed,source))
        observed=[]
        def request(method,payload,timeout):
            self.assertEqual(method,'sendMessage')
            with self.engine.begin() as connection:
                applied=connection.execute(sa.select(db.applied_operations.c.outcome)).scalar_one()
                self.assertEqual(applied,outcome.model_dump(mode='json'))
                # NOWAIT would fail if the domain or claim transaction were held during send.
                connection.execute(sa.select(db.users).with_for_update(nowait=True)).all()
                row=connection.execute(sa.select(db.outbox).with_for_update(nowait=True)).mappings().one()
                observed.append((row['status'],row['attempts']))
            return 200,{'ok':True,'result':{'message_id':707,'chat':{'id':payload['chat_id']}}}
        sender=TelegramSender(TelegramClient('101:synthetic',101,request=request))
        self.assertEqual(OutboxWorker(self.engine,bot_id=101).dispatch_one(sender),'sent')
        self.assertEqual(observed,[('sending',1)])
        row=self.rows(db.outbox)[0]
        self.assertEqual((row['status'],row['telegram_message_id']),('sent',707))

    def test_qa06_concurrent_operator_linking_cannot_reassign_identity(self):
        other=seed_user(self.engine)
        barrier=Barrier(2)
        def link(actor):
            barrier.wait(timeout=10)
            try:return link_account(self.engine,actor,303,9191,9191)
            except Conflict:return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(link,[self.seed.user_id,other.user_id]))
        self.assertEqual(sum(r is not None for r in results),1)
        mappings=[r for r in self.rows(db.telegram_accounts) if r['bot_id']==303]
        self.assertEqual(len(mappings),1)
        update=wire(self.seed)
        update['message']['from']['id']=9191
        update['message']['chat']['id']=9191
        update['message']['text']='user_id='+str(other.user_id)
        TelegramIngress(self.engine,303).accept(update)
        self.assertEqual(self.rows(db.inbox_updates)[0]['user_id'],mappings[0]['user_id'])
        self.no_food()


if __name__=='__main__':unittest.main(verbosity=2)
