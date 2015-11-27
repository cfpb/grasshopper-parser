"""
Flask-based REST API for parsing address string into its component parts
"""
from datetime import datetime
from flask import Flask, jsonify, request
import platform
import pytz
import usaddress
import yaml


class AddressParserError(Exception):
    """
    Exception for any failures that occur during address parsing
    """
    pass


class USAddressParser(object):
    """
    Parser for translating address strings into the component parts
    using datamade's usaddress library.

    See: http://usaddress.readthedocs.org
    """

    def __init__(self, rules=None, parse_method='tag'):
        # Maps `method` arg to corresponding parse function

        parse_method_dispatch = {
            'parse': self.parse_with_usaddress_parse,
            'tag': self.parse_with_usaddress_tag
        }

        try:
            self.parse_function = parse_method_dispatch[parse_method]
        except KeyError:
            raise ValueError("Parse method '{}' not supported.".format(parse_method))

        if rules:
            self.rules = rules

            # FIXME: Add real logging
            from pprint import pprint
            print('Using custom parsing rules:')
            pprint(rules)
        else:
            # If rules not passed in on init, read default "rules.yaml" file
            with open("rules.yaml", 'r') as f:
                self.rules = yaml.safe_load(f)

            print('Using default rules from "rules.yaml"')

        # Initialized static mapping dicts
        # FIXME: Need friendlier error messages when "rules" not well-formed
        self.standard_part_mapping = {x['usaddress']: x['id'] for x in self.rules['address_parts']['standard']}
        self.derived_part_mapping = {x['id']: x['parts'] for x in self.rules['address_parts']['derived']}
        self.profile_mapping = {x['id']: x['required'] for x in self.rules['profiles']}

    def parse_with_usaddress_parse(self, addr_str):
        """
        Parses address string using usaddress's `parse()` function
        """
        parsed = usaddress.parse(addr_str)

        addr_parts = [{'code': self.standard_part_mapping[v], 'value': k} for k, v in parsed]

        return addr_parts

    def parse_with_usaddress_tag(self, addr_str):
        """
        Parses address string using usaddress's `tag()` function
        """
        try:
            tagged = usaddress.tag(addr_str)[0].items()
        except usaddress.RepeatedLabelError:
            # FIXME: Add richer logging here with contents of `rle` or chain exception w/ Python 3
            # FIXME: Shouldn't leak details of 'tag' method since it not longer a param
            raise AddressParserError("Could not parse address '{}' with 'tag' method".format(addr_str))

        addr_parts = [{'code': self.standard_part_mapping[k], 'value': v} for k, v in tagged]

        return addr_parts

    def parse(self, addr_str, profile_name=None):
        """
        Parses an address string using usaddress, method  based on `parse_method` init arg
        """
        addr_parts = self.parse_function(addr_str)

        if profile_name:
            addr_parts = self.process_profile(profile_name, addr_parts)

        return addr_parts

    def process_profile(self, profile_name, addr_parts):
        """
        Translates the address parts to profile-specific address parts
        """
        try:
            profile_part_types = self.profile_mapping[profile_name]
        except KeyError:
            raise AddressParserError("Parsing profile '{}' not supported".format(profile_name))

        # Get "derived" address part types from "required"
        derived_part_types = filter(lambda x: x in self.derived_part_mapping, profile_part_types)

        for derived_part_type in derived_part_types:

            # Get all child address parts types for a given "derived" part
            child_part_types = self.derived_part_mapping[derived_part_type]

            # Filter out all child parts not in current address
            filtered_child_parts = filter(lambda x: x['code'] in child_part_types, addr_parts)
            child_part_values = map(lambda x: x['value'], filtered_child_parts)

            # Build a space-separated string of all available child parts
            derived_part_value = " ".join(child_part_values)

            addr_parts.append({'code': derived_part_type, 'value': derived_part_value})

        # Validate all required fields are present
        addr_part_types = map(lambda x: x['code'], addr_parts)
        missing_parts = filter(lambda x: x not in addr_part_types, profile_part_types)

        if missing_parts:
            # FIXME: Should extend AddressParserError with "missing_parts"
            raise AddressParserError("Could not parse out required address parts: {}".format(missing_parts))

        return addr_parts


class InvalidApiUsage(Exception):
    """
    Exception for invalid usage of address parsing API

    This is a simplifiled version of Flask's Implementing API Exceptions:
    See: http://flask.pocoo.org/docs/0.10/patterns/apierrors/
    """
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


# FIXME: Investigate using Flask's built-in configs
UP_SINCE = datetime.now(pytz.utc).isoformat()
HOSTNAME = platform.node()
MAX_BATCH_SIZE = 5000
PARSER = USAddressParser()

app = Flask(__name__)


@app.route('/', methods=['GET'])
def status():
    """
    Provides the current status of the address parsing service
    """

    status = {
        "service": "grasshopper-parser",
        "status": "OK",
        "time": datetime.now(pytz.utc).isoformat(),
        "host": HOSTNAME,
        "upSince": UP_SINCE,
    }

    return jsonify(status)


@app.route('/parse', methods=['GET'])
def parse():
    """
    Parses an address string into its component parts
    """
    params = request.args

    try:
        addr_str = params['address']
    except KeyError:
        raise InvalidApiUsage("'address' query param is required.")

    profile = params.get('profile', None)

    addr_parts = PARSER.parse(addr_str, profile)

    response = {
        'input': addr_str,
        'parts': addr_parts
    }

    return jsonify(response)


@app.route('/parse', methods=['POST'])
def parse_batch():
    """
    Parses a batch of address strings into the component parts
    """
    # FIXME: Remove "force", add explicit Content-Type handling
    body = request.get_json(force=True)

    profile = body.get('profile', None)
    addresses = body.get('addresses', None)

    if not addresses:
        raise InvalidApiUsage("'addresses' array not populated")

    addrs_len = len(addresses)

    if addrs_len > MAX_BATCH_SIZE:
        raise InvalidApiUsage("'addresses' contained {} elements, exceeding max of {}".format(addrs_len, MAX_BATCH_SIZE))

    parsed = []
    failed = []

    for addr_str in addresses:
        try:
            addr_parts = PARSER.parse(addr_str, profile)
        except AddressParserError as ape:
            # FIXME: Python3 chained exceptions would be helpful here.
            app.logger.warn('Could not parse address "{}": {}'.format(addr_str, ape.message))
            failed.append(addr_str)

        parsed.append({
            'input': addr_str,
            'parts': addr_parts
        })

    response = {
        'parsed': parsed,
        'failed': failed
    }

    return jsonify(response)


def gen_error_json(message, code):
    """
    Builds standard JSON error message
    """
    return jsonify({'error': message, 'statusCode': code}), code


# Register all Flask error handlers
@app.errorhandler(404)
def not_found_error(error):
    return gen_error_json('Resource not found', 404)


@app.errorhandler(AddressParserError)
def parser_erro(error):
    return gen_error_json(error.message, 400)


@app.errorhandler(InvalidApiUsage)
def usage_error(error):
    return gen_error_json(error.message, error.status_code)


@app.errorhandler(Exception)
def default_error(error):
    # FIXME: This should be scrubbed
    app.logger.exception('Internal server error')
    return gen_error_json('Internal server error', 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
