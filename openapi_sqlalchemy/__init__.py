"""Map an OpenAPI schema to SQLAlchemy models."""

import functools
import typing

import typing_extensions
from sqlalchemy.ext.declarative import declarative_base

from . import exceptions
from . import model_factory as _model_factory
from . import types


class ModelFactory(typing_extensions.Protocol):
    """Defines interface for model factory."""

    def __call__(self, name: str) -> typing.Type:
        """Call signature for ModelFactory."""
        ...


def init_model_factory(*, base: typing.Type, spec: types.Schema) -> ModelFactory:
    """
    Create factory that generates SQLAlchemy models based on OpenAPI specification.

    Args:
        base: The declarative base for the models.
        spec: The OpenAPI specification in the form of a dictionary.

    Returns:
        A factory that returns SQLAlchemy models derived from the base based on the
        OpenAPI specification.

    """
    # Retrieving the schema from the specification
    if "components" not in spec:
        raise exceptions.MalformedSpecificationError(
            '"components" is a required key in the specification.'
        )
    components = spec.get("components", {})
    if "schemas" not in components:
        raise exceptions.MalformedSpecificationError(
            '"schemas" is a required key in the components of the specification.'
        )
    schemas = components.get("schemas", {})

    # Binding the base and schemas
    bound_model_factories = functools.partial(
        _model_factory.model_factory, schemas=schemas, base=base
    )
    # Caching calls
    cached_model_factories = functools.lru_cache(maxsize=None)(bound_model_factories)

    return cached_model_factories


def init_json(spec_filename: str, *, base: typing.Type) -> typing.Tuple:
    """
    Create factory that generates SQLAlchemy models based on an OpenAPI specification
    as a JSON file.

    Args:
        spec_filename: filename of an OpenAPI spec in JSON format
        base: The declarative base for the models.

    Returns:
        A tuple (Base, model_factory), where:

        Base: a SQLAlchemy declarative base class
        model_factory: A factory that returns SQLAlchemy models derived from the
                       base based on the OpenAPI specification.

    """
    # Most OpenAPI specs are YAML, so, for efficiency, we only import json if we
    # need it:
    import json

    if base is None:
        Base = declarative_base()

    with open(spec_filename) as spec_file:
        spec = json.load(spec_file, Loader=Loader)
    model_factory = init_model_factory(base=Base, spec=spec)
    return Base, model_factory


def init_yaml(spec_filename: str, *, base: typing.Type = None) -> typing.Tuple:
    """
    Create factory that generates SQLAlchemy models based on an OpenAPI specification
    as a YAML file.

    Args:
        spec_filename: filename of an OpenAPI spec in YAML format
        base: (optional) The declarative base for the models.
              If base=None, construct a new SQLAlchemy declarative base.

    Returns:
        A tuple (Base, model_factory), where:

        Base: a SQLAlchemy declarative base class
        model_factory: A factory that returns SQLAlchemy models derived from the
                       base based on the OpenAPI specification.

    """

    try:
        import yaml
    except ImportError:
        raise ImportError('Using init_yaml requires the pyyaml package. '
                          'Try `pip install pyyaml`.'
        )

    if base is None:
        Base = declarative_base()

    with open(spec_filename) as spec_file:
        spec = yaml.load(spec_file, Loader=yaml.Loader)
    model_factory = init_model_factory(base=Base, spec=spec)
    return Base, model_factory


__all__ = ['init_model_factory', 'init_json', 'init_yaml']
