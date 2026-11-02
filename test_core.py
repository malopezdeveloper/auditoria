import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import collect, device, record, save, load

class Tests(unittest.TestCase):
    def test_manual_review_and_history(self):
        d=device('USB','Puerto','manual:1');d['row_id']='1'
        self.assertEqual(d['result'],'Pendiente')
        with self.assertRaises(ValueError):record(d,'PASS','','')
        with self.assertRaises(ValueError):record(d,'FAIL','Miguel','')
        record(d,'FAIL','Miguel','No reconoce memoria')
        record(d,'PASS','Miguel','Verificado tras reparación')
        self.assertEqual(len(d['history']),2)
        self.assertEqual(d['history'][0]['result'],'FAIL')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'audit.json'
            a={'schema':1,'devices':[d]};save(a,path)
            self.assertEqual(load(path),a)
    def test_windows_inventory_stays_pending(self):
        import json
        from types import SimpleNamespace
        raw={'identity':{'bios':[{'SerialNumber':'TEST'}]},'errors':['battery: failed'],
             'devices':[{'id':'USB:1','category':'USB','name':'Hub','os_status':'OK','details':{}}]}
        with patch('core.platform.system',return_value='Windows'),patch('core.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(raw).encode())):
            a=collect()
        self.assertEqual(a['devices'][0]['result'],'Pendiente')
        self.assertEqual(a['errors'],['battery: failed'])
    def test_linux_scan(self):
        import platform
        if platform.system()!='Linux':self.skipTest('Linux only')
        a=collect()
        self.assertTrue(a['devices'])
        self.assertTrue(all(d['result']=='Pendiente' for d in a['devices']))
        self.assertEqual(len({d['row_id'] for d in a['devices']}),len(a['devices']))

if __name__=='__main__':unittest.main()
