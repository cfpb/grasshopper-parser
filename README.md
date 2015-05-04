# Grasshopper Parser

US Address parser for the [Grasshopper](https://github.com/cfpb/grasshopper) project.
Provides a simple microservice that breaks an address string into its components.

## Installation

This service depends on the [Flask Microframework](http://flask.pocoo.org/) and the [US Address parsing library](https://github.com/datamade/usaddress)
To install these dependencies, run the following from your Python environment:

```
pip install usaddress
pip install flask
```

## Running

The service can be run directly from the root directory by issuing the following command:

`python app.py`


Alternatively, this microservice can be run with Docker:

To build, run `docker build --rm --tag=hmda/grasshopper-parser .`

A container can be started by running `docker run -ti -p 5000:5000 hmda/grasshopper-parser`


## Getting involved

For details on how to get involved, please first read out [CONTRIBUTING](CONTRIBUTING.md) guidelines.


## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)
