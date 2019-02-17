"""
Support for RESTful API sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.rest/
"""
import logging
import json

import voluptuous as vol
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from collections import namedtuple
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_AUTHENTICATION, CONF_FORCE_UPDATE, CONF_HEADERS, CONF_NAME,
    CONF_METHOD, CONF_PASSWORD, CONF_PAYLOAD, CONF_RESOURCE,
    CONF_UNIT_OF_MEASUREMENT, CONF_USERNAME,
    CONF_VALUE_TEMPLATE, CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION, STATE_UNKNOWN)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

LIVING_TEMP = 'Livingroom_temperature'
BED_TEMP = 'Bedroom_temperature'
BATH_TEMP = 'Bathroom_temperature'
LIVING_HUM = 'Livingroom_humidity'
BED_HUM = 'Bedroom_humidity'
BATH_HUM = 'Bathroom_humidity'
LIVING_CO2 = 'Livingroom_CO2'
BED_CO2 = 'Bedroom_CO2'
HALLWAY_MOT = 'Hallway_motion'
KIT_MOT = 'Kitchen_motion'
LIVING_MOT = 'Livingroom_motion'
BATH_MOT = 'Bathroom_motion'
BED_MOT = 'Bedroom_motion'
TOT_POW = 'Total_power'

_LOGGER = logging.getLogger(__name__)

DEFAULT_METHOD = 'GET'
DEFAULT_NAME = 'REST Sensor'
DEFAULT_VERIFY_SSL = True
DEFAULT_FORCE_UPDATE = False
CONF_REFRESH_TOKEN = 'refresh_token'

