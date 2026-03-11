import os
import sys
import asyncio
from loguru import logger

# Add project root to path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.insert(0, project_root)

from src.open_llm_vtuber.live.chzzk_live import ChzzkLivePlatform
from src.open_llm_vtuber.config_manager.utils import read_yaml, validate_config

async def main():
    """
    Main function to run the Chzzk Live platform client.
    """
    logger.info("Starting Chzzk Live platform client")

    try:
        # Load configuration
        config_path = os.path.join(project_root, "conf.yaml")
        config_data = read_yaml(config_path)
        config = validate_config(config_data)

        # Extract Chzzk Live configuration
        chzzk_config = config.live_config.chzzk_live

        if not chzzk_config.channel_id:
            logger.error("No Chzzk Channel ID specified in configuration. Please add a channel_id.")
            return

        logger.info(f"Connecting to Chzzk Channel: {chzzk_config.channel_id} (Official: {chzzk_config.use_official_api})")

        # Initialize and run the Chzzk Live platform
        platform = ChzzkLivePlatform(
            channel_id=chzzk_config.channel_id,
            use_official=chzzk_config.use_official_api,
            access_token=chzzk_config.access_token
        )

        await platform.run()

    except Exception as e:
        logger.error(f"Error starting Chzzk Live client: {e}")
        import traceback
        logger.debug(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Chzzk Live platform")
