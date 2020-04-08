""" Manual corrections to BioModels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-05
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.import_resources import biomodels
_DRY_RUN = True


def run():
    importer = biomodels.BioModelsImporter(_dry_run=_DRY_RUN)
    importer.run()


if __name__ == "__main__":
    run()
