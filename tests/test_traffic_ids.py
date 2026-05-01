from ids.traffic_ids import TrafficIDS


def test_both_green_returns_ok():
    ids = TrafficIDS()
    result = ids.check(ir_red=False, mqtt_red=False)
    assert result["status"] == "ok"


def test_both_red_returns_ok():
    ids = TrafficIDS()
    result = ids.check(ir_red=True, mqtt_red=True)
    assert result["status"] == "ok"


def test_ir_green_mqtt_red_mismatch_is_intrusion():
    ids = TrafficIDS()
    result = ids.check(ir_red=False, mqtt_red=True)
    assert result["status"] == "intrusion"
    assert result["attack_type"] == "ir_spoof"


def test_ir_red_mqtt_green_mismatch_is_intrusion():
    ids = TrafficIDS()
    result = ids.check(ir_red=True, mqtt_red=False)
    assert result["status"] == "intrusion"
    assert result["attack_type"] == "mqtt_spoof"
