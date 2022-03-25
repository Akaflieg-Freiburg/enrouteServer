#!/bin/python3

import vector_tile_pb2

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


def removeLayers(tile, list):
    """Deletes all layers from the tile whose names are contained in the list.

    :param tile: Tile whose layers are deleted

    :param list: List of key layer names
    """
    newLayers = []
    for layer in tile.layers:
        if layer.name in list:
            continue
        newLayer = vector_tile_pb2.Tile.Layer()
        newLayer.CopyFrom(layer)
        newLayers.append(newLayer)
    del tile.layers[:]
    tile.layers.extend(newLayers)


def restrictFeatures(layer, keyName, list):
    """Delete all features from the layer, except features with meta data where the value for the key name is contained in the list.

    :param layer: Layer whose features are deleted

    :param keyName: Name of key

    :param list: List of values
    """
    newFeatures = []
    for feature in layer.features:
        metaData = getMetaData(feature, layer)
        if metaData[keyName].string_value not in list:
            continue
        newFeature = vector_tile_pb2.Tile.Feature()
        newFeature.CopyFrom(feature)
        newFeatures.append(newFeature)
    del layer.features[:]
    layer.features.extend(newFeatures)


def restrictTags(layer, list):
    """Delete all tags from all features, except feature whose key names are contained in the list.

    :param layer: Layer whose features are deleted

    :param list: List of key names
    """
    for feature in layer.features:
        newTags = []
        for i in range(0, len(feature.tags), 2):
            if layer.keys[feature.tags[i]] not in list:
                continue
            newTags.append(feature.tags[i])
            newTags.append(feature.tags[i+1])
        del feature.tags[:]
        feature.tags.extend(newTags)


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

