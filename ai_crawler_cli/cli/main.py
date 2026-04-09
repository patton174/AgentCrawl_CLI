import os
import json
import click
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Load components
from ai_crawler_cli.utils.logger import setup_logger, log
from ai_crawler_cli.core.context import ContextManager
from ai_crawler_cli.tools.registry import registry
from ai_crawler_cli.core.thread_manager import thread_manager
from ai_crawler_cli.scheduler.scheduler import scheduler

# Import tools to ensure they are registered
import ai_crawler_cli.tools.builtins
import ai_crawler_cli.executor.script_runner

# OpenAI API
from openai import OpenAI

console = Console()
session = PromptSession(history=InMemoryHistory())

def process_ai_response(client: OpenAI, context: ContextManager, model: str):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=context.get_context(),
            tools=registry.get_schemas(),
            tool_choice="auto",
        )
        
        message = response.choices[0].message
        
        # Add assistant message to context
        if message.content:
            context.add_message(role="assistant", content=message.content)
            console.print(Markdown(message.content))
            
        # Handle tool calls
        if message.tool_calls:
            # We need to save the assistant message with tool calls to context
            tool_call_dicts = []
            for tc in message.tool_calls:
                tool_call_dicts.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            
            # Since context manager pydantic model expects simple dicts for tool_calls
            context.add_message(
                role="assistant", 
                content=message.content or "", 
                tool_calls=tool_call_dicts
            )

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                console.print(f"[bold cyan]🔧 Executing Tool:[/bold cyan] {func_name}")
                log.info(f"Tool Call: {func_name} with args {args}")
                
                try:
                    result = registry.execute(func_name, args)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Error executing tool: {e}"
                    log.error(result_str)
                
                # Add tool result to context
                context.add_message(
                    role="tool", 
                    content=result_str,
                    tool_call_id=tool_call.id,
                    name=func_name
                )
                
                console.print(Panel(result_str[:500] + ("..." if len(result_str)>500 else ""), title=f"Result: {func_name}", expand=False))
            
            # Recurse if tools were called to let AI interpret results
            process_ai_response(client, context, model)
            
    except Exception as e:
        console.print(f"[bold red]Error communicating with AI:[/bold red] {e}")
        log.exception("AI API Error")

@click.command()
@click.option('--debug', is_flag=True, help="Enable debug logging.")
@click.option('--model', default="gpt-4-turbo", help="OpenAI model to use.")
def main(debug, model):
    """AI Crawler CLI - A smart agent for web crawling and task automation."""
    load_dotenv()
    setup_logger(debug)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]Error: OPENAI_API_KEY environment variable is not set.[/bold red]")
        return
        
    client = OpenAI(api_key=api_key)
    context = ContextManager()
    
    # Start background managers
    scheduler.start()
    
    console.print(Panel.fit("[bold green]Welcome to AI Crawler CLI[/bold green]\nType 'exit' or 'quit' to quit. Type 'help' for commands.", border_style="green"))
    
    try:
        while True:
            try:
                user_input = session.prompt("🤖> ", auto_suggest=AutoSuggestFromHistory())
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
                
            user_input = user_input.strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                break
                
            if user_input.lower() == 'help':
                console.print("[bold yellow]Available Commands:[/bold yellow]")
                console.print("- exit, quit: Exit the CLI")
                console.print("- help: Show this help message")
                console.print("- clear: Clear the screen and context")
                continue
                
            if user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                context = ContextManager()
                console.print("[green]Context cleared.[/green]")
                continue
                
            context.add_message(role="user", content=user_input)
            
            with console.status("[bold blue]Thinking...", spinner="dots"):
                process_ai_response(client, context, model)
                
    finally:
        console.print("[yellow]Shutting down background tasks...[/yellow]")
        scheduler.stop()
        thread_manager.shutdown()
        console.print("[green]Goodbye![/green]")

if __name__ == "__main__":
    main()
