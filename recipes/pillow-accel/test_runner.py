#!/usr/bin/env python3

# Doctest doesn't provide JUnit XML output as needed to publish results.
# Doctest does integrate into unittest which provides XML output, but
# this runs all examples as one test so output is difficult to read.
# So use our own runner to create XML.
from sys import exit, argv, path
import argparse
from importlib import import_module
from pathlib import Path
from doctest import DocTestRunner, DocTestFinder
from junit_xml import TestSuite, TestCase
from traceback import format_exc

class XMLDocTestRunner(DocTestRunner):
    """An :class:`doctest.DocTestRunner` that produces JUnit XML output.
    Usage:
    ``r = XMLDocTestRunner()
    for test in doctest.DocTestFinder().find(...):
        r.run(t)
    r.write(outfile)``
    """
    def __init__(self, **kwargs):
        """Create an `XMLDocTestRunner`.
        Optional keyword arguments passed to :func:`~doctest.DocTestRunner.__init__`.
        """
        DocTestRunner.__init__(self, **kwargs)
        self._suites = []
        self._test_cases = {}

    def run(self, test, **kwargs):
        """Run the examples in `test` (a). Generates a test suite
        in the created output.
        Optional keyword arguments passed to :func:`~doctest.DocTestRunner.run`.
        :param test: The :class:`doctest.DocTest` to run examples from
        """
        if test in self._test_cases:
            return # Don't re-run DocTest
        self._test_cases[test] = []
        super().run(test, **kwargs)
        self._suites.append(TestSuite(test.name, self._test_cases[test]))

    def to_xml(self, **kwargs):
        """Get the collected JUnit XML output to.
        Optional keyword arguments passed to :func:`~junit_xml.to_xml_string`.
        """
        return TestSuite.to_xml_string(self._suites, **kwargs)

    def write_xml(self, outfile, **kwargs):
        """Write the collected output to `outfile`.
        Optional keyword arguments passed to :func:`~junit_xml.to_xml_string`.
        :param outfile: A File-like to write output to.
        """
        outfile.write(self.to_xml(**kwargs))

    def report_start(self, out, test, example):
        pass

    def _make_testcase(self, test, example):
        return TestCase(f"Example: {example.source.rstrip()}",
                        file=test.filename, line=test.lineno + example.lineno)

    def report_success(self, out, test, example, got):
        tc = self._make_testcase(test, example)
        self._test_cases[test].append(tc)

    def report_failure(self, out, test, example, got):
        tc = self._make_testcase(test, example)
        tc.add_failure_info(message=f"Expected {repr(example.want)}. Got {repr(got)}.")
        self._test_cases[test].append(tc)

    def report_unexpected_exception(self, out, test, example, exc_info):
        tc = self._make_testcase(test, example)
        tc.add_error_info(message=format_exc())
        self._test_cases[test].append(tc)

def run_tests(modules, outfile):
    xr = XMLDocTestRunner()
    tests = []
    for mod in modules:
        tests.extend(DocTestFinder().find(mod))
    for test in tests:
        xr.run(test)
    with open(outfile, 'w') as f:
        xr.write_xml(f)
    return xr.summarize(verbose=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Python doctests and produce JUnit XML output.")
    parser.add_argument('modules', nargs='+', help="Python modules to gather doctests from")
    parser.add_argument('--no-status', dest='status', action='store_false', help="Don't set exit status on test failure")
    parser.add_argument('-o', '--output', default='doctest_results.xml', help="Output file to write to (default: doctest_results.xml)")
    parser.add_argument('-r', '--root', action='append', help="Specify a module root to add to the import path. Multiple allowed.")
    args = parser.parse_args()
    if args.root:
        path.extend(args.root)
    mods = []
    for name in args.modules:
        if name.endswith('.py'):
            name = name[:-3]
        m = import_module(name)
        mods.append(m)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res = run_tests(mods, out_path)
    print(f"Test results saved to {out_path.absolute()}")
    if res.failed and args.status:
        exit(1)

