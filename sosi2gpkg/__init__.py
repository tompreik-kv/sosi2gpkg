def classFactory(iface):
    from .sosi2gpkg_plugin import Sosi2GpkgPlugin
    return Sosi2GpkgPlugin(iface)
