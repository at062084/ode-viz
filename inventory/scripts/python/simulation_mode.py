def handle_simulation_mode(inFiles, outFiles):
    """
    Handle simulation mode for data processing scripts.
    Uses standard wrappers with simulation mode.
    """
    import sys
    import os

    global odeReadParquet, odeWriteParquet
    
    if (os.getenv("AIR_SIMULATION_MODE") == "true"):
        # Exit the script
        sys.exit(0)