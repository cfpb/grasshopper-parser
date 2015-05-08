from flask import json
from nose.tools import assert_equals, assert_true
import app

class TestUnit(object):

    def setup(self):
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

    def test_status(self):
        # Setup
        from datetime import datetime
        import platform
        import pytz

        host = platform.node()
        status = 'OK'
        time = datetime.now(pytz.utc).isoformat()
        up_since = app.UP_SINCE

        # Test
        rv = self.app.get('/status')
        data = json.loads(rv.data)
        assert_equals(data['status'], status)
        assert_equals(data['host'], host)
        assert_equals(data['upSince'], up_since)
        assert_true(data['time'] > time)
        assert_true(data['time'] > data['upSince'])
