#!/usr/bin/env python
"""
Database optimization script

This script applies database optimizations including:
1. Creating indexes for frequently accessed columns
2. Analyzing slow queries
3. Providing recommendations for further optimization
"""
import sys
import os
import logging
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from exitbot.database.database import SessionLocal
from exitbot.database.query_optimization import (
    setup_indexes, 
    explain_analyze_query,
    optimize_department_query,
    optimize_exit_reason_query
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("db_optimization.log")
    ]
)
logger = logging.getLogger("db_optimizer")

def create_indexes():
    """Create database indexes for optimization"""
    logger.info("Setting up database indexes...")
    try:
        setup_indexes()
        logger.info("Successfully created indexes")
        return True
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        return False

def analyze_queries():
    """Analyze slow queries and provide optimization suggestions"""
    logger.info("Analyzing queries...")
    db = SessionLocal()
    
    try:
        # Analyze the department query
        logger.info("Analyzing department query...")
        dept_query = optimize_department_query(db)
        dept_analysis = explain_analyze_query(db, dept_query)
        logger.info("Department query analysis:")
        for line in dept_analysis:
            logger.info(f"  {line.get('plan_line', '')}")
            
        # Analyze the exit reason query
        logger.info("Analyzing exit reason query...")
        reason_query = optimize_exit_reason_query(db)
        reason_analysis = explain_analyze_query(db, reason_query)
        logger.info("Exit reason query analysis:")
        for line in reason_analysis:
            logger.info(f"  {line.get('plan_line', '')}")
            
        return True
    except Exception as e:
        logger.error(f"Error analyzing queries: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Main function to run optimizations"""
    parser = argparse.ArgumentParser(description="Optimize database performance")
    parser.add_argument(
        "--indexes-only", 
        action="store_true", 
        help="Only create indexes without analyzing queries"
    )
    parser.add_argument(
        "--analyze-only", 
        action="store_true", 
        help="Only analyze queries without creating indexes"
    )
    args = parser.parse_args()
    
    logger.info("Starting database optimization")
    
    success = True
    
    # Create indexes if requested
    if not args.analyze_only:
        index_success = create_indexes()
        success = success and index_success
        
    # Analyze queries if requested
    if not args.indexes_only:
        query_success = analyze_queries()
        success = success and query_success
    
    if success:
        logger.info("Database optimization completed successfully")
        return 0
    else:
        logger.error("Database optimization completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 