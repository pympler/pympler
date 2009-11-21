import unittest

from urllib2 import Request, urlopen, URLError

from threading import Thread

from HTMLParser import HTMLParser

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


    defaulthost = 'http://localhost:8090'

    class LinkChecker(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.errors = 0

        def follow(self, link):
            address = WebGuiTest.defaulthost + link
            try:
                urlopen(address)
            except URLError, err:
                print ('%s: %s' % (address, err))
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


    def test_overview(self):
        """Test availability of web gui."""

        req = Request(self.defaulthost)
        page = urlopen(req).read()
        self.assert_("Process overview" in page)


    def test_links(self):
        """Test all linked pages are available."""

        req = Request(self.defaulthost)
        page = urlopen(req).read()
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
