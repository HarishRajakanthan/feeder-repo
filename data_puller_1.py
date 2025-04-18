#!/usr/bin/env python3
"""
Data Puller 1: Retrieves data from the first source.
This module can be run as a standalone script or imported as a module.
"""

import argparse
import json
import logging
import requests
import time
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_puller_1.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_puller_1")

def pull_data_1(entity: str, sub_entity: str) -> Dict[str, Any]:
    """
    Pull data from the first source for a specific entity and sub-entity.
    
    Args:
        entity: The parent entity name
        sub_entity: The sub-entity name
        
    Returns:
        Dictionary containing the retrieved data
    """
    logger.info(f"Pulling data for {entity}/{sub_entity} from Source 1")
    
    # Simulate some processing time
    time.sleep(2)
    
    # In a real implementation, this would make an API call or fetch data from a URL
    # Example URL construction:
    url = f"https://api.example.com/v1/{entity}/{sub_entity}/data"
    
    try:
        # Simulated API call - replace with actual implementation
        # response = requests.get(url, timeout=30)
        # response.raise_for_status()
        # data = response.json()
        
        # For this example, we'll create dummy data
        data = {
            "source": "data_source_1",
            "entity": entity,
            "sub_entity": sub_entity,
            "timestamp": time.time(),
            "fields": {
                "metric_1": 100,
                "metric_2": 200,
                "status": "active"
            }
        }
        
        logger.info(f"Successfully pulled data for {entity}/{sub_entity} from Source 1")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error pulling data for {entity}/{sub_entity} from Source 1: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error for {entity}/{sub_entity} from Source 1: {str(e)}")
        raise

def save_data(data: Dict[str, Any], output_file: Optional[str] = None) -> None:
    """
    Save the pulled data to a file.
    
    Args:
        data: The data to save
        output_file: The file to save to (defaults to entity_subentity_source1.json)
    """
    if output_file is None:
        output_file = f"{data['entity']}_{data['sub_entity']}_source1.json"
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Data saved to {output_file}")

def main() -> None:
    """
    Main function when running as a standalone script.
    """
    parser = argparse.ArgumentParser(description="Pull data from Source 1")
    parser.add_argument("entity", help="The entity to process")
    parser.add_argument("sub_entity", help="The sub-entity to process")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        data = pull_data_1(args.entity, args.sub_entity)
        save_data(data, args.output)
    except Exception as e:
        logger.error(f"Failed to process {args.entity}/{args.sub_entity}: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
