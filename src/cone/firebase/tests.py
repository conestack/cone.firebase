from cone.app import testing
from node.tests import NodeTestCase
import sys
import unittest


class FirebaseLayer(testing.Security):

    def make_app(self, **kw):
        super(FirebaseLayer, self).make_app(**{
            'cone.plugins': 'cone.firebase'
        })


class TestFirebaseTile(NodeTestCase):
    layer = FirebaseLayer()

    def test_foo(self):
        pass


def run_tests():
    from cone.firebase import tests
    from zope.testrunner.runner import Runner

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(tests))

    runner = Runner(found_suites=[suite])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
