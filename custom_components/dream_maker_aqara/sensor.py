"""Dream Maker air quality measurements from the Aqara resource history."""

from datetime import timedelta
from functools import partial
import logging
import math
import time

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfDensity, UnitOfRatio, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

from . import source_api
from .const import CO2, CONF_SOURCE_ENTRY_ID, DOMAIN, HUMIDITY, MODEL, PM25, RESOURCE_IDS, TEMPERATURE

_LOGGER = logging.getLogger(__name__)
POLL_INTERVAL = timedelta(minutes=5)
HISTORY_WINDOW = 3 * POLL_INTERVAL
SENSORS = (
    SensorEntityDescription(
        key=TEMPERATURE, device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=HUMIDITY, device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE, suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=PM25, device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
    ),
    SensorEntityDescription(
        key=CO2, device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
    ),
)


async def async_read_monitor(hass: HomeAssistant, source_entry_id: str, did: str) -> dict[str, float]:
    api = source_api(hass, source_entry_id)
    end = int(time.time() * 1000)
    start = end - int(HISTORY_WINDOW.total_seconds() * 1000)
    try:
        response = await api.res_history(
            {"subjectId": did, "resourceIds": list(RESOURCE_IDS), "startTime": start, "endTime": end}
        )
    except RuntimeError as err:
        raise UpdateFailed(f"Aqara history request failed: {err}") from err
    if str(response["code"]) != "0":
        detail = response.get("msgDetails") or response.get("message")
        raise UpdateFailed(f"Aqara history request returned {response['code']}: {detail}")

    latest = {}
    for row in response["result"]["data"]:
        rid = row["resourceId"]
        if rid not in RESOURCE_IDS:
            continue
        timestamp = int(row["timeStamp"])
        if start <= timestamp <= end and (rid not in latest or timestamp > latest[rid][0]):
            latest[rid] = (timestamp, row["value"])

    values = {}
    for rid, (_, raw) in latest.items():
        if raw is None:
            continue
        try:
            value = float(str(raw))
            if not math.isfinite(value):
                raise ValueError("non-finite measurement")
        except (ValueError, OverflowError):
            _LOGGER.warning("Invalid air quality measurement for device %s, resource %s: %r", did, rid, raw)
            continue
        values[rid] = value
    return values


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    for monitor in entry.runtime_data:
        did = monitor["did"]
        coordinator = DataUpdateCoordinator(
            hass, _LOGGER, config_entry=entry, name=f"Dream Maker {did}",
            update_interval=POLL_INTERVAL, always_update=False,
            update_method=partial(async_read_monitor, hass, entry.data[CONF_SOURCE_ENTRY_ID], did),
        )
        await coordinator.async_refresh()
        async_add_entities([AirQualitySensor(coordinator, monitor, description) for description in SENSORS])


class AirQualitySensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, monitor, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        did = monitor["did"]
        self._attr_unique_id = f"{did}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, did)}, name=monitor["deviceName"], manufacturer="Dream Maker", model=MODEL,
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self.entity_description.key) if self.coordinator.data is not None else None

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None
