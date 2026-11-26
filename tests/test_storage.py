import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        patcher=patch.dict(os.environ,{"MYAI_DATA_DIR":self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        from src import storage
        self.storage=storage

    def tearDown(self):
        self.tmp.cleanup()

    def test_business_databases_are_separate(self):
        a=self.storage.db_path("si_natural")
        b=self.storage.db_path("paymob_crm")
        self.assertNotEqual(a,b)
        self.assertNotEqual(a.parent,b.parent)

    def test_unknown_business_rejected(self):
        with self.assertRaises(ValueError):
            self.storage.db_path("other")

    def test_approval_workflow(self):
        from src.orchestrator import create_task
        task=create_task("si_natural","content_creation","Draft a product post","campaign_publishing")
        self.storage.save_task(task)
        self.assertEqual(len(self.storage.list_approvals("si_natural")),1)
        self.assertTrue(self.storage.decide_approval("si_natural",task["id"],"approved","Reviewed"))
        self.assertEqual(self.storage.list_approvals("si_natural"),[])
        self.assertEqual(self.storage.list_tasks("si_natural")[0]["status"],"approved")

if __name__=="__main__": unittest.main()
