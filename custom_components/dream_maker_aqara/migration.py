"""Transfer registrations created by the earlier Aqara Devices patch."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import entity_sources

from .const import CONF_SOURCE_ENTRY_ID, DOMAIN, MODEL, RESOURCE_IDS, SOURCE_DOMAIN


def migrate_monitors(hass: HomeAssistant, entry: ConfigEntry, monitors: list[dict]) -> None:
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    source_id = entry.data[CONF_SOURCE_ENTRY_ID]
    transfers = []
    for monitor in monitors:
        did = monitor["did"]
        device = devices.async_get_device(identifiers={(SOURCE_DOMAIN, did)})
        if device is None:
            continue
        if device.model != MODEL or device.config_entry_id != source_id:
            raise ConfigEntryError(f"Legacy monitor {did} belongs to a different model or account")
        if devices.async_get_device(identifiers={(DOMAIN, did)}) is not None:
            raise ConfigEntryError(f"A separate monitor registration already exists for {did}")

        expected = {f"{did}_{rid}" for rid in RESOURCE_IDS}
        pending = []
        for row in er.async_entries_for_device(entities, device.id, include_disabled_entities=True):
            if row.domain != "sensor" or row.unique_id not in expected:
                raise ConfigEntryError(f"Unexpected entity attached to the legacy monitor: {row.entity_id}")
            if (row.platform, row.config_entry_id) == (DOMAIN, entry.entry_id):
                continue  # A previous attempt transferred this row before the device.
            if (row.platform, row.config_entry_id) != (SOURCE_DOMAIN, source_id):
                raise ConfigEntryError(f"Unexpected owner of {row.entity_id}")
            if row.entity_id in entity_sources(hass):
                raise ConfigEntryError(f"Restore upstream Aqara Devices before transferring {row.entity_id}")
            if entities.async_get_entity_id("sensor", DOMAIN, row.unique_id):
                raise ConfigEntryError(f"A separate sensor already exists for {row.entity_id}")
            pending.append(row.entity_id)
        transfers.append((device, did, pending))

    for device, did, pending in transfers:
        for entity_id in pending:
            entities.async_update_entity_platform(entity_id, DOMAIN, new_config_entry_id=entry.entry_id)
        devices.async_update_device(
            device.id,
            new_config_entry_id=entry.entry_id,
            new_identifiers=(device.identifiers - {(SOURCE_DOMAIN, did)}) | {(DOMAIN, did)},
        )
