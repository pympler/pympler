import unittest

from pympler.util.compat import HTMLParser, HTTPConnection
from pympler.util.compat import Request, urlopen, URLError
from socket import error as socket_error
from threading import Thread
from time import sleep

from pympler.gui.web import show

# TODO Find a way to stop server (maybe start in another process).
_server = None

class Server(Thread):
    def __init__(self):
        super(Server, self).__init__()
        self.daemon = True

    def run(self):
        show(quiet=True)


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
            conn = HTTPConnection(WebGuiTest.defaulthost)
            conn.request("GET", link)
            response = conn.getresponse()
            response.read()
            conn.close()
            if response.status not in [200, 307]:
                print ('LINK-ERROR:', link, response.status, response.reason)
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
                    urlopen(WebGuiTest.defaulturl)
                    running = True
                except (URLError, socket_error, IOError):
                    wait -= 1
                    sleep(1)


    def test_overview(self):
        """Test availability of web gui."""

        req = Request(self.defaulturl)
        page = str(urlopen(req).read())
        self.assert_("Process overview" in page)


    def test_links(self):
        """Test all linked pages are available."""

        req = Request(self.defaulturl)
        page = str(urlopen(req).read())
        parser = self.LinkChecker()
        parser.feed(page)
        parser.close()
        self.assertEqual(parser.errors, 0)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [WebGuiTest,]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
