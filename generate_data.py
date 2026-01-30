import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set random seed for reproducibility (so your demo yields the same results every time)
np.random.seed(42)
random.seed(42)

def generate_ev_data(num_cars=300):
    # --- 1. Define Basic Parameters ---
    models = ['Model_Pro', 'Model_Cool', 'Model_Entry'] # Pro=Flagship, Cool=Mid-range, Entry=Entry-level
    firmwares = ['v2.0.1 (Stable)', 'v2.1.0 (New_Feature)', 'v2.1.1 (Patch)']
    lines = ['Line_A (High_Speed)', 'Line_B (Precision)']
    
    start_date = datetime(2025, 1, 1)
    
    data_manufacturing = []
    data_performance = []
    data_issues = []

    print(f"Generating synthetic data for {num_cars} vehicles...")

    for i in range(num_cars):
        # Randomly assign a vehicle model
        model = np.random.choice(models, p=[0.2, 0.5, 0.3])
        vin = f"EV{2025}{model[0]}{i:04d}" # Generate a unique Vehicle Identification Number (VIN)
        
        # --- Manufacturing Data ---
        # Simulation: Model_Pro is more complex, thus takes longer to manufacture
        base_time_hours = 24 if model == 'Model_Pro' else 16
        manufacturing_start = start_date + timedelta(days=np.random.randint(0, 90))
        
        # Add random manufacturing variation (simulating factory efficiency fluctuations)
        delay = np.random.exponential(scale=2) 
        total_build_time = base_time_hours + delay
        
        # Simulate a 5% manufacturing failure rate (requiring rework)
        completion_status = 'Success'
        if np.random.random() < 0.05:
            completion_status = 'Rework_Needed'
            
        data_manufacturing.append({
            "VIN": vin,
            "Model": model,
            "Production_Line": np.random.choice(lines),
            "Start_Time": manufacturing_start.strftime("%Y-%m-%d %H:%M"),
            "End_Time": (manufacturing_start + timedelta(hours=total_build_time)).strftime("%Y-%m-%d %H:%M"),
            "Labor_Hours": round(total_build_time * 1.2, 1), # Simulate labor input
            "Status": completion_status,
            "Shift": np.random.choice(['Day', 'Night']),
            "Supervisor": np.random.choice(['Lead_Smith', 'Lead_Chen', 'Lead_Johnson'])
        })

        # --- Software & Performance Data ---
        # **Key Insight Embedding**: v2.1.0 on Model_Cool has a risk of battery overheating
        fw = np.random.choice(firmwares, p=[0.4, 0.4, 0.2]) 
        
        # Basic State of Health (SoH) for the battery
        soh = np.random.normal(98, 1.5) 
        if soh > 100: soh = 100
        
        # Embed anomaly logic: If firmware is v2.1.0 and model is Model_Cool, SoH is lower
        if fw == 'v2.1.0 (New_Feature)' and model == 'Model_Cool':
            soh -= np.random.uniform(2, 6) # Significant performance degradation

        # System stability (Reboot Count)
        reboot_count = np.random.poisson(0.2)
        # v2.1.0 is less stable
        if fw == 'v2.1.0 (New_Feature)':
            reboot_count += np.random.randint(0, 3)

        data_performance.append({
            "VIN": vin,
            "Firmware_Version": fw,
            "Battery_SoH": round(soh, 2),
            "Avg_Range_Efficiency_kWh_100km": round(np.random.normal(16, 2), 1),
            "Sensor_Calibration_Score": round(np.random.normal(95, 3), 1), # Score from 0-100
            "System_Reboot_Count": reboot_count,
            "Battery_Temp_Avg": round(np.random.normal(32, 4), 1)
        })

        # --- Quality Issue Log ---
        # Logic: Generate a ticket if manufacturing status is Rework or performance data is poor
        if completion_status == 'Rework_Needed' or reboot_count > 2 or soh < 92:
            issue_type = np.random.choice(['Software_Bug', 'Assembly_Gap', 'Paint_Defect', 'Battery_Module'])
            severity = 'Critical' if reboot_count > 3 else 'Major'
            
            data_issues.append({
                "Issue_ID": f"ISS-{np.random.randint(10000,99999)}",
                "VIN": vin,
                "Reported_Date": (manufacturing_start + timedelta(days=np.random.randint(1,5))).strftime("%Y-%m-%d"),
                "Category": issue_type,
                "Severity": severity,
                "Resolution_Time_Hours": np.random.randint(4, 48)
            })

    # Output to CSV
    pd.DataFrame(data_manufacturing).to_csv('data/factory_manufacturing.csv', index=False)
    pd.DataFrame(data_performance).to_csv('data/vehicle_performance.csv', index=False)
    pd.DataFrame(data_issues).to_csv('data/quality_issues.csv', index=False)
    
    print("Success! 3 CSV files generated in 'data/' folder.")

if __name__ == "__main__":
    generate_ev_data()