
"""Interface to Scenic."""

try:
    import scenic
except ModuleNotFoundError:
    import sys
    sys.exit('this functionality requires Scenic to be installed')

from scenic.core.distributions import needsSampling, Options
from scenic.core.vectors import Vector
from scenic.core.type_support import canCoerceType, coerce, underlyingType

# TODO unify handling of these custom types!
from scenic.simulators.gta.interface import CarModel as GTACarModel, CarColor
from scenic.simulators.webots.road.car_models import (
    CarModel as WebotsCarModel, carModels as webotsCarModels)

from verifai.features import (Constant, Categorical, Real, Box, Array, Struct,
                              Feature, FeatureSpace)
from verifai.samplers.feature_sampler import FeatureSampler

scalarDomain = Real()
vectorDomain = Array(scalarDomain, (2,))
gtaModelDomain = Categorical(*GTACarModel.models.values())
webotsModelDomain = Categorical(*webotsCarModels)
colorDomain = Box((0, 1), (0, 1), (0, 1))

def convertToVerifaiType(value, strict=True):
    """Attempt to convert a Scenic value to a type known to Verifai"""
    ty = underlyingType(value)
    if ty is float or ty is int:
        return float(value)
    elif canCoerceType(ty, Vector):
        return tuple(coerce(value, Vector))
    elif ty is GTACarModel:
        return value
    elif ty is WebotsCarModel:
        return value
    elif ty is CarColor:
        return value
    elif strict:    # Unknown type, so give up if we're being strict
        raise RuntimeError(
            f'attempted to convert Scenic value {value} of unknown type {ty}')
    else:
        return value

def domainForValue(value):
    """Return a Domain for this type of Scenic value, when possible"""
    ty = underlyingType(value)
    if ty is float or ty is int:
        domain = scalarDomain
    elif canCoerceType(ty, Vector):
        domain = vectorDomain
    elif ty is str:
        # We can only handle strings when they come from a finite set of
        # possibilities; we heuristically detect that here.
        if isinstance(value, Options):
            domain = Categorical(*value.options)
        else:
            domain = None   # we can't ensure the domain is finite
    elif ty is GTACarModel:
        domain = gtaModelDomain
    elif ty is WebotsCarModel:
        domain = webotsModelDomain
    elif ty is CarColor:
        domain = colorDomain
    else:
        domain = None   # no corresponding Domain known
    if not needsSampling(value):
        # We can handle constants of unknown types, but when possible we
        # convert the value to a Verifai type.
        if domain is not None:
            value = convertToVerifaiType(value)
        return Constant(value)
    return domain

def pointForValue(dom, scenicValue):
    """Convert a sampled Scenic value to a point in the corresponding Domain"""
    if isinstance(dom, Constant):
        value = convertToVerifaiType(scenicValue, strict=False)
        assert value == dom.value
        return value
    elif isinstance(dom, Categorical):
        value = convertToVerifaiType(scenicValue, strict=False)
        assert value in dom.values
        return value
    elif dom is scalarDomain:
        if not isinstance(scenicValue, (float, int)):
            raise RuntimeError(
                f'could not coerce Scenic value {scenicValue} to scalar')
        return coerce(scenicValue, float)
    elif dom is vectorDomain:
        return tuple(coerce(scenicValue, Vector))
    elif dom is colorDomain:
        assert isinstance(scenicValue, tuple)
        assert len(scenicValue) == 3
        return scenicValue
    else:
        raise RuntimeError(
            f'Scenic value {scenicValue} has unexpected domain {dom}')

# properties not included when sampling
defaultIgnoredProperties = {
    'viewAngle', 'visibleDistance', 'cameraOffset',
    'allowCollisions', 'requireVisible', 'regionContainedIn',
    'mutator', 'mutationEnabled', 'positionStdDev', 'headingStdDev',
}
# certain built-in properties requiring type normalization
normalizedProperties = {
    'position': Vector,
    'heading': float
}
# hard-coded Domains for certain properties
specialDomainProperties = {
    'webotsType': Categorical(*(model.name for model in webotsCarModels))
}

