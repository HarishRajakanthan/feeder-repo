#!/usr/bin/env python3
"""
Wrapper script to orchestrate the execution of three Python modules.
It processes entities and sub-entities defined in a configuration file.
"""

import configparser
import logging
import time
import concurrent.futures
import datetime
import os
from typing import Dict, List, Tuple, Any

# Import the three modules
from data_puller_1 import pull_data_1
from data_puller_2 import pull_data_2
from data_reconciler import reconcile_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wrapper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("wrapper")

def load_config(config_file: str) -> Dict[str, List[str]]:
    """
    Load entities and sub-entities from the configuration file.
    
    Args:
        config_file: Path to the .ini configuration file
        
    Returns:
        Dictionary with entities as keys and lists of sub-entities as values
    """
    logger.info(f"Loading configuration from {config_file}")
    config = configparser.ConfigParser()
    config.read(config_file)
    
    entities = {}
    for section in config.sections():
        entities[section] = [item.strip() for item in config[section]['sub_entities'].split(',')]
    
    return entities

def process_sub_entity(entity: str, sub_entity: str) -> Dict[str, Any]:
    """
    Process a single sub-entity by calling all three modules.
    
    Args:
        entity: The parent entity name
        sub_entity: The sub-entity name to process
        
    Returns:
        Dictionary containing results and metrics
    """
    start_time = time.time()
    logger.info(f"Starting processing of {entity}/{sub_entity}")
    
    result = {
        "entity": entity,
        "sub_entity": sub_entity,
        "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "errors": []
    }
    
    try:
        # Run the first two modules in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_1 = executor.submit(pull_data_1, entity, sub_entity)
            future_2 = executor.submit(pull_data_2, entity, sub_entity)
            
            try:
                data_1 = future_1.result(timeout=300)  # 5-minute timeout
                result["puller_1_success"] = True
            except Exception as e:
                logger.error(f"Error in data_puller_1 for {entity}/{sub_entity}: {str(e)}")
                result["puller_1_success"] = False
                result["errors"].append(f"Puller 1: {str(e)}")
                result["success"] = False
                data_1 = None
            
            try:
                data_2 = future_2.result(timeout=300)  # 5-minute timeout
                result["puller_2_success"] = True
            except Exception as e:
                logger.error(f"Error in data_puller_2 for {entity}/{sub_entity}: {str(e)}")
                result["puller_2_success"] = False
                result["errors"].append(f"Puller 2: {str(e)}")
                result["success"] = False
                data_2 = None
        
        # Only run reconciliation if both data pulls were successful
        if data_1 is not None and data_2 is not None:
            try:
                reconciliation_result = reconcile_data(data_1, data_2, entity, sub_entity)
                result["reconciliation_success"] = True
                result["reconciliation_result"] = reconciliation_result
            except Exception as e:
                logger.error(f"Error in data_reconciler for {entity}/{sub_entity}: {str(e)}")
                result["reconciliation_success"] = False
                result["errors"].append(f"Reconciliation: {str(e)}")
                result["success"] = False
        else:
            result["reconciliation_success"] = False
            result["errors"].append("Reconciliation skipped due to failed data pulls")
            
    except Exception as e:
        logger.error(f"Unexpected error processing {entity}/{sub_entity}: {str(e)}")
        result["success"] = False
        result["errors"].append(f"Unexpected: {str(e)}")
    
    end_time = time.time()
    duration = end_time - start_time
    result["duration"] = duration
    result["end_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"Finished processing {entity}/{sub_entity} in {duration:.2f} seconds. Success: {result['success']}")
    
    return result

def generate_report(results: List[Dict[str, Any]], output_file: str = "report.txt") -> None:
    """
    Generate a report of all processing results.
    
    Args:
        results: List of result dictionaries from process_sub_entity
        output_file: Path to write the report to
    """
    logger.info(f"Generating report to {output_file}")
    
    success_count = sum(1 for r in results if r["success"])
    failure_count = len(results) - success_count
    total_duration = sum(r["duration"] for r in results)
    
    with open(output_file, "w") as f:
        f.write("===== Processing Report =====\n\n")
        f.write(f"Report generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total entities processed: {len(results)}\n")
        f.write(f"Successful: {success_count}\n")
        f.write(f"Failed: {failure_count}\n")
        f.write(f"Total processing time: {total_duration:.2f} seconds\n\n")
        
        f.write("===== Entity Details =====\n\n")
        
        for r in results:
            f.write(f"Entity: {r['entity']}/{r['sub_entity']}\n")
            f.write(f"  Start time: {r['start_time']}\n")
            f.write(f"  End time: {r['end_time']}\n")
            f.write(f"  Duration: {r['duration']:.2f} seconds\n")
            f.write(f"  Success: {r['success']}\n")
            
            if "puller_1_success" in r:
                f.write(f"  Data Puller 1: {'Success' if r['puller_1_success'] else 'Failed'}\n")
            if "puller_2_success" in r:
                f.write(f"  Data Puller 2: {'Success' if r['puller_2_success'] else 'Failed'}\n")
            if "reconciliation_success" in r:
                f.write(f"  Reconciliation: {'Success' if r['reconciliation_success'] else 'Failed'}\n")
            
            if r["errors"]:
                f.write("  Errors:\n")
                for error in r["errors"]:
                    f.write(f"    - {error}\n")
            
            f.write("\n")
    
    logger.info(f"Report generated successfully: {success_count} successful, {failure_count} failed")

def create_sample_config(config_file: str = "entities.ini") -> None:
    """
    Create a sample configuration file if none exists.
    
    Args:
        config_file: Path to the configuration file to create
    """
    if os.path.exists(config_file):
        return
    
    config = configparser.ConfigParser()
    
    config["EntityA"] = {
        "sub_entities": "SubA1, SubA2, SubA3"
    }
    
    config["EntityB"] = {
        "sub_entities": "SubB1, SubB2"
    }
    
    config["EntityC"] = {
        "sub_entities": "SubC1"
    }
    
    with open(config_file, "w") as f:
        config.write(f)
    
    logger.info(f"Created sample configuration file: {config_file}")

def main(config_file: str = "entities.ini") -> None:
    """
    Main function to run the wrapper script.
    
    Args:
        config_file: Path to the .ini configuration file
    """
    # Make sure we have a config file
    create_sample_config(config_file)
    
    # Load the configuration
    entities = load_config(config_file)
    
    logger.info(f"Found {len(entities)} entities with a total of {sum(len(subs) for subs in entities.values())} sub-entities")
    
    # Process all entities and sub-entities
    results = []
    
    for entity, sub_entities in entities.items():
        logger.info(f"Processing entity: {entity} with {len(sub_entities)} sub-entities")
        
        for sub_entity in sub_entities:
            result = process_sub_entity(entity, sub_entity)
            results.append(result)
    
    # Generate the report
    generate_report(results)

if __name__ == "__main__":
    main()