CONF_JSON_ATTRS = 'json_attributes'
METHODS = ['POST', 'GET']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RESOURCE): cv.url,
    vol.Optional(CONF_AUTHENTICATION):
        vol.In([HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]),
    vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
    vol.Optional(CONF_JSON_ATTRS, default=[]): cv.ensure_list_csv,
    vol.Optional(CONF_METHOD, default=DEFAULT_METHOD): vol.In(METHODS),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_PAYLOAD): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    vol.Required(CONF_REFRESH_TOKEN): cv.string,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the RESTful sensor."""
    name = config.get(CONF_NAME)
    resource = config.get(CONF_RESOURCE)
    method = config.get(CONF_METHOD)
    payload = config.get(CONF_PAYLOAD)
    verify_ssl = config.get(CONF_VERIFY_SSL)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    headers = config.get(CONF_HEADERS)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    json_attrs = config.get(CONF_JSON_ATTRS)
    force_update = config.get(CONF_FORCE_UPDATE)
    refresh_token = config.get(CONF_REFRESH_TOKEN)

    if value_template is not None:
        value_template.hass = hass

    if username and password:
        if config.get(CONF_AUTHENTICATION) == HTTP_DIGEST_AUTHENTICATION:
            auth = HTTPDigestAuth(username, password)
        else:
            auth = HTTPBasicAuth(username, password)
    else:
        auth = None
    rest = RestData(method, resource, auth, headers, payload, verify_ssl, refresh_token)
    rest.update()

    add_devices([RestSensor(
        hass, rest, name, unit, value_template, json_attrs, force_update
    )], True)


class RestSensor(Entity):
    """Implementation of a REST sensor."""

    def __init__(self, hass, rest, name, unit_of_measurement,
                 value_template, json_attrs, force_update):
        """Initialize the REST sensor."""
        self._hass = hass
        self.rest = rest
        self._name = name
        self._state = STATE_UNKNOWN
        self._unit_of_measurement = unit_of_measurement
        self._value_template = value_template
        self._json_attrs = json_attrs
        self._attributes = None
        self._force_update = force_update
        self.blokoutput = None
        self.status = namedtuple(
            'status', [LIVING_TEMP, BED_TEMP])

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self.rest.data is not None

    @property
    def state(self):
        """Return the state of the device."""

        return self._state

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    def update(self):
        """Get the latest data from REST API and update the state."""
        self.rest.update()
        #value = self.rest.data

        
        #self._attributes = self.rest.data
        if self.rest.data is not None:
            self.blokoutput = self.rest.data
            self._state = 'Connected'
        else:
            self.state = 'Disconnected'

    @property
    def device_state_attributes(self):
        """Return the state attributes of the monitored installation."""
       # _LOGGER.warning('This is getting called')
        if self.blokoutput is not None:
           # _LOGGER.warning('This is also getting called')
            return {
                BED_TEMP: self.blokoutput[5]['attributes']['currentTemperature']['value'],
                LIVING_TEMP: self.blokoutput[2]['attributes']['currentTemperature']['value'],
                BATH_TEMP: self.blokoutput[4]['attributes']['currentTemperature']['value'],
                BED_HUM: self.blokoutput[5]['attributes']['humidity']['value'],
                LIVING_HUM: self.blokoutput[2]['attributes']['humidity']['value'],
                BATH_HUM: self.blokoutput[4]['attributes']['humidity']['value'],
                BED_CO2: self.blokoutput[5]['attributes']['co2Level']['value'],
                LIVING_CO2: self.blokoutput[2]['attributes']['co2Level']['value'],
#                HALLWAY_MOT: self.blokoutput[1]['attributes']['presenceDetected']['value'],
		HALLWAY_MOT: 'false',
                LIVING_MOT: self.blokoutput[2]['attributes']['presenceDetected']['value'],
                BED_MOT: self.blokoutput[5]['attributes']['presenceDetected']['value'],
#                BATH_MOT: self.blokoutput[4]['attributes']['presenceDetected']['value'],
                KIT_MOT: self.blokoutput[3]['attributes']['presenceDetected']['value'],
                BATH_MOT: 'false',
                TOT_POW: self.blokoutput[0]['attributes']['totalPower']['value'],
            }
        else:
            self.state = 'Disconnected'


class RestData(object):
    """Class for handling the data retrieval."""

    def __init__(self, method, resource, auth, headers, data, verify_ssl, refresh_token):
        """Initialize the data object."""

        self.data = None
        self.resource = resource
        self.refresh_token = refresh_token

    def update(self):
        """Get the latest data from REST service with provided method."""

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        data= {
            'grant_type': 'refresh_token',
#            'refresh_token': 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJQTUp4R0FocWI2a1cxSVBHWUFicmNnUlNEamMzbUpKNUJFRzdfY1MzT3lZIn0.eyJqdGkiOiIxOWI0MDhlZC0zY2ViLTQ5ZTMtYjczZC0zZWM5OTJmZWQ2M2YiLCJleHAiOjAsIm5iZiI6MCwiaWF0IjoxNTI0Njc2MjY2LCJpc3MiOiJodHRwczovL2Jsb2s2MS5vcGVucmVtb3RlLmlvL2F1dGgvcmVhbG1zL2Jsb2s2MSIsImF1ZCI6Im9wZW5yZW1vdGUiLCJzdWIiOiJkOGM5N2QyMi04NDQ4LTRiZWItYTg0YS04N2M5Y2M2MWYzYWEiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoib3BlbnJlbW90ZSIsIm5vbmNlIjoiNmQ4YWQxZjgtMTczZS00MzViLThhMjAtNTgxMzIwZjQyMzhjIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiYTUyNzNhZDUtMGI0My00YWRjLWE5NmEtZjEyN2FjOWY2NjY3IiwiY2xpZW50X3Nlc3Npb24iOiIzYzJlZWY2NC05ODMwLTQwZWEtYTU1Ny1lYTMyZjY3NWVlM2EiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7Im9wZW5yZW1vdGUiOnsicm9sZXMiOlsid3JpdGU6YXNzZXRzIiwicmVhZDptYXAiLCJyZWFkOmFzc2V0cyIsIndyaXRlOnVzZXIiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJ2aWV3LXByb2ZpbGUiXX19fQ.LTxG9XSkZqNpF7pftmQfjla2gRk_nH2Avl0BVOqVt1mNr1rHpmzOrOdwQIBKEOSAFrRiOAftNji_yk3fdtwQxNnckDREbzjEnLB09mKxFW66GghBShHCvm2cmbGtoB7zd2AlaLbupfwjUi20GUSNBjFMeeJQzzvyG83etO2hssKR-TodDDydCLfl8kYsgqtpxGZuHtFLUQccVadStoXZ2iakgQjD0hnyFyivR0xKgj5SP7lU9sqRmirc2ir12VJv_iZmjcWKxeyuhXwU3F3zyCAE64Oty5ijxcMfpmw_CO_irq62hdaGIHEUDvb24kzn7t1DYm2hh_9p1TDLOXujkg',
            'client_id': 'openremote',
#            'refresh_token': 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJMby1yVjhnT3NuV0o3RnQ0MGk4WnJkOVY1TWF3ZEhqQVE1bmpWZl94YWhjIn0.eyJqdGkiOiI2MTUzODIxOC03YThjLTQ2OTYtYmMyOC04ZDYzODU2YTBiODQiLCJleHAiOjAsIm5iZiI6MCwiaWF0IjoxNTM5NzcyODQzLCJpc3MiOiJodHRwczovL2Jsb2s2MS5vcGVucmVtb3RlLmlvL2F1dGgvcmVhbG1zL2Jsb2s2MSIsImF1ZCI6Im9wZW5yZW1vdGUiLCJzdWIiOiJkZjU2ZmIyOS04ODI0LTQ1ZDctYTAxNS1mMmYxNTA3ZjAzMzEiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoib3BlbnJlbW90ZSIsIm5vbmNlIjoiYjMzMGIxYzktMGZkMC00NGEzLTg4MmEtODJkYTQ1OTMxOWM5IiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiNzUxMDY1MGMtM2IyOC00MmU2LWJhYjctZjYyNTAyNDRhMzAwIiwiY2xpZW50X3Nlc3Npb24iOiJiNjQ3MjQxZi00ZTc2LTQ2MWUtOTllNS0zNTg4YTZhMjIxNzEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7Im9wZW5yZW1vdGUiOnsicm9sZXMiOlsid3JpdGU6YXNzZXRzIiwicmVhZDptYXAiLCJyZWFkOmFzc2V0cyIsIndyaXRlOnVzZXIiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJ2aWV3LXByb2ZpbGUiXX19fQ.Sp_DaAeqEp4M5kdQzj231mQN0He8TRlzZibKnmuGitSMgRdwIr8TvgLiUNKHxt8TsnE0tYvpFelCKINVXTZj9Xs6l_XEeyRirIvRwDkYaDlWAHVDpElvBAihwXeXAXItBp5h_8VQMiaybFguLjxWi6ze47ITck9bCd_599PBap1rLpSQVFjfwDvoQVVWq2i9skBEZ8QwkgxgeDJVZVYymDofnzu72STC6o5BnqjhMHdPed8wC1TiJIbHggVP3geMrdk4FEL7JofIAfRTgdvkKDmsPI1YJXczJMmbv3cF_BxnGJ1wV9SXQ2QFzuQXYE-PjBivTPtJmjW0yQYxHaviSg'
#            'refresh_token': 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJSeV9SSksyZUo1cWVleXo2VzF5QlA4RGIxakdaQ0VnMm1iaFZua1BaSzBBIn0.eyJqdGkiOiI1NGZiNGUwZS00NGFjLTQzMTktYWM5MC1hM2U3ZDUyM2I0MTgiLCJleHAiOjAsIm5iZiI6MCwiaWF0IjoxNTQ1MTI3ODE3LCJpc3MiOiJodHRwczovL2Jsb2s2MS5vcGVucmVtb3RlLmlvL2F1dGgvcmVhbG1zL2Jsb2s2MSIsImF1ZCI6Im9wZW5yZW1vdGUiLCJzdWIiOiJmM2UwZDNiMy1mNzdiLTQ2ZGYtOTAzZi1mMTU3ZWZhYzEwNDgiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoib3BlbnJlbW90ZSIsIm5vbmNlIjoiMTBhOWY1ODMtYTA5NC00MGMzLTgxMDgtNzBiOGExN2VhZjBjIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiZDdjYzY5OGEtOWY3Yy00MTliLThkZWEtNmU1MjczMTQ4OGNhIiwiY2xpZW50X3Nlc3Npb24iOiI4MGMwYzk2NS0wNGZlLTRlZTItODRlOC0zNmY4NzEzZTExOWMiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7Im9wZW5yZW1vdGUiOnsicm9sZXMiOlsid3JpdGU6YXNzZXRzIiwicmVhZDptYXAiLCJyZWFkOmFzc2V0cyIsIndyaXRlOnVzZXIiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJ2aWV3LXByb2ZpbGUiXX19fQ.RJdbPDFhbTEBnwlMXzqSE8cT8mHRWClhfg-L4k1TuoOliCudkLfkLy--McPcxI_Kx4zxPpMpujeaKF4DZGP9cm8RRWZBWNT77DNf9lWYReWJbSwN4ptvoVUry6N7leOsdFnrVVYFpsOQbfjYeTXWf5z0_GmD7KPYyD0CM7vQgSyFlCJZB8NmZcZk9L-TDBCKVkERh2EtLQ1tFH49KXS8OkFBcmQ7HDzAJsvWYQ3EJX57uSAXKlpw2KjqeeAMMHECPeMS41uakMaJNnc_TW5qUXudrGib0B0d7MKpOdMROBH7-xK1vhzeNOogIfOgKBKRD96ng5PCHkGGAWzFQ4aDCQ'
             'refresh_token': self.refresh_token
            }
        r = requests.post('https://blok61.openremote.io/auth/realms/blok61/protocol/openid-connect/token', data=data, headers = headers)

        access_token = r.json()['access_token']

        data= {
          "select": {
            "include": "ALL"
          },
          "userId": "d8c97d22-8448-4beb-a84a-87c9cc61f3aa"
        }

        headers = {'Authorization' : 'Bearer ' + access_token, 'Content-Type': 'application/json; charset=utf-8'}

        data=json.dumps(data)

        self._request = requests.Request(
            'POST', self.resource, headers=headers, data=data).prepare()
        self._verify_ssl = True

        try:
            with requests.Session() as sess:
                response = sess.send(
                    self._request, timeout=10, verify=self._verify_ssl)

            #_LOGGER.info(response.text)
            self.data = response.json()
        except requests.exceptions.RequestException:
            _LOGGER.error("Error fetching data: %s", self._request)
            self.data = None
