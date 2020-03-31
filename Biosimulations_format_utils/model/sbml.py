""" Utilities for working with SBML-encoded models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import ModelReader, ModelIoError
import copy
import enum
import ete3
import libsbml
import math
import os
import re

__all__ = ['SbmlModelReader']


class ModelFramework(dict, enum.Enum):
    flux_balance = {
        'ontology': 'SBO',
        'id': '0000624',
        'name': 'flux balance framework',
        'description': ('Modelling approach, typically used for metabolic models, where the flow '
                        'of metabolites (flux) through a network can be calculated. This approach '
                        'will generally produce a set of solutions (solution space), which may be '
                        'reduced using objective functions and constraints on individual fluxes.'),
        'iri': 'http://biomodels.net/SBO/SBO_0000624',
    }

    logical = {
        'ontology': 'SBO',
        'id': '0000234',
        'name': 'logical framework',
        'description': ('Modelling approach, pioneered by Rene Thomas and Stuart Kaufman, where the '
                        'evolution of a system is described by the transitions between discrete activity '
                        'states of "genes" that control each other.'),
        'iri': 'http://biomodels.net/SBO/SBO_0000234',
    }

    non_spatial_continuous = {
        'ontology': 'SBO',
        'id': '0000293',
        'name': 'non-spatial continuous framework',
        'description': ('Modelling approach where the quantities of participants are considered continuous, '
                        'and represented by real values. The associated simulation methods make use of '
                        'differential equations. The models do not take into account the distribution of the '
                        'entities and describe only the temporal fluxes.'),
        'iri': 'http://biomodels.net/SBO/SBO_0000293',
    }

    non_spatial_discrete = {
        'ontology': 'SBO',
        'id': '0000295',
        'name': 'non-spatial discrete framework',
        'description': ('Modelling approach where the quantities of participants are considered discrete, '
                        'and represented by integer values. The associated simulation methods can be '
                        'deterministic or stochastic.The models do not take into account the distribution '
                        'of the entities and describe only the temporal fluxes.'),
        'iri': 'http://biomodels.net/SBO/SBO_0000295',
    }

    spatial_continuous = {
        'ontology': 'SBO',
        'id': '0000292 ',
        'name': 'spatial continuous framework',
        'description': ('Modelling approach where the quantities of participants are considered continuous, '
                        'and represented by real values. The associated simulation methods make use of '
                        'differential equations. The models take into account the distribution of the '
                        'entities and describe the spatial fluxes.'),
        'iri': 'http://biomodels.net/SBO/SBO_0000292 ',
    }

    spatial_discrete = {
        'ontology': 'SBO',
        'id': '0000294',
        'name': 'spatial discrete framework',
        'description': ('Modelling approach where the quantities of participants are considered discrete, '
                        'and represented by integer values. The associated simulation methods can be '
                        'deterministic or stochastic. The models take into account the distribution of '
                        'the entities and describe the spatial fluxes.'),
        'iri': 'http://biomodels.net/SBO/SBO_0000294',
    }


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
            model (:obj:`dict`): model

        Returns:
            :obj:`dict`: format of the model
        """
        model['format'] = {
            'name': 'SBML',
            'version': 'L{}V{}'.format(model_sbml.getLevel(), model_sbml.getVersion()),
            'edamId': 'format_2585',
            'url': 'http://sbml.org',
        }

        return model['format']

    def _read_metadata(self, model_sbml, model):
        """ Read the metadata of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`dict`): model

        Returns:
            :obj:`dict`: model with additional metadata
        """
        annot_xml = model_sbml.getAnnotation()
        desc_xml = self._get_xml_child_by_names(annot_xml, [
            XmlName('rdf', 'RDF'),
            XmlName('rdf', 'Description'),
        ])

        # modeling framework
        packages = set()
        for i_plugin in range(model_sbml.getNumPlugins()):
            plugin = model_sbml.getPlugin(i_plugin)
            packages.add(plugin.getPackageName())
        packages = packages.difference(set(['annot', 'layout', 'render', 'req']))
        if packages:
            raise ModelIoError("{} packages are not supported".format(', '.join(packages)))

        framework = ModelFramework.non_spatial_continuous
        model['framework'] = framework.value

        # taxon
        taxon_xml = self._get_xml_child_by_names(desc_xml, [
            XmlName('bqbiol', 'hasTaxon'),
            XmlName('rdf', 'Bag'),
            XmlName('rdf', 'li'),
        ])
        model['taxon'] = None
        if taxon_xml:
            taxon_url = self._get_xml_attr_by_name(taxon_xml, XmlName('rdf', 'resource'))
            match = re.match(r'https?://identifiers.org/taxonomy/(\d+)', taxon_url)
            if match:
                taxon_id = int(match.group(1))
                ncbi_taxa = ete3.NCBITaxa()
                taxon_name = ncbi_taxa.get_taxid_translator([taxon_id]).get(taxon_id, None)
                if taxon_name:
                    model['taxon'] = {
                        'id': taxon_id,
                        'name': taxon_name,
                    }
                else:
                    model['taxon_name'] = None

        return model

    def _read_units(self, model_sbml, model):
        """ Read the units of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`dict`): model

        Returns:
            :obj:`dict`: dictionary that maps the ids of units to their definitions
        """
        model['units'] = {}
        for i_unit_def in range(model_sbml.getNumUnitDefinitions()):
            unit_def_sbml = model_sbml.getUnitDefinition(i_unit_def)
            model['units'][unit_def_sbml.getId()] = self._format_units(unit_def_sbml.getDerivedUnitDefinition())

        return model['units']

    def _read_parameters(self, model_sbml, model):
        """ Read information about the parameters of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`dict`): model

        Returns:
            :obj:`list` of :obj:`dict`: information about parameters
        """
        model['parameters'] = parameters = []

        for i_param in range(model_sbml.getNumParameters()):
            param_sbml = model_sbml.getParameter(i_param)
            parameters.append(self._read_parameter(param_sbml, model))

        for i_rxn in range(model_sbml.getNumReactions()):
            rxn_sbml = model_sbml.getReaction(i_rxn)

            kin_law_sbml = rxn_sbml.getKineticLaw()
            if not kin_law_sbml:
                continue

            reaction_id = rxn_sbml.getId()
            reaction_name = rxn_sbml.getName() or None

            for i_param in range(kin_law_sbml.getNumParameters()):
                assert reaction_id
                param_sbml = kin_law_sbml.getParameter(i_param)
                parameters.append(self._read_parameter(param_sbml, model, reaction_id=reaction_id, reaction_name=reaction_name))

        return parameters

    def _read_parameter(self, param_sbml, model, reaction_id=None, reaction_name=None):
        """ Read information about a SBML parameter

        Args:
            param_sbml (:obj:`libsbml.Parameter`): SBML parameter
            model (:obj:`dict`): model
            reaction_id (:obj:`str`, optional): id of the parent reaction (used by local parameters)
            reaction_name (:obj:`str`, optional): name of the parent reaction (used by local parameters)

        Returns:
            :obj:`dict`: information about the parameter
        """
        assert param_sbml.getId()

        param = {
            'target': None,
            'id': param_sbml.getId(),
            'name': param_sbml.getName() or None,
            'value': param_sbml.getValue(),
            'units': self._format_units(param_sbml.getDerivedUnitDefinition()),
        }

        if reaction_id:
            if int(model['format']['version'][1]) >= 3:
                target = [
                    "sbml:sbml",
                    "sbml:model",
                    "sbml:listOfReactions",
                    "sbml:reaction[@id='{}']".format(reaction_id),
                    "sbml:kineticLaw",
                    "sbml:listOfLocalParameters",
                    "sbml:localParameter[@id='{}']".format(param['id']),
                    "@value",
                ]
            else:
                target = [
                    "sbml:sbml",
                    "sbml:model",
                    "sbml:listOfReactions",
                    "sbml:reaction[@id='{}']".format(reaction_id),
                    "sbml:kineticLaw",
                    "sbml:listOfParameters",
                    "sbml:parameter[@id='{}']".format(param['id']),
                    "@value",
                ]
        else:
            target = [
                "sbml:sbml",
                "sbml:model",
                "sbml:listOfParameters",
                "sbml:parameter[@id='{}']".format(param['id']),
                "@value",
            ]
        param['target'] = '/' + '/'.join(target)

        if reaction_id and param['id']:
            param['id'] = reaction_id + '.' + param['id']
        if reaction_name and param['name']:
            param['name'] = reaction_name + ': ' + param['name']

        return param

    def _read_variables(self, model_sbml, model):
        """ Read the variables of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`dict`): model

        Returns:
            :obj:`list` of :obj:`dict`: information about the variables of the model
        """
        model['variables'] = vars = []
        for i_species in range(model_sbml.getNumSpecies()):
            species_sbml = model_sbml.getSpecies(i_species)
            vars.append(self._read_variable(model_sbml, species_sbml, model))
        return vars

    def _read_variable(self, model_sbml, species_sbml, model):
        """ Read information about a SBML species

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            species_sbml (:obj:`libsbml.Species`): SBML species
            model (:obj:`dict`): model

        Returns:
            :obj:`dict`: information about the species
        """
        id = species_sbml.getId()
        assert id

        comp_sbml = None
        comp_id = species_sbml.getCompartment() or None
        comp_name = None
        if comp_id:
            for i_comp in range(model_sbml.getNumCompartments()):
                comp_sbml = model_sbml.getCompartment(i_comp)
                if comp_sbml.getId() == comp_id:
                    break
            comp_name = comp_sbml.getName()

        var = {
            'target': "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']".format(id),
            'id': id,
            'name': species_sbml.getName() or None,
            'compartment_id': comp_id,
            'compartment_name': comp_name,
            'units': self._format_units(species_sbml.getDerivedUnitDefinition()),
            'constant': species_sbml.getConstant(),
            'boundary_condition': species_sbml.getBoundaryCondition(),
        }

        return var

    def _format_units(self, unit_def_sbml):
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

        unit_def_exp = self._unit_registry.parse_expression(unit_def_str.replace(', ', ' * '))
        mag = unit_def_exp.magnitude
        pow = math.floor(math.log10(mag))
        mag = round(mag / math.pow(10, pow), 3)
        units = str(unit_def_exp.units)

        if pow == 0:
            if mag == 1:
                return units
            else:
                return '{} {}'.format(mag, units)
        else:
            if mag == 1:
                return '10^{} {}'.format(pow, units)
            else:
                return '{} 10^{} {}'.format(mag, pow, units)

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
        return None
