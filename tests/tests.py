from flask import json
from nose.tools import assert_equals, assert_true
import app

class TestIntegration(object):

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


    def test_parse_success(self):
        # Setup
        addr_number = '1600'
        street_name = 'Pennsylvania'
        street_type = 'Ave'
        street_direction = 'NW'
        city = 'Washington'
        state = 'DC'
        zip = '20006'
        address = '1600 Pennsylvania Ave NW Washington DC 20006'

        # Test
        rv = self.app.get('/parse?address={}'.format(address))
        data = json.loads(rv.data)

        assert_equals(data['input'], address)
        
        parts = data['parts']

        assert_equals(parts['AddressNumber'], addr_number)
        assert_equals(parts['PlaceName'], city)
        assert_equals(parts['StateName'], state)
        assert_equals(parts['StreetName'], street_name)
        assert_equals(parts['StreetNamePostDirectional'], street_direction)
        assert_equals(parts['StreetNamePostType'], street_type)
        assert_equals(parts['ZipCode'], zip)

        from pprint import pprint
        pprint(data)


    def test_parse_fail_invalid_param(self):
        pass


    def test_parse_with_method_tag(self):
        pass


    def test_parse_with_method_parse(self):
        pass


    def test_parse_with_method_invalid(self):
        pass


    def test_parse_with_validate_success(self):
        pass


    def test_parse_with_validate_fail_incomplete(self):
        pass


    def test_parse_with_validate_fail_invalid_parts(self):
        pass
