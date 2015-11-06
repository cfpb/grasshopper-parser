"""
Unit and integration tests for grasshopper-parser
"""
import app
from flask import json
from nose.tools import assert_equals, assert_true


class TestIntegration(object):

    def setup(self):
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

    def test_status(self):
        """
        / - simple request
        """
        # Setup
        from datetime import datetime
        import platform
        import pytz

        host = platform.node()
        service = 'grasshopper-parser'
        status = 'OK'
        time = datetime.now(pytz.utc).isoformat()
        up_since = app.UP_SINCE

        # Test
        rv = self.app.get('/')
        data = json.loads(rv.data)

        assert_equals(data['service'], service)
        assert_equals(data['status'], status)
        assert_equals(data['host'], host)
        assert_equals(data['upSince'], up_since)
        assert_true(data['time'] > time)
        assert_true(data['time'] > data['upSince'])

    @app.app.route('/explode', methods=['GET'])
    def explode():
        """
        Simulates an internal (uncaught) error
        """
        raise ValueError("Hey!  Don't do that!")

    def test_internal_error(self):
        """
        /explode - 500 on internal error
        """
        # Test
        rv = self.app.get('/explode')
        data = json.loads(rv.data)

        assert_equals(500, rv.status_code)
        assert_equals(500, data['statusCode'])
        assert_equals("Hey!  Don't do that!", data['error'])

    def test_parse_success(self):
        """
        /parse - 200 with just address, and parses correctly
        """
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
        status_code = rv.status_code

        assert_equals(200, status_code)

        assert_equals(data['input'], address)

        parts = data['parts']

        # WARN: These asserts have the potential to fail if we retrain the parser
        assert_equals(parts[0]['type'], 'AddressNumber')
        assert_equals(parts[0]['value'], addr_number)
        assert_equals(parts[1]['type'], 'StreetName')
        assert_equals(parts[1]['value'], street_name)
        assert_equals(parts[2]['type'], 'StreetNamePostType')
        assert_equals(parts[2]['value'], street_type)
        assert_equals(parts[3]['type'], 'StreetNamePostDirectional')
        assert_equals(parts[3]['value'], street_direction)
        assert_equals(parts[4]['type'], 'PlaceName')        
        assert_equals(parts[4]['value'], city)
        assert_equals(parts[5]['type'], 'StateName')
        assert_equals(parts[5]['value'], state)
        assert_equals(parts[6]['type'], 'ZipCode')
        assert_equals(parts[6]['value'], zip)

    def test_parse_fail_no_address(self):
        """
        /parse - 400 with 'address' param is not present
        """
        # Test
        rv = self.app.get('/parse?method=tag')
        data = json.loads(rv.data)

        assert_equals(400, rv.status_code)
        assert_equals(400, data['statusCode'])

        assert_equals("'address' query param is required.", data['error'])

    def test_parse_with_method_tag(self):
        """
        /parse - 200 with 'method=tag'
        """
        # Setup
        address = '1600 Pennsylvania Ave NW Washington DC 20006'

        # Test
        rv = self.app.get('/parse?address={}&method=tag'.format(address))
        assert_equals(200, rv.status_code)

    def test_parse_with_method_tag_fail_repeated_label_error(self):
        """
        /parse - 400 with 'method=tag' and address that raises RepeatedLabelError
        """
        # Setup
        address = '1234 Main St. 1234 Main St., Sacramento, CA 95818'

        # Test
        rv = self.app.get('/parse?address={}&method=tag'.format(address))
        data = json.loads(rv.data)

        assert_equals(400, rv.status_code)
        assert_equals(400, data['statusCode'])
        assert_equals("Could not parse address '{}' with 'tag' method".format(address), data['error'])

    def test_parse_with_method_parse(self):
        """
        /parse - 200 with 'method=parse'
        """
        # Setup
        address = '1600 Pennsylvania Ave NW Washington DC 20006'

        # Test
        rv = self.app.get('/parse?address={}&method=parse'.format(address))
        assert_equals(200, rv.status_code)

    def test_parse_with_method_invalid(self):
        """
        /parse - 400 with invalid 'method' param value
        """
        # Setup
        address = '1600 Pennsylvania Ave NW Washington DC 20006'
        bad_method = 'bad'

        # Test
        rv = self.app.get('/parse?address={}&method={}'.format(address, bad_method))
        data = json.loads(rv.data)

        assert_equals(400, rv.status_code)
        assert_equals(400, data['statusCode'])
        assert_equals("Parsing method '{}' not supported.".format(bad_method), data['error'])


