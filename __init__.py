from . import SpoolmanMaterialExtension


def getMetaData():
    return {}


def register(app):
    return {"extension": SpoolmanMaterialExtension.SpoolmanMaterialExtension()}
