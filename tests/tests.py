"""
Unit and integration tests for grasshopper-parser
"""
import app
from flask import json
from nose.tools import assert_equals, assert_false, assert_raises, assert_true
import yaml

# Hack to get nose asserts to give diff against large lists
assert_equals.__self__.maxDiff = None


class TestUSAddressParser(object):

    def setup(self):
        with open("rules.yaml", 'r') as f:
            self.yaml_rules = yaml.safe_load(f)

    def test_init_default(self):
        """
        PARSER: init - default
        """
        # Setup
        cut = app.USAddressParser()

        # Test
        assert_equals(cut.rules, self.yaml_rules)
        assert_equals(cut.parse_function.__name__, 'parse_with_usaddress_tag')

    def test_init_with_parse_method(self):
        """
        PARSER: init - with valid parse_method
        """
        # Setup
        parser = app.USAddressParser(parse_method='parse')

        # Test
        assert_equals(parser.rules, self.yaml_rules)
        assert_equals(parser.parse_function.__name__, 'parse_with_usaddress_parse')

    def test_init_with_parse_method_invalid(self):
        """
        PARSER: init - with invalid parse_method
        """
        # Setup
        parse_method = 'bad'

        # Test
        with assert_raises(ValueError) as context:
            app.USAddressParser(parse_method=parse_method)

        err_msg = context.exception.message
        assert_equals(err_msg, "Parse method '{}' not supported.".format(parse_method))

    def test_init_with_rules_valid(self):
        """
        PARSER: init - with valid rules
        """
        # Setup
        rules = {
            'address_parts': {
                'standard': {},
                'derived': {}
            },
            'profiles': {}
        }

        # Test
        parser = app.USAddressParser(rules=rules)
        parser.rules = rules

    def test_parse_with_usaddress_parse(self):
        """
        PARSER: usaddress `parse` function
        """
        # Setup
        addr_str = '1234 Main St., Sacramento CA 95818'
        expected = [
            {'code': 'address_number', 'value': u'1234'},
            {'code': 'street_name', 'value': u'Main'},
            {'code': 'street_name_post_type', 'value': u'St.,'},
            {'code': 'city_name', 'value': u'Sacramento'},
            {'code': 'state_name', 'value': u'CA'},
            {'code': 'zip_code', 'value': u'95818'}
        ]
        cut = app.USAddressParser()

        # Test
        actual = cut.parse_with_usaddress_parse(addr_str)
        assert_equals(actual, expected)

    def test_parse_with_usaddress_tag(self):
        """
        PARSER: usaddress `tag` function
        """
        # Setup
        addr_str = '1234 Main St., Sacramento CA 95818'
        expected = [
            {'code': 'address_number', 'value': u'1234'},
            {'code': 'street_name', 'value': u'Main'},
            {'code': 'street_name_post_type', 'value': u'St.'},  # Strips comma
            {'code': 'city_name', 'value': u'Sacramento'},
            {'code': 'state_name', 'value': u'CA'},
            {'code': 'zip_code', 'value': u'95818'}
        ]
        cut = app.USAddressParser()

        # Test
        actual = cut.parse_with_usaddress_tag(addr_str)
        assert_equals(actual, expected)


