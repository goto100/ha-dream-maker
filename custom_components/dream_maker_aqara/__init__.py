"""Read Dream Maker monitors through an existing Aqara Devices entry."""

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import CONF_SOURCE_ENTRY_ID, MODEL, SOURCE_DOMAIN
from .migration import migrate_monitors

PLATFORMS = [Platform.SENSOR]


def source_api(hass: HomeAssistant, source_entry_id: str):
    """Get the client owned by the currently loaded Aqara entry."""
    source = hass.config_entries.async_get_entry(source_entry_id)
    if source is None or source.state is not ConfigEntryState.LOADED:
        raise UpdateFailed("The selected Aqara Devices entry is not loaded")

    source_data = hass.data.get(SOURCE_DOMAIN, {}).get(source_entry_id, {})
    if (api := source_data.get("api")) is None:
        raise UpdateFailed("The selected Aqara Devices entry has no API client")
    return api


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        api = source_api(hass, entry.data[CONF_SOURCE_ENTRY_ID])
        monitors = await api.get_devices_by_model(MODEL)
    except (ClientError, TimeoutError, RuntimeError, UpdateFailed) as err:
        raise ConfigEntryNotReady(f"Could not discover Dream Maker air quality monitors: {err}") from err
    if not monitors:
        raise ConfigEntryNotReady("No Dream Maker air quality monitors found in the selected Aqara account")

    migrate_monitors(hass, entry, monitors)
    entry.runtime_data = monitors
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
