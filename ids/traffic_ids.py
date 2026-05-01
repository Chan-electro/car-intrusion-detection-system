"""Traffic signal dual-verify mismatch detection."""


class TrafficIDS:
    def check(self, ir_red: bool, mqtt_red: bool) -> dict:
        if ir_red == mqtt_red:
            return {"status": "ok", "attack_type": None}

        if ir_red and not mqtt_red:
            attack_type = "mqtt_spoof"
        else:
            attack_type = "ir_spoof"

        return {"status": "intrusion", "attack_type": attack_type}
