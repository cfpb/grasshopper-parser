# Grasshopper Address Parser

[![Build Status](https://travis-ci.org/cfpb/grasshopper-parser.svg)](https://travis-ci.org/cfpb/grasshopper-parser) 
[![Coverage Status](https://coveralls.io/repos/cfpb/grasshopper-parser/badge.svg?branch=master)](https://coveralls.io/r/cfpb/grasshopper-parser?branch=master)

Simple microservice for parsing US address strings into their component parts.  This project
is used by the [Grasshopper](https://github.com/cfpb/grasshopper) geocoding service, but can
also be used for general-purpose address parsing.

## Requirements

* [Flask](http://flask.pocoo.org/) - Python HTTP microframework
* [US Address parsing library](https://github.com/datamade/usaddress) - Python
    library for parsing US addresses using natural language processing (NLP) methods.

## Build and Deploy

grasshopper-parser is a standard Python app with few dependencies, making it
quite simple to build and launch.

### Locally

1. Build it.

        pip install -r requirements.txt

1. Run it.
    * [Flask Dev Server](http://flask.pocoo.org/docs/0.10/server/)


            python app.py

    * ...or [Gunicorn](http://gunicorn.org/)


            gunicorn -c conf/gunicorn.py -b localhost:5000 app:app

### Docker

The service can also be run as a [Docker](https://docs.docker.com/) container.  See the
[`Dockerfile`](https://github.com/cfpb/grasshopper-parser/blob/master/Dockerfile) for details on the Docker image.

1. Build it.

        docker build --rm --tag=hmda/grasshopper-parser .

1. Run it.

        docker run -ti -p 5000:5000 hmda/grasshopper-parser

## Configuration

Much of the parser's logic is maintained within [`rules.yaml`](https://github.com/cfpb/grasshopper-parser/blob/master/rules.yaml).
This file is read once at startup.  If you wish to make changes, you will need to restart the API for
the changes to take affect.

`rules.yaml` is composed of the following sections:

1. **`address_parts`:** Maps all address parts to their underlying data source.

    1. **`standard`:** Maps [`usaddress`'s "components"](http://usaddress.readthedocs.org/en/latest/#details) to the 
        parser's address "parts".  This is currently a one-to-one mapping, but may diverge from usaddress
        in the future.  These are the default set of "parts" returned if no "profile" is given.

    1. **`derived`:** Adds additional composite parts, made by joining multiple "parts" from the `standard` mapping.
        These "parts" are only available when mapped to a given "profile".

1. **`profiles`:** Provides additional address part processing, such as returning "derived" address parts, and validating
    that a given address string can be parsed into the minimum "required" parts.

## API Usage

The following resources are available.  All examples assume running on `localhost`, port `5000`.

### `/` (root resource)

Displays the current state of the API.

##### Request

    GET http://localhost:5000/

##### Response

```json
{
    "host": "yourhost.local",
    "service": "grasshopper-parser",
    "status": "OK",
    "time": "2015-05-06T19:14:19.304850+00:00",
    "upSince": "2015-05-06T19:08:26.568966+00:00"
}
```

### `/parse`

The `/parse` resource is the heart the API.  It parses free-text address
strings into their component parts.  It supports `GET` requests for individual with the following query parameters:

* **`address`:** Free-text address string to be parsed.

* **`profile`:** Additional parsing logic based on pre-defined "profiles"

    The "grasshopper" profile is included by default.  It is geared towards the 
    [grasshopper](https://github.com/cfpb/grasshopper) geocoder's parsing requirement.
    Additional profiles can be added in [`rules.yaml`](https://github.com/cfpb/grasshopper-parser/blob/master/rules.yaml).

#### Single address

##### Request

    GET http://localhost:5000/parse?address=1600+Pennsylvania+Ave+NW+Washington+DC+20006

##### Response

The `input` value will always be the address string provided in the request.

```json
{
  "input": "1600 Pennsylvania Ave NW Washington DC 20006",
  "parts": [
    { "code": "address_number", "value": "1600" }, 
    { "code": "street_name", "value": "Pennsylvania" }, 
    { "code": "street_name_post_type", "value": "Ave" }, 
    { "code": "street_name_post_directional", "value": "NW" }, 
    { "code": "city_name", "value": "Washington" }, 
    { "code": "state_name", "value": "DC" }, 
    { "code": "zip_code", "value": "20006" }
  ]
}
```

#### Single address with optional `profile`

##### Request

    GET http://localhost:5000/parse?address=1600+Pennsylvania+Ave+NW+Washington+DC+20006?profile=grasshopper

##### Response

Notice there are two additional "derived" parts at the end of the list.

```json
{
  "input": "1600 Pennsylvania Ave NW Washington DC 20006",
  "parts": [
    { "code": "address_number", "value": "1600" }, 
    { "code": "street_name", "value": "Pennsylvania" }, 
    { "code": "street_name_post_type", "value": "Ave" }, 
    { "code": "street_name_post_directional", "value": "NW" }, 
    { "code": "city_name", "value": "Washington" }, 
    { "code": "state_name", "value": "DC" }, 
    { "code": "zip_code", "value": "20006" }, 
    { "code": "address_number_full", "value": "1600" }, 
    { "code": "street_name_full", "value": "Pennsylvania Ave NW" }
  ]
}
```

#### Single _incomplete_ address with `profile`

##### Request

    GET http://localhost:5000/parse?address=1234+main+st&profile=grasshopper

##### Response

This is considered an error, and returned with a `400` HTTP status.

```json
{
  "error": "Could not parse out required address parts: ['state_name', 'zip_code']",
  "statusCode": 400
}
```

#### Batch address parsing

Batch parsing of up to 5000 addresses is also supported via HTTP POST.  The format is
very similar to the URL structure using in parsing individual addresses.

##### Request

The following example contains a batch of 3 address strings, 2 good, 1 incomplete.

    POST -H 'Content-Type: application/json' http://localhost:5000/parse

```json
{
  "profile": "grasshopper", 
  "addresses": [
    "1600 Pennsylvania Ave NW Washington DC 20006", 
    "1315 10th St Sacramento CA 95814", 
    "1234 Main St"
  ]
}
```

##### Response

```json
{
  "failed": [
    "1234 Main St"
  ],
  "parsed": [
    {
      "input": "1600 Pennsylvania Ave NW Washington DC 20006",
      "parts": [
        { "code": "address_number", "value": "1600" },
        { "code": "street_name", "value": "Pennsylvania" },
        { "code": "street_name_post_type", "value": "Ave" },
        { "code": "street_name_post_directional", "value": "NW" },
        { "code": "city_name", "value": "Washington" },
        { "code": "state_name", "value": "DC" },
        { "code": "zip_code", "value": "20006" },
        { "code": "address_number_full", "value": "1600" },
        { "code": "street_name_full", "value": "Pennsylvania Ave NW" }
      ]
    },
    {
      "input": "1315 10th St Sacramento CA 95814",
      "parts": [
        { "code": "address_number", "value": "1315" },
        { "code": "street_name", "value": "10th" },
        { "code": "street_name_post_type", "value": "St" },
        { "code": "city_name", "value": "Sacramento" },
        { "code": "state_name", "value": "CA" },
        { "code": "zip_code", "value": "95814" },
        { "code": "address_number_full", "value": "1315" },
        { "code": "street_name_full", "value": "10th St" }
      ]
    }
  ]
}
```

## Testing

This project uses the [Flask Testing](http://flask.pocoo.org/docs/0.10/testing/) tools, which really uses a
[Werkzeug Test Client](http://werkzeug.pocoo.org/docs/0.10/test/#werkzeug.test.Client) under
the hood.  In addition, we're using
[nose](https://nose.readthedocs.org/en/latest/) as the unittesting framework,
[coverage](http://nedbatchelder.com/code/coverage/) for test coverage,
[flake8](http://flake8.readthedocs.org/en/latest/index.html) for code quality,
and [tox](https://tox.readthedocs.org/en/latest/) to glue it all together.


### Prerequisite

In order to use these tools, you will first need to install:

    pip install -r tests/requirements.txt

### Unit Testing

All unit tests are in the [`tests`]() directory.  To run them:

    $ nosetests -vs

...which should get you something similar to:

    /explode - 500 on internal error ... ok
    /parse - 400 with 'address' param is not present ... ok
    /parse - 200 with just address, and parses correctly ... ok
    ...
    /status - simple request ... ok

    ----------------------------------------------------------------------
    Ran 11 tests in 0.089s

### Test Coverage

If you'd like to include test coverage with your tests:

    nosetests -vs --with-coverage --cover-package=app

...resulting in a report like:

    Name    Stmts   Miss  Cover   Missing
    -------------------------------------
    app        67      2    97%   96, 127
    ----------------------------------------------------------------------
    Ran 11 tests in 0.115s


### Code Quality

[flake8](https://flake8.readthedocs.org/en/2.4.0/#) is a wrapper code quality tools 
[pep8](http://pep8.readthedocs.org/en/latest/), 
[pyflakes](https://github.com/pyflakes/pyflakes/), and 
[mccabe](https://github.com/flintwork/mccabe). To run `flake8`:

    flake8
 
To adjust the `flake8` settings, edit the `[flake8]` section of `tox.ini`.

    [flake8]
    exclude = .git,.tox
    format = pylint
    max-line-length = 160
    max-complexity = 10
    show-source = 1

### Do-it-all

To execute all of the above mentioned tools in one fell swoop, and simulate the
full test suite executed by our [Travis CI cfpb/grasshopper-parser](https://travis-ci.org/cfpb/grasshopper-parser),
you can also use `tox`:

    tox

All `tox` settings can be found in `tox.ini`.


## Getting involved

For details on how to get involved, please first read out [CONTRIBUTING](CONTRIBUTING.md) guidelines.


## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)
