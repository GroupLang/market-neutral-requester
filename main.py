import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import logging
import pandas_market_calendars as mcal
from src.scripts.sector_market_pipeline import sector_market_pipeline
from multiprocessing import Pool
import multiprocessing

logger = logging.getLogger(__name__)

def get_trading_days(start_date, end_date):
    # Get NYSE calendar
    nyse = mcal.get_calendar('NYSE')
    
    # Get trading days
    trading_days = nyse.valid_days(start_date=start_date, end_date=end_date)
    
    # Convert to string format YYYY-MM-DD
    return [day.strftime('%Y-%m-%d') for day in trading_days]

def process_sector(args):
    market, date, sector = args
    logger.info(f"Processing sector: {sector} on date: {date}")
    try:
        decisions = sector_market_pipeline(market, date, sector)
        df = pd.DataFrame(decisions)
        return df
    except Exception as e:
        logger.error(f"The pipeline raised the following error for {sector}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def get_latest_date_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'date' in df.columns:
            return df['date'].max()
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def main():
    try:
        market = "sp500"
        
        # Get input file path from environment variable or use default
        input_file = os.environ.get("INPUT_FILE", "data/gpt_raw_decisions_o1.csv")
        
        # Get latest date from the input file
        latest_date = get_latest_date_from_csv(input_file)
        if latest_date is None:
            logger.error("Could not get latest date from input file")
            return
            
        start_date = latest_date
        end_date = datetime.today().strftime('%Y-%m-%d')
        trading_days = get_trading_days(start_date, end_date)
        
        # Get the two trading days before the latest date
        if not trading_days:
            logger.info(f"No trading days found between {start_date} and {end_date}")
            return
            
        # Take only the first two trading days (if available)
        trading_days = trading_days[1:-2]
        logger.info(f"Processing trading days: {trading_days}")
            
        # Get unique sectors from SP500 data
        sectors = [
            "Information Technology",
            "Communication Services", 
            "Consumer Discretionary",
            "Consumer Staples",
            "Energy",
            "Financials",
            "Health Care",
            "Industrials",
            "Materials",
            "Real Estate",
            "Utilities"
        ]

        # Set up multiprocessing pool
        num_cores = 6  # Leave one core free
        pool = Pool(processes=num_cores)

        for date in trading_days:
            logger.info(f"Processing date: {date}\n\n\n")
            
            # Create arguments list for parallel processing
            args_list = [(market, date, sector) for sector in sectors]
            
            # Process sectors in parallel
            results = pool.map(process_sector, args_list)
            
            # Get input file path from environment variable or use default
            input_file = os.environ.get("INPUT_FILE", "data/gpt_raw_decisions_o1.csv")
            
            # Combine results
            existing_df = pd.read_csv(input_file)
            combined_df = pd.concat([existing_df] + [df for df in results if not df.empty], 
                                  ignore_index=True)
            combined_df.to_csv(input_file, index=False)

        pool.close()
        pool.join()

    except Exception as e:
        logger.error(f"The pipeline raised the following error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
