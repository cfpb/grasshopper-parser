"""
Flask-based REST API for parsing address string into its component parts
"""
from datetime import datetime
from flask import Flask, jsonify, request
import platform
import pytz
import usaddress

# Parsed addresses MUST have these part types to be "valid"
# See: http://usaddress.readthedocs.org/en/latest/#details
REQ_ADDR_PARTS = set([
    'AddressNumber',
    'PlaceName',
    'StateName',
    'ZipCode',
])

# Parsed addresses must NOT have these part types to be "valid"
INVALID_ADDR_PARTS = set([
    'USPSBoxGroupID',
    'USPSBoxGroupType',
    'USPSBoxID',
    'USPSBoxType',
])

UP_SINCE = datetime.now(pytz.utc).isoformat()


def parse_with_parse(addr_str):
    """
    Translates an address string using usaddress's `parse()` function

    See: http://usaddress.readthedocs.org/en/latest/#usage
    """
    # usaddress parses free-text address into an array of tuples...why, I don't know.
    parsed = usaddress.parse(addr_str)

    # Converted tuple array to dict
    addr_parts = {addr_part[1]: addr_part[0] for addr_part in parsed}

    return addr_parts


def parse_with_tag(addr_str):
    """
    Translates an address string using usaddress's `tag()` function

    See: http://usaddress.readthedocs.org/en/latest/#usage
    """
    try:
        # FIXME: Consider using `tag()`'s address type for validation?
        # `tag` returns OrderedDict, ordered by address parts in original address string
        addr_parts = usaddress.tag(addr_str)[0]
    except usaddress.RepeatedLabelError:
        # FIXME: Add richer logging here with contents of `rle`
        raise InvalidApiUsage("Could not parse address '{}' with 'tag' method".format(addr_str))

    return addr_parts


def validate_parse_results(addr_parts, req_addr_parts=REQ_ADDR_PARTS, invalid_addr_parts=INVALID_ADDR_PARTS):
    """
    Validates address parts list has all required part types, and no invalid types.
    """
    parsed_types = set(addr_parts.keys())

    invalid = parsed_types & invalid_addr_parts

    if invalid:
        raise InvalidApiUsage('Parsed address includes invalid address part(s): {}'.format(list(invalid)))

    missing = req_addr_parts - parsed_types

    if missing:
        raise InvalidApiUsage('Parsed address does not include required address part(s): {}'.format(list(missing)))


# Maps `method` param to corresponding parse function
parse_method_dispatch = {'parse': parse_with_parse, 'tag': parse_with_tag}


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


app = Flask(__name__)


@app.route('/status', methods=['GET'])
def status():
    """
    Provides the current status of the address parsing service
    """

    status = {
        "status": "OK",
        "time": datetime.now(pytz.utc).isoformat(),
        "host": platform.node(),
        "upSince": UP_SINCE,
    }

    return jsonify(status)


@app.route('/parse', methods=['GET'])
def parse():
    """
    Parses an address string into its component parts
    """

    req_data = request.args

    try:
        addr_str = req_data['address']
    except KeyError:
        raise InvalidApiUsage("'address' not present in request.")

    method = req_data.get('method', 'parse')

    # FIXME: Make this smarter.  Works as expected for JSON, but not GET param
    #        May want to use Flask-RESTful, which has richer param parsing
    validate = req_data.get('validate', False)

    try:
        addr_parts = parse_method_dispatch[method](addr_str)
    except KeyError:
        raise InvalidApiUsage("Parsing method '{}' not supported.".format(method))

    if validate:
        validate_parse_results(addr_parts)

    response = {
        'input': addr_str,
        'parts': addr_parts
    }

    return jsonify(response)


def gen_error_json(message, code):
    return jsonify({'error': message, 'statusCode': code}), code


@app.errorhandler(InvalidApiUsage)
def usage_error(error):
    return gen_error_json(error.message, error.status_code)


@app.errorhandler(404)
def not_found_error(error):
    return gen_error_json('Resource not found', 404)


@app.errorhandler(Exception)
def default_error(error):
    # FIXME: This should be scrubbed
    return gen_error_json(str(error), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
