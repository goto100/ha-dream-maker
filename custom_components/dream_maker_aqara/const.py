"""Aqara model and resource identifiers for the Dream Maker air quality monitor."""

DOMAIN = "dream_maker_aqara"
SOURCE_DOMAIN = "ha_aqara_devices"
CONF_SOURCE_ENTRY_ID = "source_entry_id"
MODEL = "aqara.adetector.drcn01"
TEMPERATURE = "0.1.85"
HUMIDITY = "0.2.85"
PM25 = "0.20.85"
CO2 = "0.6.85"
RESOURCE_IDS = (TEMPERATURE, HUMIDITY, PM25, CO2)
