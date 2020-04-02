""" Utilities for working with SBML-encoded models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, OntologyTerm, Taxon, Type
from ..utils import pretty_print_units
from .core import ModelReader, ModelIoError
from .data_model import Model, ModelParameter, Variable  # noqa: F401
from PIL import Image
import enum
import ete3
import libsbml
import numpy
import os
import re
import requests

__all__ = ['SbmlModelReader', 'viz_model']


class ModelFramework(enum.Enum):
    flux_balance = OntologyTerm(
        ontology='SBO',
        id='0000624',
        name='flux balance framework',
        description=('Modelling approach, typically used for metabolic models, where the flow '
                     'of metabolites (flux) through a network can be calculated. This approach '
                     'will generally produce a set of solutions (solution space), which may be '
                     'reduced using objective functions and constraints on individual fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000624',
    )

    logical = OntologyTerm(
        ontology='SBO',
        id='0000234',
        name='logical framework',
        description=('Modelling approach, pioneered by Rene Thomas and Stuart Kaufman, where the '
                     'evolution of a system is described by the transitions between discrete activity '
                     'states of "genes" that control each other.'),
        iri='http://biomodels.net/SBO/SBO_0000234',
    )

    non_spatial_continuous = OntologyTerm(
        ontology='SBO',
        id='0000293',
        name='non-spatial continuous framework',
        description=('Modelling approach where the quantities of participants are considered continuous, '
                     'and represented by real values. The associated simulation methods make use of '
                     'differential equations. The models do not take into account the distribution of the '
                     'entities and describe only the temporal fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000293',
    )

    non_spatial_discrete = OntologyTerm(
        ontology='SBO',
        id='0000295',
        name='non-spatial discrete framework',
        description=('Modelling approach where the quantities of participants are considered discrete, '
                     'and represented by integer values. The associated simulation methods can be '
                     'deterministic or stochastic.The models do not take into account the distribution '
                     'of the entities and describe only the temporal fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000295',
    )

    spatial_continuous = OntologyTerm(
        ontology='SBO',
        id='0000292 ',
        name='spatial continuous framework',
        description=('Modelling approach where the quantities of participants are considered continuous, '
                     'and represented by real values. The associated simulation methods make use of '
                     'differential equations. The models take into account the distribution of the '
                     'entities and describe the spatial fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000292 ',
    )

    spatial_discrete = OntologyTerm(
        ontology='SBO',
        id='0000294',
        name='spatial discrete framework',
        description=('Modelling approach where the quantities of participants are considered discrete, '
                     'and represented by integer values. The associated simulation methods can be '
                     'deterministic or stochastic. The models take into account the distribution of '
                     'the entities and describe the spatial fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000294',
    )


class XmlName(object):
    """ Name of an XML node

    Attributes:
        prefix (:obj:`str`): prefix
        name (:obj:`str`): name
    """

    def __init__(self, prefix, name):
        """
        Args:
            prefix (:obj:`str`): prefix
            name (:obj:`str`): name
        """
        self.prefix = prefix
        self.name = name


class SbmlModelReader(ModelReader):
    """ Read information about SBML-encoded models """

    def _read_from_file(self, filename):
        """ Read a SBML-encoded model from a file

        Args:
            filename (:obj:`str`): path to a file which defines an SBML-encoded model

        Returns:
            :obj:`libsbml.Model`: SBML-encoded model
        """
        reader = libsbml.SBMLReader()
        if not os.path.isfile(filename):
            raise ValueError('{} does not exist'.format(filename))
        doc = reader.readSBMLFromFile(filename)
        model_sbml = doc.getModel()
        return model_sbml

    def _read_format(self, model_sbml, model):
        """ Read the metadata of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`Model`): model

        Returns:
            :obj:`Format`: format of the model
        """
        model.format = format = Format(
            name='SBML',
            version='L{}V{}'.format(model_sbml.getLevel(), model_sbml.getVersion()),
            edam_id='format_2585',
            url='http://sbml.org',
        )

        return format

    def _read_metadata(self, model_sbml, model):
        """ Read the metadata of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`Model`): model

        Returns:
            :obj:`Model`: model with additional metadata
        """
        annot_xml = model_sbml.getAnnotation()
        desc_xml = self._get_xml_child_by_names(annot_xml, [
            XmlName('rdf', 'RDF'),
            XmlName('rdf', 'Description'),
        ])

        # modeling framework
        packages = set()
        for i_plugin in range(model_sbml.getNumPlugins()):
            plugin_sbml = model_sbml.getPlugin(i_plugin)
            packages.add(plugin_sbml.getPackageName())

        unsupported_packages = packages.difference(set(['annot', 'fbc', 'groups', 'layout', 'multi', 'qual', 'render', 'req']))
        if unsupported_packages:
            raise ModelIoError("{} package(s) are not supported".format(', '.join(unsupported_packages)))

        framework = ModelFramework.non_spatial_continuous
        model.framework = framework.value

        # taxon
        taxon_xml = self._get_xml_child_by_names(desc_xml, [
            XmlName('bqbiol', 'hasTaxon'),
            XmlName('rdf', 'Bag'),
            XmlName('rdf', 'li'),
        ])
        model.taxon = None
        if taxon_xml:
            taxon_url = self._get_xml_attr_by_name(taxon_xml, XmlName('rdf', 'resource'))
            match = re.match(r'https?://identifiers.org/taxonomy/(\d+)', taxon_url)
            if match:
                taxon_id = int(match.group(1))
                ncbi_taxa = ete3.NCBITaxa()
                taxon_name = ncbi_taxa.get_taxid_translator([taxon_id]).get(taxon_id, None)
                if taxon_name:
                    model.taxon = Taxon(
                        id=taxon_id,
                        name=taxon_name,
                    )

        return model

    def _read_units(self, model_sbml, model):
        """ Read the units of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`Model`): model

        Returns:
            :obj:`dict`: dictionary that maps the ids of units to their definitions
        """
        units = {}
        for unit_def_sbml in model_sbml.getListOfUnitDefinitions():
            units[unit_def_sbml.getId()] = self._format_unit_def(unit_def_sbml.getDerivedUnitDefinition())

        return units

    def _read_parameters(self, model_sbml, model, units):
        """ Read information about the parameters of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`Model`): model
            units (:obj:`dict`): dictionary that maps the ids of units to their definitions

        Returns:
            :obj:`list` of :obj:`ModelParameter`: information about parameters
        """
        parameters = {}

        # global parameters
        for param_sbml in model_sbml.getListOfParameters():
            parameters[param_sbml.getId()] = self._read_parameter(param_sbml, model)

        # local parameters of reactions
        for rxn_sbml in model_sbml.getListOfReactions():
            kin_law_sbml = rxn_sbml.getKineticLaw()
            if kin_law_sbml:
                rxn_id = rxn_sbml.getId()
                rxn_name = rxn_sbml.getName() or None

                for param_sbml in kin_law_sbml.getListOfParameters():
                    assert rxn_id
                    parameters[(rxn_id, param_sbml.getId())] = self._read_parameter(
                        param_sbml, model, rxn_sbml=rxn_sbml, rxn_id=rxn_id, rxn_name=rxn_name)

        # compartment sizes
        for comp_sbml in model_sbml.getListOfCompartments():
            if not comp_sbml.isSetSize():
                continue

            comp_id = comp_sbml.getId()
            assert comp_id
            comp_name = comp_sbml.getName() or comp_id

            value = comp_sbml.getSize()
            parameters[comp_id] = ModelParameter(
                target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                group='Initial compartment sizes',
                id="init_size_{}".format(comp_id),
                name='Initial size of {}'.format(comp_name),
                description=None,
                identifiers=[],
                type=Type.float,
                value=value,
                recommended_range=self._calc_recommended_param_range(value),
                units=self._format_unit_def(comp_sbml.getDerivedUnitDefinition()),
            )

        # initial amounts / concentrations of species
        for species_sbml in model_sbml.getListOfSpecies():
            if not (species_sbml.isSetInitialAmount() or species_sbml.isSetInitialConcentration()):
                continue

            species_id = species_sbml.getId()
            assert species_id

            species_name = species_sbml.getName() or species_id

            species_substance_units = units.get(species_sbml.getSubstanceUnits() or model_sbml.getSubstanceUnits(), None) \
                or species_sbml.getSubstanceUnits() \
                or model_sbml.getSubstanceUnits()
            if species_sbml.isSetInitialAmount():
                species_initial_type = 'Amount'
                species_initial_val = species_sbml.getInitialAmount()
                species_initial_units = species_substance_units
            else:
                species_initial_type = 'Concentration'
                species_initial_val = species_sbml.getInitialConcentration()

                comp_sbml = self._get_compartment(model_sbml, species_sbml.getCompartment())

                if species_substance_units:
                    species_initial_units = pretty_print_units('({}) / ({})'.format(
                        species_substance_units,
                        self._format_unit_def(comp_sbml.getDerivedUnitDefinition())
                    ))
                else:
                    species_initial_units = None

            parameters[species_id] = ModelParameter(
                target='/' + '/'.join([
                    "sbml:sbml",
                    "sbml:model",
                    "sbml:listOfSpecies",
                    "sbml:species[@id='{}']".format(species_id),
                    "@initial{}".format(species_initial_type),
                ]),
                group='Initial species amounts/concentrations',
                id="init_{}_{}".format(species_initial_type.lower(), species_id),
                name='Initial {} of {}'.format(species_initial_type.lower(), species_name),
                description=None,
                identifiers=[],
                type=Type.float,
                value=species_initial_val,
                recommended_range=self._calc_recommended_param_range(species_initial_val),
                units=species_initial_units,
            )

        # fbc package
        plugin_sbml = model_sbml.getPlugin('fbc')
        if plugin_sbml:
            obj_sbml = plugin_sbml.getActiveObjective()
            assert obj_sbml

            obj_id = obj_sbml.getId()
            obj_name = obj_sbml.getName() or obj_id
            for flux_obj_sbml in obj_sbml.getListOfFluxObjectives():
                rxn_id = flux_obj_sbml.getReaction()
                rxn_sbml = self._get_reaction(model_sbml, rxn_id)
                rxn_name = rxn_sbml.getName() or rxn_id
                value = flux_obj_sbml.getCoefficient()
                parameters[species_id] = ModelParameter(
                    target='/' + '/'.join([
                        "sbml:sbml",
                        "sbml:model",
                        "fbc:listOfObjectives",
                        "fbc:objective[@fbc:id='{}']".format(obj_id),
                        "fbc:listOfFluxObjectives",
                        "fbc:fluxObjective[@fbc:reaction='{}']".format(rxn_id),
                        "@fbc:coefficient",
                    ]),
                    group='Flux objective coefficients',
                    id="{}/{}".format(obj_id, rxn_id),
                    name='Coefficient of {} of {}'.format(obj_name, rxn_name),
                    description=None,
                    identifiers=[],
                    type=Type.float,
                    value=value,
                    recommended_range=self._calc_recommended_param_range(value),
                    units='dimensionless',
                )

        # qual package
        plugin_sbml = model_sbml.getPlugin('qual')
        if plugin_sbml:
            for species_sbml in plugin_sbml.getListOfQualitativeSpecies():
                species_id = species_sbml.getId()
                init_level = species_sbml.getInitialLevel()
                if species_sbml.isSetMaxLevel():
                    max_level = species_sbml.getMaxLevel()
                else:
                    max_level = max(1, init_level)

                parameters[species_id] = ModelParameter(
                    target='/' + '/'.join([
                        "sbml:sbml",
                        "sbml:model",
                        "qual:listOfQualitativeSpecies",
                        "qual:qualitativeSpecies[@qual:id='{}']".format(species_id),
                        "@qual:initialLevel",
                    ]),
                    group='Initial species levels',
                    id='init_level_' + species_id,
                    name='Initial level of {}'.format(species_sbml.getName() or species_id),
                    description=None,
                    identifiers=[],
                    type=Type.integer,
                    value=init_level,
                    recommended_range=[0, max_level],
                    units='dimensionless',
                )

        # ignore parameters set via assignment rules and initial assignments
        for rule_sbml in model_sbml.getListOfRules():
            if rule_sbml.isScalar():
                param_id = rule_sbml.getVariable()
                if param_id in parameters:
                    parameters.pop(param_id)

        for init_assign_sbml in model_sbml.getListOfInitialAssignments():
            param_id = init_assign_sbml.getSymbol()
            if param_id in parameters:
                parameters.pop(param_id)

        # return parameters
        model.parameters = parameters.values()
        return model.parameters

    def _read_parameter(self, param_sbml, model, rxn_sbml=None, rxn_id=None, rxn_name=None):
        """ Read information about a SBML parameter

        Args:
            param_sbml (:obj:`libsbml.ModelParameter`): SBML parameter
            model (:obj:`Model`): model
            rxn_sbml (:obj:`libsbml.Reaction`, optional): SBML reaction
            rxn_id (:obj:`str`, optional): id of the parent reaction (used by local parameters)
            rxn_name (:obj:`str`, optional): name of the parent reaction (used by local parameters)

        Returns:
            :obj:`ModelParameter`: information about the parameter
        """
        assert param_sbml.getId()

        value = param_sbml.getValue()
        param = ModelParameter(
            target=None,
            group=None,
            id=param_sbml.getId(),
            name=param_sbml.getName() or param_sbml.getId(),
            description=None,
            identifiers=[],
            type=Type.float,
            value=value,
            recommended_range=self._calc_recommended_param_range(value),
            units=self._format_unit_def(param_sbml.getDerivedUnitDefinition()),
        )

        if rxn_sbml:
            if int(model.format.version[1]) >= 3:
                target = [
                    "sbml:sbml",
                    "sbml:model",
                    "sbml:listOfReactions",
                    "{}:{}[@id='{}']".format(rxn_sbml.getPrefix() or 'sbml', rxn_sbml.getElementName(), rxn_id),
                    "sbml:kineticLaw",
                    "sbml:listOfLocalParameters",
                    "sbml:{}[@id='{}']".format(param_sbml.getElementName(), param.id),
                    "@value",
                ]
            else:
                target = [
                    "sbml:sbml",
                    "sbml:model",
                    "sbml:listOfReactions",
                    "{}:{}[@id='{}']".format(rxn_sbml.getPrefix() or 'sbml', rxn_sbml.getElementName(), rxn_id),
                    "sbml:kineticLaw",
                    "sbml:listOfParameters",
                    "sbml:{}[@id='{}']".format(param_sbml.getElementName(), param.id),
                    "@value",
                ]
            group = '{} rate constants'.format(rxn_name or rxn_id)
        else:
            target = [
                "sbml:sbml",
                "sbml:model",
                "sbml:listOfParameters",
                "sbml:parameter[@id='{}']".format(param.id),
                "@value",
            ]
            group = 'Other global parameters'
        param.target = '/' + '/'.join(target)
        param.group = group

        if rxn_id:
            param.id = rxn_id + '/' + param.id
            param.name = (rxn_name or rxn_id) + ': ' + (param.name or param.id)

        return param

    def _read_variables(self, model_sbml, model, units):
        """ Read the variables of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`Model`): model
            units (:obj:`dict`): dictionary that maps the ids of units to their definitions

        Returns:
            :obj:`list` of :obj:`Variable`: information about the variables of the model
        """
        model.variables = vars = []

        fbc_plugin_sbml = model_sbml.getPlugin('fbc')

        if fbc_plugin_sbml:
            flux_units = pretty_print_units('({}) / ({})'.format(
                units.get(model_sbml.getExtentUnits(), None) or model_sbml.getExtentUnits(),
                units.get(model_sbml.getTimeUnits(), None) or model_sbml.getTimeUnits(),
            ))

            # objective
            obj_sbml = fbc_plugin_sbml.getActiveObjective()
            assert obj_sbml

            obj_id = obj_sbml.getId()
            assert obj_id

            vars.append(Variable(
                target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='{}']".format(obj_id),
                group='Objectives',
                id=obj_id,
                name=obj_sbml.getName() or obj_id,
                description=None,
                identifiers=[],
                type=Type.float,
                units=flux_units,
            ))

            # reaction fluxes
            for rxn_sbml in model_sbml.getListOfReactions():
                rxn_id = rxn_sbml.getId()
                vars.append(Variable(
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/{}:{}[@id='{}']".format(
                        rxn_sbml.getPrefix() or 'sbml', rxn_sbml.getElementName(), rxn_id),
                    group='Reaction fluxes',
                    id=rxn_id,
                    name=rxn_sbml.getName() or None,
                    description=None,
                    identifiers=[],
                    type=Type.float,
                    units=flux_units,
                ))

        else:
            # regular species
            for species_sbml in model_sbml.getListOfSpecies():
                vars.append(self._read_variable(model_sbml, species_sbml, model))

            # qualitative species of qual package
            qual_plugin = model_sbml.getPlugin('qual')
            if qual_plugin:
                for species_sbml in qual_plugin.getListOfQualitativeSpecies():
                    species_id = species_sbml.getId()

                    vars.append(Variable(
                        target=("/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies"
                                "/qual:qualitativeSpecies[@qual:id='{}']").format(species_id),
                        group='Species levels',
                        id=species_id,
                        name=species_sbml.getName() or None,
                        description=None,
                        identifiers=[],
                        type=Type.integer,
                        units='dimensionless',
                    ))

        return vars

    def _read_variable(self, model_sbml, species_sbml, model):
        """ Read information about a SBML species

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            species_sbml (:obj:`libsbml.Species`): SBML species
            model (:obj:`Model`): model

        Returns:
            :obj:`Variable`: information about the species
        """
        id = species_sbml.getId()
        assert id

        var = Variable(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']".format(id),
            group='Species amounts/concentrations',
            id=id,
            name=species_sbml.getName() or None,
            description=None,
            identifiers=[],
            type=Type.float,
            units=self._format_unit_def(species_sbml.getDerivedUnitDefinition()),
        )

        return var

    def _get_compartment(self, model_sbml, comp_id):
        """ Get a compartment

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            comp_id (:obj:`str`): compartment id

        Returns:
            :obj:`libsbml.Compartment`: compartment
        """
        for comp_sbml in model_sbml.getListOfCompartments():
            if comp_sbml.getId() == comp_id:
                return comp_sbml

    def _get_reaction(self, model_sbml, rxn_id):
        """ Get a reaction

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            rxn_id (:obj:`str`): reaction id

        Returns:
            :obj:`libsbml.Reaction`: reaction
        """
        for rxn_sbml in model_sbml.getListOfReactions():
            if rxn_sbml.getId() == rxn_id:
                return rxn_sbml

    def _format_unit_def(self, unit_def_sbml):
        """ Get a human-readable representation of a unit definition

        Args:
            unit_def_sbml (:obj:`libsbml.UnitDefinition`): unit definition

        Returns:
            :obj:`str`: human-readable string representation of the unit definition
        """
        if not unit_def_sbml:
            return None

        unit_def_str = unit_def_sbml.printUnits(unit_def_sbml, True)
        if unit_def_str == 'indeterminable':
            return None

        return pretty_print_units(unit_def_str.replace(', ', ' * '))

    def _calc_recommended_param_range(self, value, zero_fold=10., non_zero_fold=10.):
        """ Calculate a recommended range for the value of a parameter

        Args:
            value (:obj:`float`): Default value
            non_zero_fold (:obj:`float`, optional): Multiplicative factor, :math:`f`, for the recommended minimum and maximum
                values relative to the default value, :math:`d`, producing the recommend range :math:`d / f - d * f`.

        Returns:
            :obj:`list` of :obj:`float`: recommended minimum and maximum values of the parameter
        """
        if value == 0:
            return [0., zero_fold]

        else:
            return [
                value * non_zero_fold ** -1,
                value * non_zero_fold,
            ]

    @classmethod
    def _get_xml_child_by_names(cls, node, names):
        """ Get the child of an XML element with a prefix and name

        Args:
            node (:obj:`libsbml.XMLNode`): XML node
            names (:obj:`list` of :obj:`XmlName`): names

        Returns:
            :obj:`libsbml.XMLNode`: child with prefix and name
        """
        for name in names:
            if not node:
                break
            node = cls._get_xml_child_by_name(node, name)
        return node

    @classmethod
    def _get_xml_child_by_name(cls, node, name):
        """ Get the child of an XML element with a prefix and name

        Args:
            node (:obj:`libsbml.XMLNode`): XML node
            name (:obj:`XmlName`): name

        Returns:
            :obj:`libsbml.XMLNode`: child with prefix and name
        """
        matching_children = []
        for i_child in range(node.getNumChildren()):
            child = node.getChild(i_child)
            if child.getPrefix() == name.prefix and child.getName() == name.name:
                matching_children.append(child)
        if len(matching_children) == 1:
            return matching_children[0]
        else:
            return None

    @classmethod
    def _get_xml_attr_by_name(cls, node, name):
        """ Get an attribute of an XML element with a prefix and name

        Args:
            node (:obj:`libsbml.XMLNode`): XML node
            name (:obj:`XmlName`): attribute name

        Returns:
            :obj:`str`: attribute value
        """
        for i_attr in range(node.getAttributesLength()):
            if node.getAttrPrefix(i_attr) == name.prefix and node.getAttrName(i_attr) == name.name:
                return node.getAttrValue(i_attr)


def viz_model(model_filename, img_filename):
    """ Use `Minerva <https://minerva.pages.uni.lu/>`_ to visualize a model and save the visualization to a PNG file.

    Args:
        model_filename (:obj:`str`): path to the SBML-encoded model
        img_filename (:obj:`str`): path to save the visualization of the model
    """
    # read the model
    doc = libsbml.readSBMLFromFile(model_filename)
    model = doc.getModel()

    # remove layouts from the model
    plugin = model.getPlugin('layout')
    if plugin:
        for i_layout in range(plugin.getNumLayouts()):
            plugin.removeLayout(i_layout)
    model_without_layout = libsbml.writeSBMLToString(doc)

    # use Minerva to generate a visualization of the model
    url = 'https://minerva-dev.lcsb.uni.lu/minerva/api/convert/image/{}:{}'.format('SBML', 'png')
    response = requests.post(url, headers={'Content-Type': 'text/plain'}, data=model_without_layout)
    response.raise_for_status()
    with open(img_filename, 'wb') as file:
        file.write(response.content)
    img = Image.open(img_filename)

    # make the background of the visualization transparent
    img = img.convert('RGBA')
    img_data = numpy.array(img)
    img_rgb = img_data[:, :, :3]
    white = [255, 255, 255]
    transparent = [0, 0, 0, 0]
    mask = numpy.all(img_rgb == white, axis=-1)
    img_data[mask] = transparent
    img = Image.fromarray(img_data)

    # crop the visualization
    img_bbox = img.getbbox()
    cropped_img = img.crop(img_bbox)

    # save the visualization
    cropped_img.save(img_filename)
