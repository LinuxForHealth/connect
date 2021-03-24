"""
test_fhir.py
Tests the /fhir endpoint
"""
import pytest
from pyconnect import clients
from pyconnect.config import get_settings
from pyconnect.workflows.fhir import FhirWorkflow
from starlette.responses import Response
import asyncio


@pytest.fixture
def encounter_fixture():
    return {
            'resourceType': 'Encounter',
            'id': 'emerg',
            'text': {
                'status': 'generated',
                'div': '\u003cdiv xmlns\u003d\'http://www.w3.org/1999/xhtml\'\u003eEmergency visit that escalated into inpatient patient @example\u003c/div\u003e'
            },
            'status': 'in-progress',
            'statusHistory': [
                {
                    'status': 'arrived',
                    'period': {
                        'start': '2017-02-01T07:15:00+10:00',
                        'end': '2017-02-01T07:35:00+10:00'
                    }
                },
                {
                    'status': 'triaged',
                    'period': {
                        'start': '2017-02-01T07:35:00+10:00',
                        'end': '2017-02-01T08:45:00+10:00'
                    }
                },
                {
                    'status': 'in-progress',
                    'period': {
                        'start': '2017-02-01T08:45:00+10:00',
                        'end': '2017-02-01T12:15:00+10:00'
                    }
                },
                {
                    'status': 'onleave',
                    'period': {
                        'start': '2017-02-01T12:15:00+10:00',
                        'end': '2017-02-01T12:45:00+10:00'
                    }
                },
                {
                    'status': 'in-progress',
                    'period': {
                        'start': '2017-02-01T12:45:00+10:00'
                    }
                }
            ],
            'class': {
                'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                'code': 'IMP',
                'display': 'inpatient encounter'
            },
            'classHistory': [
                {
                    'class': {
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                        'code': 'EMER',
                        'display': 'emergency'
                    },
                    'period': {
                        'start': '2017-02-01T07:15:00+10:00',
                        'end': '2017-02-01T09:27:00+10:00'
                    }
                },
                {
                    'class': {
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                        'code': 'IMP',
                        'display': 'inpatient encounter'
                    },
                    'period': {
                        'start': '2017-02-01T09:27:00+10:00'
                    }
                }
            ],
            'subject': {
                'reference': 'Patient/example'
            },
            'period': {
                'start': '2017-02-01T07:15:00+10:00'
            },
            'hospitalization': {
                'admitSource': {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/admit-source',
                            'code': 'emd',
                            'display': 'From accident/emergency department'
                        }
                    ]
                }
            },
            'location': [
                {
                    'location': {
                        'display': 'Emergency Waiting Room'
                    },
                    'status': 'active',
                    'period': {
                        'start': '2017-02-01T07:15:00+10:00',
                        'end': '2017-02-01T08:45:00+10:00'
                    }
                },
                {
                    'location': {
                        'display': 'Emergency'
                    },
                    'status': 'active',
                    'period': {
                        'start': '2017-02-01T08:45:00+10:00',
                        'end': '2017-02-01T09:27:00+10:00'
                    }
                },
                {
                    'location': {
                        'display': 'Ward 1, Room 42, Bed 1'
                    },
                    'status': 'active',
                    'period': {
                        'start': '2017-02-01T09:27:00+10:00',
                        'end': '2017-02-01T12:15:00+10:00'
                    }
                },
                {
                    'location': {
                        'display': 'Ward 1, Room 42, Bed 1'
                    },
                    'status': 'reserved',
                    'period': {
                        'start': '2017-02-01T12:15:00+10:00',
                        'end': '2017-02-01T12:45:00+10:00'
                    }
                },
                {
                    'location': {
                        'display': 'Ward 1, Room 42, Bed 1'
                    },
                    'status': 'active',
                    'period': {
                        'start': '2017-02-01T12:45:00+10:00'
                    }
                }
            ],
            'meta': {
                'tag': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActReason',
                        'code': 'HTEST',
                        'display': 'test health data'
                    }
                ]
            }
    }


@pytest.mark.asyncio
async def test_fhir_post(async_test_client,
                         encounter_fixture,
                         mock_async_kafka_producer,
                         monkeypatch,
                         settings):
    """
    Tests /fhir [POST] where data is not transmitted to an external server
    :param async_test_client: HTTPX test client fixture
    :param encounter_fixture: FHIR R4 Encounter Resource fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: pyConnect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(clients, 'ConfluentAsyncKafkaProducer', mock_async_kafka_producer)

        async with async_test_client as ac:
            # remove external server setting
            settings.fhir_r4_externalserver = None
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post('/fhir/Encounter', json=encounter_fixture)

        assert actual_response.status_code == 200

        actual_json = actual_response.json()
        assert 'uuid' in actual_json
        assert 'creation_date' in actual_json
        assert 'store_date' in actual_json
        assert 'transmit_date' in actual_json
        assert 'target_endpoint_url' in actual_json
        assert 'elapsed_storage_time' in actual_json
        assert 'elapsed_transmit_time' in actual_json
        assert 'elapsed_total_time' in actual_json

        assert actual_json['consuming_endpoint_url'] == '/fhir'
        assert actual_json['data_format'] == 'ENCOUNTER'
        assert actual_json['status'] == 'success'
        assert actual_json['data_record_location'] == 'ENCOUNTER:0:0'


@pytest.mark.asyncio
async def test_fhir_post_with_transmit(async_test_client,
                                       encounter_fixture,
                                       mock_async_kafka_producer,
                                       monkeypatch,
                                       settings):
    """
    Tests /fhir [POST] with an external FHIR server defined.
    :param async_test_client: HTTPX test client fixture
    :param encounter_fixture: FHIR R4 Encounter Resource fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: pyConnect configuration settings
    """

    async def mock_workflow_transmit(self, response: Response):
        """
        A mock workflow transmission method used to set a response returned to a client
        """
        await asyncio.sleep(.1)
        response.status_code = 201
        response.headers['location'] = 'fhir/v4/Patient/5d7dc79a-faf2-453d-9425-a0efe85032ea/_history/1'
        self.use_response = True

    with monkeypatch.context() as m:
        m.setattr(clients, 'ConfluentAsyncKafkaProducer', mock_async_kafka_producer)
        m.setattr(FhirWorkflow, 'transmit', mock_workflow_transmit)

        async with async_test_client as ac:
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings
            actual_response = await ac.post('/fhir/Encounter', json=encounter_fixture)

            assert actual_response.status_code == 201
            assert actual_response.text == ''
            assert 'location' in actual_response.headers


@pytest.mark.asyncio
async def test_fhir_post_endpoints(async_test_client,
                                   encounter_fixture,
                                   mock_async_kafka_producer,
                                   monkeypatch,
                                   settings):
    """
    Tests /fhir [POST] endpoints to ensure that 404 and 422 status codes are returned when appropriate
    :param async_test_client: HTTPX test client fixture
    :param encounter_fixture: FHIR R4 Encounter Resource fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: pyConnect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(clients, 'ConfluentAsyncKafkaProducer', mock_async_kafka_producer)

        async with async_test_client as ac:
            # remove external server setting
            settings.fhir_r4_externalserver = None
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post('/fhir/Encounter', json=encounter_fixture)
            assert actual_response.status_code == 200

            actual_response = await ac.post('/fhir/encounter', json=encounter_fixture)
            assert actual_response.status_code == 404

            encounter_fixture['resourceType'] = 'Patient'
            actual_response = await ac.post('/fhir/Encounter', json=encounter_fixture)
            assert actual_response.status_code == 422
