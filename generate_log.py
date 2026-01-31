import os
import random
import datetime
import time

def ensure_dir(directory):
    """Ensure that the directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

# === Simulation Data Configuration ===
# Updated models to match generate_data.py for consistent RAG analysis
LOG_DIR = "data/logs"
MODELS = ["Model_Pro", "Model_Cool", "Model_Entry"]
FIRMWARE_VERSIONS = ["v2.0.1", "v2.1.0", "v2.1.1"]

# Error codes mapped by category
ERROR_CODES = {
    "BMS": ["E-301: Cell Imbalance", "E-304: Thermal Runaway Warning", "E-310: Sensor Timeout"],
    "ADAS": ["E-505: Lidar Calibration Fail", "E-509: Camera Obstruction"],
    "MFG": ["E-102: Torque Wrench Timeout", "E-105: Robot Arm Sync Error"]
}

# Responsible Engineering Teams (Used for Agent to suggest Owner assignment)
OWNERS = {
    "BMS": "Battery_R&D_Team (Lead: Sarah)",
    "ADAS": "AI_Vision_Team (Lead: Mike)",
    "MFG": "Process_Engineering (Lead: Alex)",
    "INFRA": "DevOps_SRE (Lead: Jason)"
}

def generate_timestamp(base_time, offset_minutes):
    """Generates an incremental timestamp based on a start time and offset."""
    delta = datetime.timedelta(minutes=offset_minutes)
    return (base_time + delta).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def create_station_logs(num_lines=200):
    """
    Generates production line test station logs (Station Logs).
    Simulates the EOL (End of Line) testing process of the machine.
    """
    filename = os.path.join(LOG_DIR, "station_eol_test.log")
    base_time = datetime.datetime.now() - datetime.timedelta(days=7)

    print(f"Generating {filename}...")

    with open(filename, 'w', encoding='utf-8') as f:
        # Write Header
        f.write("=== FACTORY EOL TEST STATION #42 LOGS ===\n")
        f.write("Station_ID: TS-42-B\n")
        f.write("Location: Zone C, Final Assembly\n")
        f.write("------------------------------------------------\n")

        for i in range(num_lines):
            # [UPDATED] Use the new MODELS list to generate consistent VIN prefixes
            model_name = random.choice(MODELS)
            # Map model name to a VIN code (e.g., Model_Pro -> P, Model_Cool -> C)
            model_code = model_name.split("_")[1][0]

            seq = random.randint(1000, 9999)
            vin = f"EV2025{model_code}{seq}"

            # Determine if this log entry is a pass or fail (Simulating 15% failure rate)
            is_error = random.random() < 0.15
            fw = random.choice(FIRMWARE_VERSIONS)

            # Generate timestamp: approx 1 car every 5 minutes
            ts = generate_timestamp(base_time, i * 5)

            if is_error:
                # Generate an error scenario
                category = random.choice(["BMS", "ADAS", "MFG"])
                err_msg = random.choice(ERROR_CODES[category])
                owner = OWNERS[category]

                # Embed specific bug descriptions for RAG analysis to detect patterns
                if fw == "v2.1.0" and category == "BMS":
                    # Specifically embed: v2.1.0 battery issue (Root Cause candidate)
                    detail = "CRITICAL: Voltage drift detected > 50mV during high-load test. Suspect firmware regression in current control loop."
                elif category == "ADAS":
                    detail = "WARNING: Calibration matrix checksum mismatch. Sensor alignment required."
                else:
                    detail = "ERROR: Actuator response delay exceeded 200ms threshold."

                log_entry = (
                    f"[{ts}] [ERROR] [VIN: {vin}] [Model: {model_name}] [FW: {fw}] "
                    f"Test_Sequence_ID: {random.randint(100000, 999999)} "
                    f"| Code: {err_msg} | Detail: {detail} "
                    f"| Action: Flagged for Rework | Assigned_To: {owner}\n"
                )
            else:
                # Success Log
                log_entry = (
                    f"[{ts}] [INFO ] [VIN: {vin}] [Model: {model_name}] [FW: {fw}] "
                    f"Test_Sequence_ID: {random.randint(100000, 999999)} "
                    f"| Status: PASS | Cycle_Time: {random.randint(45, 60)}s "
                    f"| Uploaded to cloud: OK\n"
                )

            f.write(log_entry)

            # Occasionally insert system logs from the machine itself
            if random.random() < 0.05:
                sys_ts = generate_timestamp(base_time, i * 5 + 1)
                f.write(f"[{sys_ts}] [SYSTEM] Memory Usage: 45%, CPU Load: 12%. Garbage collection completed.\n")

def create_server_logs(num_lines=100):
    """
    Generates backend server logs (Server Logs).
    Simulates issues with software update servers or databases.
    """
    filename = os.path.join(LOG_DIR, "server_syslogs.log")
    base_time = datetime.datetime.now() - datetime.timedelta(days=7)

    print(f"Generating {filename}...")

    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            # Generate a few entries per hour
            ts = generate_timestamp(base_time, i * 60)
            level = random.choice(["INFO", "INFO", "WARN", "ERROR"])

            if level == "INFO":
                msg = "Batch processing completed. 500 records synced."
            elif level == "WARN":
                msg = "High latency detected in us-west-2 region API endpoint (2045ms)."
            else:
                # Embed errors related to firmware OTA (Over-The-Air) updates
                err_type = random.choice([
                    "DatabaseDeadlock",
                    "OTA_Package_Corrupt",
                    "AuthTokenExpired"
                ])

                if err_type == "OTA_Package_Corrupt":
                    msg = (
                        f"Exception: {err_type} | Target: Firmware v2.1.0 "
                        "| Hash mismatch during distribution. "
                        "Impact: 1500 vehicles may download invalid update bundle. "
                        f"Owner: {OWNERS['INFRA']}"
                    )
                else:
                    msg = f"Exception: {err_type} | Connection reset by peer. Retrying..."

            f.write(f"{ts} {level} [Service: OTA-Manager] [Thread-{random.randint(1,9)}] - {msg}\n")

if __name__ == "__main__":
    ensure_dir(LOG_DIR)
    create_station_logs()
    create_server_logs()
    print(f"✅ Log generation complete. Files saved in '{LOG_DIR}/'")