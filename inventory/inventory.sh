
# This script is the bootstrap loader for Rscripts in the inventory
# It is the only file in the inventory directly sourced by R scripts

# Its default location is in /export/inventory
# this may be overridden by setting the INVENTORY_ROOT_DIR shell variable

# Global variables. Currently contains mainly data layers
source $INVENTORY_ROOT_DIR/config/ode/globals.sh
source $INVENTORY_ROOT_DIR/scripts/utils.sh