def domainForObject(obj, ignoredProperties):
    """Construct a Domain for the given Scenic Object"""
    domains = {}
    for prop in obj.properties:
        if prop in ignoredProperties:
            continue
        value = getattr(obj, prop)
        if prop in normalizedProperties:
            value = coerce(value, normalizedProperties[prop])
        # TODO improve this system... (need to get better type info in Scenic)
        if prop in specialDomainProperties and needsSampling(value):
            dom = specialDomainProperties[prop]
        else:
            dom = domainForValue(value)
        if dom is None:
            ty = underlyingType(value)
            print(f'WARNING: skipping property "{prop}" of unknown type {ty}')
        else:
            domains[prop] = dom
    # add type as additional property
    value = type(obj).__name__
    dom = domainForValue(value)
    assert dom is not None
    assert 'type' not in domains
    domains['type'] = dom
    return Struct(domains)

def pointForObject(dom, obj):
    """Convert a sampled Scenic Object to a point in its Domain"""
    values = []
    for prop, subdom in dom.domainNamed.items():
        if prop == 'type':      # special case for 'type' pseudo-property
            scenicValue = type(obj).__name__
        else:
            scenicValue = getattr(obj, prop)
        values.append(pointForValue(subdom, scenicValue))
    return dom.makePoint(*values)

def spaceForScenario(scenario, ignoredProperties):
    """Construct a FeatureSpace for the given Scenic Scenario"""
    # create domains for objects
    assert scenario.egoObject is scenario.objects[0]
    doms = (domainForObject(obj, ignoredProperties)
            for obj in scenario.objects)
    objects = Struct({ f'object{i}': dom for i, dom in enumerate(doms) })

    # create domains for global parameters
    paramDoms = {}
    for param, value in scenario.params.items():
        dom = domainForValue(value)
        if dom is None:
            ty = underlyingType(value)
            print(f'WARNING: skipping param "{param}" of unknown type {ty}')
        else:
            paramDoms[param] = dom
    params = Struct(paramDoms)

    return FeatureSpace({
        'objects': Feature(objects),
        'params': Feature(params)
    })

def pointForScene(space, scene):
    """Convert a sampled Scenic Scene to a point in the Scenario's space"""
    lengths, dom = space.domains
    assert lengths is None
    assert scene.egoObject is scene.objects[0]
    objDomain = dom.domainNamed['objects']
    assert len(objDomain.domains) == len(scene.objects)
    objects = (pointForObject(subdom, obj)
               for subdom, obj in zip(objDomain.domains, scene.objects))
    objPoint = objDomain.makePoint(*objects)

    paramDomain = dom.domainNamed['params']
    params = {}
    for param, subdom in paramDomain.domainNamed.items():
        params[param] = pointForValue(subdom, scene.params[param])
    paramPoint = paramDomain.makePoint(**params)

    return space.makePoint(objects=objPoint, params=paramPoint)

class ScenicSampler(FeatureSampler):
    """Samples from the induced distribution of a Scenic scenario.

    maxIterations controls Scenic's internal rejection sampling, and
    ignoredProperties specifies which Object properties should not be included
    in the sampled points.
    """

    def __init__(self, scenario, maxIterations=None, ignoredProperties=None):
        self.scenario = scenario
        self.maxIterations = 2000 if maxIterations is None else maxIterations
        if ignoredProperties is None:
            ignoredProperties = defaultIgnoredProperties
        space = spaceForScenario(scenario, ignoredProperties)
        super().__init__(space)

    @classmethod
    def fromScenario(cls, path, maxIterations=None, ignoredProperties=None):
        """Create a sampler corresponding to a Scenic program."""
        scenario = scenic.scenarioFromFile(path)
        return cls(scenario, maxIterations=maxIterations,
                   ignoredProperties=ignoredProperties)

    @classmethod
    def fromScenicCode(cls, code, maxIterations=None, ignoredProperties=None):
        """As above, but given a Scenic program as a string."""
        scenario = scenic.scenarioFromString(code)
        return cls(scenario, maxIterations=maxIterations,
                   ignoredProperties=ignoredProperties)

    def nextSample(self):
        scene, iterations = self.scenario.generate(
            maxIterations=self.maxIterations)
        return pointForScene(self.space, scene)
