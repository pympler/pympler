
import sys
import unittest

from html.parser import HTMLParser
from http.client import HTTPConnection
from io import StringIO
from socket import error as socket_error
from time import sleep
from urllib.error import URLError
from urllib.request import Request, urlopen

from pympler.classtracker import ClassTracker
from pympler.garbagegraph import start_debug_garbage, end_debug_garbage
from pympler.process import get_current_thread_id
from pympler.web import start_profiler, start_in_background

from threading import Thread

_server = None


class Trash(object):
    pass


class Server(Thread):

    def __init__(self):
        super(Server, self).__init__()
        self.daemon = True

    def run(self):
        """
        Redirect bottle logging messages so it doesn't clutter the test output
        and start the web GUI.
        """
        tracker = ClassTracker()
        tracker.track_class(Trash)
        tracked_trash = Trash()
        tracker.create_snapshot()

        # XXX Comment this out when troubleshooting failing tests
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        start_profiler(debug=True, quiet=True, tracker=tracker)


class WebGuiTest(unittest.TestCase):

    defaulthost = 'localhost:8090'
    defaulturl = 'http://' + defaulthost

    class LinkChecker(HTMLParser):

        def __init__(self):
            HTMLParser.__init__(self)
            self.errors = 0

        def follow(self, link):
            if link.startswith('http://'):
                return
            conn = HTTPConnection(WebGuiTest.defaulthost, timeout=5)
            conn.request("GET", link)
            response = conn.getresponse()
            body = response.read()
            conn.close()
            if response.status not in [200, 302, 303, 307]:
                sys.stderr.write('\nLINK-ERROR: %s, %d, %s' % (link, response.status, response.reason))
                if response.status == 500:
                    sys.stderr.write(body.decode())
                self.errors += 1

        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                for name, value in attrs:
                    if name == 'href':
                        self.follow(value)

    def setUp(self):
        """Use the same server for all tests."""
        global _server

        if not _server:
            _server = Server()
            _server.start()
            wait = 5
            running = False
            while not running and wait > 0:
                try:
                    urlopen(WebGuiTest.defaulturl).read()
                    running = True
                except (URLError, socket_error, IOError):
                    wait -= 1
                    sleep(1)

    def get(self, url, status=200):
        conn = HTTPConnection(self.defaulthost, timeout=5)
        conn.request("GET", url)
        response = conn.getresponse()
        body = response.read()
        conn.close()
        self.assertEqual(response.status, status)
        try:
            body = body.decode()
        except UnicodeDecodeError:
            pass
        return body

    def test_overview(self):
        """Test availability of web gui."""

        req = Request(self.defaulturl)
        page = str(urlopen(req).read())
        self.assertTrue("Process overview" in page)

    def test_links(self):
        """Test all linked pages are available."""
        req = Request(self.defaulturl)
        page = str(urlopen(req).read())
        parser = self.LinkChecker()
        parser.feed(page)
        parser.close()
        self.assertEqual(parser.errors, 0)

    def test_static_files(self):
        """Test if static files are served."""
        for filename in ['style.css', 'jquery.flot.min.js']:
            self.get('/static/%s' % filename, status=200)

    def test_traceback(self):
        """Test if stack traces can be viewed.
        First test valid tracebacks, then the invalid ones.
        Also check if we can expand the locals of the current stackframe and
        access size information of local data (dummy).
        """
        class Dummy(object):
            pass

        dummy = Dummy()
        for threadid in sys._current_frames():
            resp = self.get('/traceback/%d' % threadid, status=200)
            if threadid == get_current_thread_id():
                locals_id = id(locals())
                self.assertTrue('id="%d' % locals_id in resp, resp)
                resp = self.get('/objects/%d' % locals_id, status=200)
                self.assertTrue('dummy' in resp, resp)
                self.assertTrue('id="%d' % id(dummy) in resp, resp)
                self.get('/objects/%d' % id(dummy), status=200)

        self.get('/traceback/gabelstapler', status=500)
        body = self.get('/traceback/12345', status=200)
        self.assertTrue("Cannot retrieve stacktrace for thread 12345" in body, body)

    def test_garbage(self):
        """Test if reference cycles can be viewed."""
        start_debug_garbage()
        try:
            body = self.get('/garbage', status=200)
            #self.assertTrue('0 reference cycles' in body, body)
            cycle = ['spam', 'eggs']
            cycle.append(cycle)
            del cycle
            body = self.get('/garbage', status=200)
            #self.assertTrue('0 reference cycles' in body, body)
            body = self.get('/refresh', status=303)
            body = self.get('/garbage', status=200)
            #self.assertTrue('1 reference cycle' in body, body)
            self.assertTrue('/garbage/0' in body)
            body = self.get('/garbage/0', status=200)
            self.assertTrue('/garbage/graph/0' in body, body)
            self.assertTrue('/garbage/graph/0?reduce=' in body, body)
            body = self.get('/garbage/graph/0', status=200)
            body = self.get('/garbage/graph/0?reduce=on', status=200)
        finally:
            end_debug_garbage()

    def test_tracker(self):
        resp = self.get('/tracker', status=200)
        clsname = '%s.Trash' % (Trash.__module__)
        self.assertTrue(clsname in resp, resp)
        resp = self.get('/tracker/class/%s' % clsname, status=200)
        self.assertTrue('1 instance' in resp, resp)

    def test_start_in_background(self):
        """Test server can be started in background mode."""
        tracker = ClassTracker()
        thread = start_in_background(port=64546, stats=tracker.stats)
        self.assertEqual(thread.daemon, True)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [WebGuiTest]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
