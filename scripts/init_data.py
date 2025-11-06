#!/usr/bin/env python3.12
import asyncio
import logging
import sys
from pathlib import Path
from app.services.data_loader import DataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app/logs/data_init.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Initialize the data pipeline and generate embeddings."""
    try:
        # Create data loader
        loader = DataLoader()
        
        # Check if we need to force refresh
        force_refresh = "--force" in sys.argv
        
        # Initialize data
        logger.info("Starting data initialization...")
        if await loader.initialize_data(force_refresh=force_refresh):
            logger.info("Data initialization completed successfully")
            
            # Print stats
            stats = loader.get_data_stats()
            logger.info("Data Statistics:")
            logger.info(f"Total Episodes: {stats['total_episodes']}")
            logger.info(f"Seasons: {', '.join(map(str, stats['seasons']))}")
            logger.info(f"Last Updated: {stats['last_updated']}")
            logger.info(f"Collection: {stats['collection_name']}")
            logger.info(f"Model: {stats['embedding_model']}")
        else:
            logger.error("Data initialization failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during data initialization: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 