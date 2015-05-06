# Grasshopper Parser

US Address parser for the [Grasshopper](https://github.com/cfpb/grasshopper) project.
Provides a simple microservice that breaks an address string into its components.

## Installation

This service depends on the [Flask Microframework](http://flask.pocoo.org/) and the [US Address parsing library](https://github.com/datamade/usaddress)
To install these dependencies, run the following from your Python environment:


    pip install -r requirements.txt 


## Running

The service can be run directly from the root directory by issuing the following command:

    python app/app.py


Alternatively, this microservice can be run with Docker:

To build, run `docker build --rm --tag=hmda/grasshopper-parser .`

A container can be started by running `docker run -ti -p 5000:5000 hmda/grasshopper-parser`

## Usage

The following resources are available.  All examples assume running on
`localhost`, port `5000`.

### `/status`

The `/status` resource simply displays the current state of the API

#### Request

    GET http://localhost:5000/status

#### Response

```json
{
    host: "yourhost.local",
    status: "OK",
    time: "2015-05-06T19:14:19.304850+00:00",
    upSince: "2015-05-06T19:08:26.568966+00:00"
}
```

### `/parse`

The `/parse` resource is the heart of this API.  It parses a free-text address
strings into their component parts.  This service currently uses 

The following options are available via both `HTTP GET` query paramaters or
JSON attributes via `HTTP POST`.

* **`address`:** Free-text address string to be parsed.

* **`method`:** (Optional) [usaddress parsing method](http://usaddress.readthedocs.org/en/latest/#usage)
    to be used to split `address` into its component parts.

    Supported Values:

    * `parse` (Default)
    * `tag`

* **`validate`:** (Optional) Validates whether the `address` string splits into
    either too few parts to be considered complete, or contains parts we do not
    allow (such as P.O. Box addresses).

    Supported Values:

    * `false` (Default)
    * `true`


#### Request

    GET http://localhost:5000/parse\?address\=1311+30th+st+washington+dc+20007


OR

```curl
curl -X POST \
-H "Content-Type: application/json" \
-d '{"address" : "1311 30th st washington dc 20007"}' \
http://localhost:5000/parse
```

#### Response

```json
{
  "input": "1311 30th st washington dc 20007",
  "parts": {
    "AddressNumber": "1311",
    "PlaceName": "washington",
    "StateName": "dc",
    "StreetName": "30th",
    "StreetNamePostType": "st",
    "ZipCode": "20007"
  }
}
```


## Getting involved

For details on how to get involved, please first read out [CONTRIBUTING](CONTRIBUTING.md) guidelines.


## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)
