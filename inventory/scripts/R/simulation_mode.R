handle_simulation_mode <- function(inFiles, outFiles) {
    # Check if simulation mode is enabled
    if (tolower(Sys.getenv("AIR_SIMULATION_MODE", "false")) == "true") {
        # Immediately exit the script
        quit(save = "no", status = 0)
    }
}