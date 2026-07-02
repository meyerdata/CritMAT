import argparse
import os
from critmat.calculations import get_data
from critmat.calculations import hhi_basic,hhi_wgi,hhi_wgi_tp

'''
This script handles the calculation of the Herfindahl-Hirschman Index (HHI).
It calls the required data and the appropriate HHI calculation function based on the provided command-line arguments.
'''
def main():
    parser = argparse.ArgumentParser(description='Calculate HHI with optional WGI and trade parameters')
    parser.add_argument('--eu_trade', action='store_true', help='Use EU trade data instead of world production data')
    parser.add_argument('--wgi', action='store_true', help='Include world governance index data')
    parser.add_argument('--tradeparameters', action='store_true', help='Include trade parameter data (requires --wgi)')
    parser.add_argument('--timeframe', nargs='+', type=int, default=None, help='Timeframe on which production is aggregated (Default: None, which means no aggregation)')
    parser.add_argument('--timeframe_preset', type=str, default=None, help='Timeframe preset to use (Default: None, Example: EU2023)')
    parser.add_argument('--output_dir', type=str, default='output_data', help='Directory to save output files')

    args = parser.parse_args()
    
    # Get the production or trade data based on the --eu_trade flag. If --eu_trade is set, we use EU trade data; otherwise, we use world production data.
    if args.eu_trade:   
        prod_data = get_data('supply')  
    else:
        prod_data = get_data('production')

    # If a timeframe preset is provided, we set the timeframe accordingly. If no preset is provided, we use the custom timeframe specified by the user.
    if args.timeframe_preset:
        if args.timeframe_preset == "EU2023":
            print("Using EU2023 timeframe preset: 2016-2020")
            args.timeframe = [2016, 2017, 2018, 2019, 2020]
        else:
            print(f"Unknown timeframe preset: {args.timeframe_preset}. Please provide a valid preset or specify a custom timeframe.")
            return

    # Get the WGI and trade parameter data if the corresponding flags are set. If the flags are not set, we do not retrieve this data.
    wgi_data = get_data('wgi') if args.wgi else None
    tradeparameters = get_data('tradeparameters') if args.tradeparameters else None

    # Determine which HHI calculation function to call based on the provided flag.
    if args.wgi and args.tradeparameters:
        print("Calculating HHI with WGI and trade parameters")
        result = hhi_wgi_tp(prod_data, wgi_data, tradeparameters,timeframe=args.timeframe)
    elif args.wgi:
        print("Calculating HHI with WGI (no trade parameters)")
        result = hhi_wgi(prod_data, wgi_data,timeframe=args.timeframe)    
    else:
        print("Calculating basic HHI (no WGI, no trade parameters)")
        result = hhi_basic(prod_data,timeframe=args.timeframe)

    # Error handling
    if result is None:
        print("Please check the arguments provided. Ensure that the required data is available and the correct flags are set.")
    else:
        print("Calculation completed successfully.")

    # Save the results to a CSV file in the specified output directory. If the directory does not exist, it will be created.
    output_path = os.path.join(args.output_dir, f'hhi_results.csv')
    result.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()