class TestAPI(object):

    def setup(self):
        app.MAX_BATCH_SIZE = 3
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

    def test_status(self):
        """
        API: GET / -> 200 with service status
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
        API: GET /explode -> 500 on internal error
        """
        # Test
        rv = self.app.get('/explode')
        data = json.loads(rv.data)

        assert_equals(500, rv.status_code)
        assert_equals(500, data['statusCode'])
        assert_equals("Internal server error", data['error'])

    def test_resource_not_found(self):
        """
        API: GET /bad-resource -> 404 on resource not found
        """
        # Setup
        url = '/bad-resource'

        # Test
        rv = self.app.get(url)
        data = json.loads(rv.data)

        assert_equals(404, rv.status_code)
        assert_equals(404, data['statusCode'])
        assert_equals("Resource not found", data['error'])

    def test_parse_success(self):
        """
        API: GET /parse -> 200 with just address
        """
        # Setup
        addr_str = '1600 Pennsylvania Ave NW Washington DC 20006'
        expected = {
            'input': addr_str,
            'parts': [
                {'code': 'address_number', 'value': '1600'},
                {'code': 'street_name', 'value': 'Pennsylvania'},
                {'code': 'street_name_post_type', 'value': 'Ave'},
                {'code': 'street_name_post_directional', 'value': 'NW'},
                {'code': 'city_name', 'value': 'Washington'},
                {'code': 'state_name', 'value': 'DC'},
                {'code': 'zip_code', 'value': '20006'}
            ]}

        # Test
        rv = self.app.get('/parse?address={}'.format(addr_str))
        actual = json.loads(rv.data)
        status_code = rv.status_code

        assert_equals(200, status_code)
        assert_equals(expected, actual)

    def test_parse_with_profile_success(self):
        """
        API: GET /parse -> 200 with address and profile
        """
        # Setup
        profile = 'grasshopper'
        addr_str = '1600 Pennsylvania Ave NW Washington DC 20006'
        expected = {
            'input': addr_str,
            'parts': [
                {'code': 'address_number', 'value': '1600'},
                {'code': 'street_name', 'value': 'Pennsylvania'},
                {'code': 'street_name_post_type', 'value': 'Ave'},
                {'code': 'street_name_post_directional', 'value': 'NW'},
                {'code': 'city_name', 'value': 'Washington'},
                {'code': 'state_name', 'value': 'DC'},
                {'code': 'zip_code', 'value': '20006'},
                {'code': 'address_number_full', 'value': '1600'},
                {'code': 'street_name_full', 'value': 'Pennsylvania Ave NW'}
            ]}

        # Test
        rv = self.app.get('/parse?address={}&profile={}'.format(addr_str, profile))
        actual = json.loads(rv.data)
        status_code = rv.status_code

        assert_equals(200, status_code)
        assert_equals(expected, actual)

    def test_parse_with_invalid_profile(self):
        """
        API: GET /parse -> 400 with invalid profile
        """
        # Setup
        profile = 'bad'
        expected = {
            'statusCode': 400,
            'error': "Parsing profile '{}' not supported".format(profile)
        }
        addr_str = '1600 Pennsylvania Ave NW Washington DC 20006'

        # Test
        rv = self.app.get('/parse?address={}&profile={}'.format(addr_str, profile))
        actual = json.loads(rv.data)
        status_code = rv.status_code

        assert_equals(400, status_code)
        assert_equals(expected, actual)

    def test_parse_fail_no_address(self):
        """
        API: GET /parse -> 400 with 'address' param is not present
        """
        # Test
        rv = self.app.get('/parse?method=tag')
        data = json.loads(rv.data)

        assert_equals(400, rv.status_code)
        assert_equals(400, data['statusCode'])

        assert_equals("'address' query param is required.", data['error'])

    def test_parse_fail_with_repeated_label_error(self):
        """
        API: GET /parse -> 400 with 'method=tag' and address that raises RepeatedLabelError
        """
        # Setup
        address = '1234 Main St. 1234 Main St., Sacramento, CA 95818'

        # Test
        rv = self.app.get('/parse?address={}'.format(address))
        data = json.loads(rv.data)

        assert_equals(400, rv.status_code)
        assert_equals(400, data['statusCode'])
        assert_equals("Could not parse address '{}' with 'tag' method".format(address), data['error'])

    def test_parse_batch_success(self):
        """
        API: POST /parse -> 200 with just "addresses"
        """
        # Setup
        req_data = {
            'addresses': [
                '1600 Pennsylvania Ave NW Washington DC 20006',
                '1234 Main St., Somewheresville, CA 91234'
            ]
        }
        req_json = json.dumps(req_data)

        # Test
        resp = self.app.post('/parse', data=req_json)
        resp_data = json.loads(resp.data)

        assert_equals(200, resp.status_code)
        assert_false(resp_data['failed'])
        assert_equals(len(req_data['addresses']), len(resp_data['parsed']))
        assert_equals(len(resp_data['parsed'][0]['parts']), 7)

    def test_parse_batch_with_failed_parse(self):
        """
        API: POST /parse -> 200 with good and bad address strings
        """
        # Setup
        req_data = {
            'addresses': [
                '1600 Pennsylvania Ave NW Washington DC 20006',
                '5 Arapahoe Plaza El Paso TX 88530'
            ]
        }
        req_json = json.dumps(req_data)

        # Test
        resp = self.app.post('/parse', data=req_json)
        resp_data = json.loads(resp.data)

        assert_equals(200, resp.status_code)
        assert_equals(resp_data['failed'][0], '5 Arapahoe Plaza El Paso TX 88530')
        assert_equals(resp_data['parsed'][0]['input'], '1600 Pennsylvania Ave NW Washington DC 20006')

    def test_parse_batch_with_no_addresses(self):
        """
        API: POST /parse -> 400 with no 'addresses' array
        """
        # Setup
        req_json = json.dumps({})

        # Test
        resp = self.app.post('/parse', data=req_json)
        resp_data = json.loads(resp.data)

        assert_equals(400, resp.status_code)
        assert_equals(400, resp_data['statusCode'])
        assert_equals("'addresses' array not populated", resp_data['error'])

    def test_parse_batch_with_too_many_addresses(self):
        """
        API: POST /parse -> 400 with 'addresses' array too big
        """
        # Setup
        req_data = {
            'addresses': [
                'address1',
                'address2',
                'address3',
                'address4'
            ]
        }
        req_json = json.dumps(req_data)

        # Test
        resp = self.app.post('/parse', data=req_json)
        resp_data = json.loads(resp.data)

        assert_equals(400, resp.status_code)
        assert_equals(400, resp_data['statusCode'])
        assert_equals("'addresses' contained 4 elements, exceeding max of 3", resp_data['error'])
