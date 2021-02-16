"""
test_data.py
Tests /data endpoints
"""


def test_get_data_record(test_client):
    """
    Tests /data?dataFormat=x&partition=0&offset=0
    """
    actual_response = test_client.get('/data',
                                      params={
                                          'dataformat': 'EXAMPLE',
                                          'partition': 100,
                                          'offset': 4561
                                      })
    assert actual_response.status_code == 200

    actual_json = actual_response.json()
    assert actual_json['data_record_location'] == 'EXAMPLE:100:4561'
