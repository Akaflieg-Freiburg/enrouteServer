#!/bin/python3

"""
vector_tile
=======================================================================================================

Toolset to manipulate vector tiles, in the format described here:
https://github.com/mapbox/vector-tile-spec/tree/master/2.1
"""

def getMetaData(feature, layer):
    """Obtain meta data for a feature, as a convenient string-to-value dictionary

    :param feature: Feature whose meta data is to be read

    :param layer: Layer that contains the feature

    :returns: Meta data dictionary
    """
    metaData = {}                   
    for i in range(0, len(feature.tags), 2):                 
        metaData[layer.keys[feature.tags[i]]] = layer.values[feature.tags[i+1]]
    return metaData


def optimizeLayer(layer):
    """Delete unused keys and values from a layer

    :param layer: Layer that is to be optimized. The layer is modified in-place
    """
    keysInUse = []
    valuesInUse = []
    for feature in layer.features:
        for i in range(0, len(feature.tags), 2):
            key = layer.keys[feature.tags[i]]
            if not key in keysInUse:
                keysInUse.append(key)
            feature.tags[i] = keysInUse.index(key)
            value = layer.values[feature.tags[i+1]]
            if not value in valuesInUse:
                valuesInUse.append(value)
            feature.tags[i+1] = valuesInUse.index(value)

    del layer.keys[:]
    layer.keys.extend(keysInUse)
    del layer.values[:]
    layer.values.extend(valuesInUse)

