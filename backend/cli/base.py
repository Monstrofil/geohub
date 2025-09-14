"""
Base command class for CLI management commands
"""
import argparse
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, List
from tortoise import Tortoise


class BaseCommand(ABC):
    """Base class for management commands"""
    
    help = ""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(description=self.help)
        self.add_arguments()
    
    def add_arguments(self):
        """Add command-specific arguments to the parser"""
        pass
    
    @abstractmethod
    async def handle(self, **options):
        """Handle the command execution"""
        pass
    
    async def run(self, args: Optional[List[str]] = None):
        """Parse arguments and run the command"""
        try:
            # Initialize database connection
            await self._init_db()
            
            # Parse arguments
            parsed_args = self.parser.parse_args(args)
            options = vars(parsed_args)
            
            # Execute command
            await self.handle(**options)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        finally:
            # Close database connection
            await self._close_db()
    
    async def _init_db(self):
        """Initialize database connection"""
        from database import TORTOISE_ORM
        await Tortoise.init(
            db_url=TORTOISE_ORM["connections"]["default"],
            modules={"models": TORTOISE_ORM["apps"]["models"]["models"]}
        )
    
    async def _close_db(self):
        """Close database connection"""
        await Tortoise.close_connections()
    
    def execute(self, args: Optional[List[str]] = None):
        """Execute the command (synchronous entry point)"""
        asyncio.run(self.run(args))
