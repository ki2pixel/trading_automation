"""Runtime compatibility patches for third-party libraries.

Ensures compatibility between vectorbt 1.x templates and Plotly >= 7.0,
where legacy mapbox trace types were replaced by maplibre trace types.
"""
import pkgutil
import logging

logger = logging.getLogger("backtest_engine.compatibility")

_orig_pkgutil_get_data = pkgutil.get_data

def _safe_pkgutil_get_data(package: str, resource: str) -> bytes:
    data = _orig_pkgutil_get_data(package, resource)
    if isinstance(resource, str) and "templates" in resource and resource.endswith(".json"):
        try:
            # Map legacy Mapbox trace types removed in Plotly 7 to Maplibre trace types
            data = data.replace(b'"scattermapbox"', b'"scattermap"')
            data = data.replace(b'"densitymapbox"', b'"densitymap"')
            data = data.replace(b'"choroplethmapbox"', b'"choroplethmap"')
        except Exception as e:
            logger.debug("[Compatibility] Failed to patch template %s: %s", resource, e)
    return data

pkgutil.get_data = _safe_pkgutil_get_data
