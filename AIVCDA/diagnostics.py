import psutil
import platform
try:
    import wmi
    import pythoncom
except ImportError:
    wmi = None
    pythoncom = None

def get_health_report():
    """Returns a formatted string describing system CPU, RAM and Temp."""
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    
    # Attempt to get WMI Temperatures. (Often requires Admin and specific MBs)
    temp_info = ""
    if wmi is not None:
        try:
            w = wmi.WMI(namespace="root\\wmi")
            # MSAcpi_ThermalZoneTemperature gives temp in tenths of degrees Kelvin
            temperatures = w.MSAcpi_ThermalZoneTemperature()
            if len(temperatures) > 0:
                kelvin_tenth = temperatures[0].CurrentTemperature
                celsius = (kelvin_tenth / 10.0) - 273.15
                temp_info = f" Core temperature is {celsius:.1f} degrees celsius."
        except Exception:
            pass # Fails gracefully if no admin privileges or unsupported
            
    report = f"CPU utilization is at {cpu_percent} percent. Memory usage is at {ram_percent} percent." + temp_info
    return report

def check_abnormal_levels():
    """
    Checks if CPU or RAM usage > 90%.
    Returns (True, "reason") if dangerous, else (False, "").
    """
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # Check CPU Temp if possible
    if wmi is not None:
        try:
            if pythoncom: pythoncom.CoInitialize()
            w = wmi.WMI(namespace="root\\wmi")
            temperatures = w.MSAcpi_ThermalZoneTemperature()
            if len(temperatures) > 0:
                celsius = (temperatures[0].CurrentTemperature / 10.0) - 273.15
                if celsius > 85.0: # 85C is quite hot
                    return True, "abnormal CPU temperature detected"
        except Exception:
            pass

    if cpu > 92.0:
        return True, "abnormal CPU load detected"
    if ram > 92.0:
        return True, "abnormal memory usage detected"
        
    return False, ""
