"""Tests for dashboard app — reset endpoint and alert state."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
import json


@patch("dashboard.app.start_mqtt_listener")
@patch("dashboard.app.start_ids_service")
def test_reset_post_from_localhost_works(mock_ids, mock_mqtt):
    from dashboard.app import app, state, socketio
    app.config["TESTING"] = True
    client = app.test_client()

    state["car_status"] = "INTRUSION"
    state["alerts"] = [{"type": "test"}]

    response = client.post("/reset", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200
    assert state["car_status"] == "SAFE"
    assert state["alerts"] == []


@patch("dashboard.app.start_mqtt_listener")
@patch("dashboard.app.start_ids_service")
def test_reset_get_method_not_allowed(mock_ids, mock_mqtt):
    from dashboard.app import app
    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get("/reset")
    assert response.status_code == 405
