"""Independent offline checks for W004's numeric HTTP diagnostic follow-up."""
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SOURCE=Path(os.environ.get('HTTP_QA_SOURCE','/private/tmp/nutrition-http-status-review-4ki38q0u'))
sys.path.insert(0,str(SOURCE))
from nutrition_app.__main__ import main
from nutrition_app.interpretation import ParserRequest,ParserRejected,ParserUnavailable
from nutrition_app.nebius import NebiusConfig,NebiusParser

SECRET='synthetic-qa-token-not-real'
PRIVATE='synthetic-provider-private-sentinel'

def request():return ParserRequest('Съела 100 г хлеба','2026-09-23','Europe/Berlin',())

class DiagnosticQA(unittest.TestCase):
    def test_qa01_cli_status_is_visible_without_body_reason_or_header_output(self):
        class Reply:
            status=401
            def getheader(self,name):
                self.assert_header=name
                return PRIVATE
            @property
            def reason(self):raise AssertionError('Reason phrase must never be inspected')
            def read(self,*args):raise AssertionError('Error body must never be read')
        reply=Reply()
        with patch('nutrition_app.nebius.http.client.HTTPSConnection') as conn, \
                patch('nutrition_app.__main__.engine_for') as engine, \
                patch.dict(os.environ,{'NEBIUS_API_KEY':SECRET,'NUTRITION_LLM_MODEL':'qa/model'}), \
                patch('sys.argv',['nutrition_app','nebius-smoke']), \
                patch('sys.stdout',new_callable=io.StringIO) as stdout, \
                patch('sys.stderr',new_callable=io.StringIO) as stderr:
            conn.return_value.getresponse.return_value=reply
            with self.assertRaises(SystemExit) as caught:main()
            self.assertEqual(caught.exception.code,1)
            message=json.loads(stdout.getvalue())
            self.assertEqual(message,{'error':'parser_rejected','message':
                'Nebius rejected the request (HTTP 401); check credentials, model and schema support'})
            self.assertEqual(stderr.getvalue(),'')
            self.assertNotIn(SECRET,stdout.getvalue());self.assertNotIn(PRIVATE,stdout.getvalue())
            self.assertEqual(reply.assert_header,'Retry-After')
            conn.return_value.request.assert_called_once();conn.return_value.close.assert_called_once()
            engine.assert_not_called()
    def test_qa02_noninteger_status_never_reaches_interpolated_diagnostic(self):
        class HostileInt(int):
            def __str__(self):raise AssertionError('Untrusted status formatter invoked')
            def __format__(self,spec):raise AssertionError('Untrusted status formatter invoked')
        for status in [PRIVATE,401.0,True,None,HostileInt(401)]:
            parser=NebiusParser(NebiusConfig(SECRET,'qa/model'),
                request=lambda body,timeout:(status,{},b''))
            with self.assertRaises(ParserRejected) as caught:parser.parse(request())
            self.assertEqual(str(caught.exception),'Invalid provider response envelope')
    def test_qa03_base_request_fingerprint_and_classification_are_unchanged(self):
        name='nutrition_app._qa_baseline_nebius'
        baseline=types.ModuleType(name);baseline.__file__=str(SOURCE/'nutrition_app/nebius.py');baseline.__package__='nutrition_app'
        sys.modules[name]=baseline
        try:
            exec(compile(Path(__file__).with_name('baseline-nebius.py.txt').read_text(),baseline.__file__,'exec'),baseline.__dict__)
            current=NebiusParser(NebiusConfig(SECRET,'qa/model'))
            prior=baseline.NebiusParser(baseline.NebiusConfig(SECRET,'qa/model'))
            self.assertEqual(current.version,prior.version)
            self.assertEqual(current._payload(request()),prior._payload(request()))
            for status in [301,307,400,401,402,403,404,422,408,429,500,503,599]:
                classifications=[]
                for module in [baseline,sys.modules['nutrition_app.nebius']]:
                    parser=module.NebiusParser(module.NebiusConfig(SECRET,'qa/model'),
                        request=lambda body,timeout:(status,{'Retry-After':'120'},b''))
                    with self.assertRaises((ParserRejected,ParserUnavailable)) as caught:parser.parse(request())
                    classifications.append((caught.exception.code,getattr(caught.exception,'retry_after',None)))
                self.assertEqual(classifications[0],classifications[1])
        finally:sys.modules.pop(name,None)

if __name__=='__main__':unittest.main(verbosity=2)
