import argparse
import os
from critmat.calculations import get_data
from critmat.calculations import supply_risk_eu

'''
This script handles the calculation of the Herfindahl-Hirschman Index (HHI).
It calls the required data and the appropriate HHI calculation function based on the provided command-line arguments.
'''
def main():
    parser = argparse.ArgumentParser(description='Perform supply risk assessment')
    parser.add_argument('--eu', action='store_true', help='Use EU trade data instead of world production data')
    parser.add_argument('--timeframe', nargs='+', type=int, default=[2020, 2021, 2022, 2023, 2024], help='Timeframe on which production is aggregated (Default: WMD2026 preset 2020-2024)')
    parser.add_argument('--timeframe_preset', type=str, default=None, help='Timeframe preset to use (Default: None, Example: EU2023, WMD2026)')
    parser.add_argument('--output_dir', type=str, default='output_data', help='Directory to save output files')

    args = parser.parse_args()
    
    #Get all required data from the database
    prod_data = get_data('production')
    supply_data = get_data('supply')  
    wgi_data = get_data('wgi') 
    tradeparameters_data = get_data('tradeparameters')
    eureport_data = get_data('eureport')

    # Check that every required dataset was retrieved
    missing = []
    if prod_data is None:
        missing.append('production')
    if supply_data is None:
        missing.append('supply')
    if wgi_data is None:
        missing.append('wgi')
    if tradeparameters_data is None:
        missing.append('tradeparameters')
    if eureport_data is None:
        missing.append('eureport')

    if missing:
        print(
            "Error: The following required dataset(s) could not be retrieved: "
            + ", ".join(missing)
            + ". Please check the uploaded data."
        )
        return

    # If a timeframe preset is provided, we set the timeframe accordingly. If no preset is provided, we use the custom timeframe specified by the user.
    if args.timeframe_preset:
        if args.timeframe_preset == "EU2023":
            print("Using EU2023 timeframe preset: 2016-2020")
            args.timeframe = [2016, 2017, 2018, 2019, 2020]
        elif args.timeframe_preset == "WMD2026":
            print("Using WMD2026 timeframe preset: 2020-2024")
            args.timeframe = [2020, 2021, 2022, 2023, 2024]
        else:
            print(f"Unknown timeframe preset: {args.timeframe_preset}. Please provide a valid preset or specify a custom timeframe.")
            return

    result = supply_risk_eu(prod_data, supply_data, wgi_data, eureport_data, tradeparameters_data, timeframe=args.timeframe)

    # Error handling
    if result is None:
        print("Please check the arguments provided. Ensure that the required data is available and the correct flags are set.")
        return
    else:
        print("Calculation completed successfully.")

    # Save the results to a CSV file in the specified output directory. If the directory does not exist, it will be created.
    output_path = os.path.join(args.output_dir, f'assessment_results.csv')
    result.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()