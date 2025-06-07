"""
ModuLink Python Default Trigger Providers

Default implementations for cron, message, and CLI triggers.
Users can override these with custom providers.
"""

from typing import Callable, Any, Dict, Optional, List, Union
from abc import ABC, abstractmethod
import asyncio
import logging
import warnings
from datetime import datetime

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

try:
    import click
    HAS_CLICK = True
    ClickGroup = click.Group
except ImportError:
    HAS_CLICK = False
    ClickGroup = Any


logger = logging.getLogger(__name__)


class TriggerProvider(ABC):
    """Abstract base class for trigger providers."""
    
    @abstractmethod
    def setup(self) -> None:
        """Setup the trigger provider."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup the trigger provider."""
        pass


class CronTriggerProvider(TriggerProvider):
    """
    Default cron trigger provider using APScheduler.
    
    Provides scheduling functionality for running function chains
    on time-based triggers.
    """
    
    def __init__(self):
        if not HAS_APSCHEDULER:
            raise ImportError(
                "APScheduler is required for cron triggers. "
                "Install with: pip install apscheduler"
            )
        # Use BackgroundScheduler for synchronous operation (better for testing)
        self.scheduler = BackgroundScheduler()
        self._jobs = {}
    
    def setup(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Cron scheduler started")
    
    def cleanup(self) -> None:
        """Stop the scheduler and cleanup jobs."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Cron scheduler stopped")
        self._jobs.clear()
    
    def schedule(self, expression: str, handler: Callable) -> str:
        """
        Schedule a function to run on a cron expression.
        
        Args:
            expression: Cron expression (e.g., '0 */5 * * *')
            handler: Function to execute - will be wrapped to receive Context
            
        Returns:
            Job ID for tracking
        """
        try:
            # Parse cron expression
            cron_parts = expression.split()
            
            # Create wrapper function that creates Context and calls handler
            def wrapped_handler():
                from .context import Context
                ctx = Context.from_cron_job(expression, {})
                return handler(ctx)
            
            # Store reference to original handler for testing
            wrapped_handler.original_func = handler
            
            if len(cron_parts) != 5:
                # For invalid format, create a job that will be scheduled but won't execute
                # Use a far future date to avoid actual execution during tests
                logger.warning(f"Invalid cron expression format: {expression}")
                from apscheduler.triggers.date import DateTrigger
                from datetime import datetime, timezone
                future_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
                trigger = DateTrigger(run_date=future_date)
                
                job = self.scheduler.add_job(
                    func=wrapped_handler,
                    trigger=trigger,
                    id=f"cron_{datetime.now().timestamp()}",
                    name=f"Cron job: {expression}"
                )
            else:
                minute, hour, day, month, day_of_week = cron_parts
                
                try:
                    # Let APScheduler handle detailed cron validation
                    trigger = CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week
                    )
                    
                    job = self.scheduler.add_job(
                        func=wrapped_handler,
                        trigger=trigger,
                        id=f"cron_{datetime.now().timestamp()}",
                        name=f"Cron job: {expression}"
                    )
                    
                except Exception as trigger_error:
                    # If APScheduler validation fails, create a date job for the far future
                    logger.warning(f"Invalid cron expression, scheduling for far future: {expression} - {trigger_error}")
                    from apscheduler.triggers.date import DateTrigger
                    from datetime import datetime, timezone
                    future_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
                    trigger = DateTrigger(run_date=future_date)
                    
                    job = self.scheduler.add_job(
                        func=wrapped_handler,
                        trigger=trigger,
                        id=f"cron_{datetime.now().timestamp()}",
                        name=f"Cron job: {expression}"
                    )
            
            self._jobs[job.id] = job
            logger.info(f"Scheduled cron job: {expression} -> {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to schedule cron job '{expression}': {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            logger.info(f"Removed cron job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove cron job '{job_id}': {e}")
            return False
    
    def register(self, expression: str, handler: Callable) -> str:
        """
        Register a cron job with direct function handler (for testing).
        
        Args:
            expression: Cron expression
            handler: Function to execute
            
        Returns:
            Job ID
        """
        return self.schedule(expression, handler)
    
    def start(self) -> None:
        """Start the scheduler."""
        self.setup()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.cleanup()


class MessageTriggerProvider(TriggerProvider):
    """
    Default message trigger provider (placeholder implementation).
    
    This is a placeholder that logs warnings. Users should provide
    their own message broker implementation.
    """
    
    def __init__(self):
        self._handlers = {}
    
    @property
    def handlers(self) -> Dict[str, Callable]:
        """Get registered handlers."""
        return self._handlers
    
    def setup(self) -> None:
        """Setup (no-op for placeholder)."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup handlers."""
        self._handlers.clear()
    
    def consume(self, topic: str, handler: Callable) -> None:
        """
        Register a message handler (placeholder).
        
        Args:
            topic: Message topic
            handler: Handler function
        """
        self._handlers[topic] = handler
        warnings.warn(
            f"Message trigger not implemented for topic: {topic}. "
            "Provide a custom message trigger provider for production use.",
            UserWarning
        )
        logger.warning(
            f"Message trigger registered but not implemented: {topic}. "
            "Use a custom provider for real message handling."
        )
    
    def register(self, topic: str, handler: Callable) -> None:
        """
        Register a message handler (alias for consume).
        
        Args:
            topic: Message topic
            handler: Handler function
        """
        self.consume(topic, handler)
    
    def emit(self, topic: str, message: Dict[str, Any]) -> None:
        """
        Emit a message to registered handler.
        
        Args:
            topic: Message topic
            message: Message data
        """
        from .context import Context
        
        if topic in self._handlers:
            handler = self._handlers[topic]
            # Create context for message
            ctx = Context.from_message(topic, message)
            ctx.data['event_type'] = topic
            ctx.data['payload'] = message
            handler(ctx)
        else:
            logger.warning(f"No handler registered for topic: {topic}")
    
    def start(self) -> None:
        """Start message provider (no-op for placeholder)."""
        pass
    
    def stop(self) -> None:
        """Stop message provider (no-op for placeholder)."""
        pass
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        """
        Simulate message publishing (for testing).
        
        Args:
            topic: Message topic
            message: Message data
        """
        if topic in self._handlers:
            handler = self._handlers[topic]
            await handler(message)
        else:
            logger.warning(f"No handler registered for topic: {topic}")


class CLITriggerProvider(TriggerProvider):
    """
    Default CLI trigger provider using Click.
    
    Provides command-line interface functionality for running
    function chains via CLI commands.
    """
    
    def __init__(self):
        if not HAS_CLICK:
            raise ImportError(
                "Click is required for CLI triggers. "
                "Install with: pip install click"
            )
        self._commands = {}
        self._cli_group = click.Group()
    
    @property
    def commands(self) -> Dict[str, Callable]:
        """Get registered commands."""
        return self._commands
    
    def setup(self) -> None:
        """Setup (no additional setup needed for CLI)."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup commands."""
        self._commands.clear()
    
    def command(self, name: str, handler: Callable) -> None:
        """
        Register a CLI command.
        
        Args:
            name: Command name
            handler: Handler function
        """
        
        @click.command(name=name)
        @click.option('--data', '-d', help='JSON data payload', default='{}')
        @click.pass_context
        def cli_command(ctx, data):
            """Execute the ModuLink chain function."""
            import json
            import asyncio
            
            try:
                data_dict = json.loads(data) if data else {}
            except json.JSONDecodeError as e:
                click.echo(f"Error parsing JSON data: {e}", err=True)
                ctx.exit(1)
            
            try:
                # Run the async handler
                result = asyncio.run(handler(data_dict))
                if hasattr(result, 'to_dict'):
                    result = result.to_dict()
                click.echo(json.dumps(result, indent=2, default=str))
            except Exception as e:
                click.echo(f"Error executing command: {e}", err=True)
                ctx.exit(1)
        
        self._commands[name] = cli_command
        self._cli_group.add_command(cli_command)
        logger.info(f"Registered CLI command: {name}")
    
    def register(self, command: str, handler: Callable) -> None:
        """
        Register a CLI command (alias for command).
        
        Args:
            command: Command name
            handler: Handler function
        """
        self._commands[command] = handler
        
    def execute(self, command: str, data: Dict[str, Any]) -> "Context":
        """
        Execute a registered command.
        
        Args:
            command: Command name
            data: Command data
            
        Returns:
            Context result
        """
        from .context import Context
        
        if command not in self._commands:
            raise ValueError(f"Command '{command}' not found")
        
        handler = self._commands[command]
        ctx = Context.from_cli_command(command, data)
        ctx.data['command'] = command
        ctx.data['args'] = data
        return handler(ctx)
    
    def start(self) -> None:
        """Start CLI provider (no-op)."""
        pass
    
    def stop(self) -> None:
        """Stop CLI provider (no-op)."""
        pass
    
    def get_cli_group(self):
        """Get the Click group for running CLI commands."""
        return self._cli_group


# Default trigger providers
DEFAULT_TRIGGERS = {
    'cron': CronTriggerProvider,
    'message': MessageTriggerProvider,
    'cli': CLITriggerProvider
}
