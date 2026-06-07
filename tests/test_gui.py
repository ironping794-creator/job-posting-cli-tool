import unittest

import job_posting_cli.gui as gui


class GuiTests(unittest.TestCase):
    def test_gui_entrypoint_exists(self):
        self.assertTrue(callable(gui.main))
        self.assertTrue(hasattr(gui, "JobPostingApp"))


if __name__ == "__main__":
    unittest.main()
