import os
import logging
import pandas as pd

# Configured in inventory/inventory.py
from inventory.inventory import odelog
from inventory.scripts.python.wrappers import odeReadParquet, odeWriteParquet


input_files = [
    ("datatype", "OGD/AMS", "Abgemeldete-RGS_MW_AG_Dauer")
]
output_files = [
    ("enrich", "OGD/AMS", "Abgemeldete-BL_MW_AG_Dauer")
]

# -----------------------------------------------------------------
# Run script in simulation mode. Terminates script after execution
# -----------------------------------------------------------------
# handle_simulation_mode(input_files, output_files)


# -----------------------------------------------------------------
# Run script from command line
# -----------------------------------------------------------------

def main() -> None:
    """
    Enrich Abgang dataset with Bundesland and NUTS2 information.
    
    Features:
    - Add Bundesland and NUTS2 metadata
    - Aggregate over RGS into Bundesland
    """
    # Dicts to handle Bundesland and NUTS2
    AT_NUTS2 = {
        'AT11':'Burgenland', 'AT12': 'Niederösterreich', 'AT13': 'Wien', 
        'AT21': 'Kärnten', 'AT22':'Steiermark', 'AT31': 'Oberösterreich',
        'AT32': 'Salzburg', 'AT33': 'Titol', 'AT34': 'Vorarlberg'
    }
    AT_idBundesland = {
        '1':'Burgenland', 
        '2':'Kärnten',
        '3':'Niederösterreich',
        '4':'Oberösterreich',
        '5':'Salzburg',
        '6':'Steiermark',
        '7':'Innsbruck',
        '8':'Vorarlberg',
        '9':'Wien',
    }
    
    # ============================================================================
    # Read Input
    # ============================================================================
    input_path = f'{os.getenv("DATA_ROOT_DIR")}/{"/".join(input_files[0])}.parquet'
    odelog.info(f'Reading: {input_path}')
    dp = odeReadParquet(input_path)
    odelog.debug(f'Input DataFrame info:\n{dp.info()}')

    # ============================================================================
    # Datatype transforms
    # ============================================================================    
    # Add some features
    dp['gesamtAnzahlTageAMS'] = dp['Abgemeldete'] * dp['mittlereGemeldetTage']
    dp['idBundesland'] = dp['idRGS'].astype(str).str[0]

    # Construct dataframes from dicts for joins
    dn = pd.DataFrame(AT_NUTS2.items(), columns=['NUTS2','Bundesland'])
    da = pd.DataFrame(AT_idBundesland.items(), columns=['idBundesland','Bundesland'])

    # Add lookup fields for Bundesland and NUTS2
    dj = (dp.join(da.set_index('idBundesland'), on='idBundesland')
            .join(dn.set_index('Bundesland'), on='Bundesland'))
    dj['Bundesland'] = dj['Bundesland'].astype('category')
    dj['NUTS2'] = dj['NUTS2'].astype('category')

    # Group and aggregate data
    dg = dj.groupby(
        ['Datum', 'Bundesland', 'NUTS2', 'Geschlecht', 'idxAltersGruppe', 
         'AltersGruppe', 'idxGemeldetZeitSpanne', 'gemeldetZeitSpanne'],
        observed=True
    )
    db = dg[['Abgemeldete', 'gesamtAnzahlTageAMS']].sum().reset_index()
    odelog.debug(f'Aggregated DataFrame shape: {db.shape}')

    # ============================================================================
    # Persist data
    # ============================================================================
    output_path = f'{os.getenv("DATA_ROOT_DIR")}/{"/".join(output_files[0])}.parquet'
    odelog.info(f'Writing: {output_path}')
    odeWriteParquet(db, output_path)
    odelog.info(f'Data written to {output_path}')

if __name__ == "__main__":
    main()