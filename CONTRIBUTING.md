# Contributing to the template repository for BioSimulators-compliant simulation tools

We enthusiastically welcome contributions to the template repository.

## Coordinating contributions

Before getting started, please contact the lead developers at [info@biosimulations.org](mailto:info@biosimulations.org) to coordinate your planned contributions with other ongoing efforts. Please also use GitHub issues to announce your plans to the community so that other developers can provide input into your plans and coordinate their own work. As the development community grows, we will institute additional infrastructure as needed such as a leadership committee and regular online meetings.

## Repository organization

This repository follows standard Python conventions:

* `README.md`: Overview of `BioSimulation-utils`
* `Dockerfile`: file for building a Docker image for the simulator
* `my_simulator/`: Source code for the simulator
* `tests/`: Unit tests
* `setup.py`: pip installation script
* `setup.cfg`: Configuration for the pip installation
* `requirements.txt`: Dependencies
* `requirements.optional.txt`: Optional dependencies
* `MANIFEST.in`: List of files to include in package
* `LICENSE`: License
* `CONTRIBUTING.md`: Guide to contributing to `BioSimulation-utils` (this document)
* `CODE_OF_CONDUCT.md`: Code of conduct for developers

## Coding convention

This repository follows standard Python style conventions:

* Class names: `UpperCamelCase`
* Function names: `lower_snake_case`
* Variable names: `lower_snake_case`

## Documentation convention

`BioSimulation-utils` is documented using [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html) and the [napoleon Sphinx plugin](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html). The documentation can be compiled with [Sphinx](https://www.sphinx-doc.org/) by running `sphinx-build docs docs/_build/html`.

## Submitting changes

Please use GitHub pull requests to submit changes. Each request should include a brief description of the new and/or modified features.

## Releasing and deploying new versions

Contact [info@biosimulations.org](mailto:info@biosimulations.org) to request release and deployment of new changes. 

## Reporting issues

Please use [GitHub issues](https://github.com/biosimulations/Biosimulations_utils/issues) to report any issues to the development community.

## Getting help

Please use [GitHub issues](https://github.com/biosimulations/Biosimulations_utils/issues) to post questions or contact the lead developers at [info@biosimulations.org](mailto:info@biosimulations.org).
