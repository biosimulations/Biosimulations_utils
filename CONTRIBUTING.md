# Contributing to BioSimulations-utils

We enthusiastically welcome contributions to BioSimulations-utils!

## Coordinating contributions

Before getting started, please contact the lead developers at [info@biosimulations.org](mailto:info@biosimulations.org) to coordinate your planned contributions with other ongoing efforts. Please also use GitHub issues to announce your plans to the community so that other developers can provide input into your plans and coordinate their own work. As the development community grows, we will institute additional infrastructure as needed such as a leadership committee and regular online meetings.

## Repository organization

This repository follows standard Python conventions:

* `README.md`: Overview of this repository
* `biosimulations_utils/`: Source code for this package
* `tests/`: Unit tests for this package
* `setup.py`: pip installation script for this package
* `setup.cfg`: Configuration for the pip installation script
* `requirements.txt`: Dependencies of this package
* `requirements.optional.txt`: Optional dependencies of this package
* `MANIFEST.in`: List of files to include when BioSimulations-utils is packaged for distribution through PyPI
* `LICENSE`: License for this package
* `CONTRIBUTING.md`: Guide to contributing to this package (this document)
* `CODE_OF_CONDUCT.md`: Code of conduct for developers of this package

## Coding convention

This repository follows standard Python style conventions:

* Class names: `UpperCamelCase`
* Function names: `lower_snake_case`
* Variable names: `lower_snake_case`

## Documentation convention

`BioSimulation-utils` is documented using [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html) and the [napoleon Sphinx plugin](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html). The documentation can be compiled with [Sphinx](https://www.sphinx-doc.org/) by running `sphinx-build docs-src docs`.

## Submitting changes

Please use GitHub pull requests to submit changes. Each request should include a brief description of the new and/or modified features.

## Releasing new versions

Contact [info@biosimulations.org](mailto:info@biosimulations.org) to request release of new changes. 

## Reporting issues

Please use [GitHub issues](https://github.com/biosimulations/Biosimulations_utils/issues) to report any issues to the development community.

## Getting help

Please use [GitHub issues](https://github.com/biosimulations/Biosimulations_utils/issues) to post questions or contact the lead developers at [info@biosimulations.org](mailto:info@biosimulations.org).
