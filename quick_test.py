#!/usr/bin/env python3
"""
Quick Test Script - Verify connection and basic functionality

Usage:
    # Test localhost (default)
    python quick_test.py
    
    # Test with custom URL
    python quick_test.py --url http://staging:3333
    
    # Test with custom message
    python quick_test.py --message "chi 100k cà phê"
    
    # Interactive mode
    python quick_test.py --interactive
"""
import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import TestConfig
from api_client import MoneyCareAPIClient

console = Console()


def test_connection(config: TestConfig) -> bool:
    """Test if chatbot service is reachable"""
    import requests
    
    try:
        response = requests.get(
            f"{config.chatbot_base_url}/actuator/health",
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


def run_quick_test(config: TestConfig, message: str = "chi 50k ăn trưa"):
    """Run a quick test to verify everything works"""
    
    console.print(Panel(
        f"[bold blue]MoneyCare Chatbot Quick Test[/bold blue]\n\n"
        f"URL: {config.chatbot_base_url}\n"
        f"Environment: {config.environment}",
        title="🧪 Quick Test"
    ))
    
    # Step 1: Check connection
    console.print("\n[bold]Step 1: Checking connection...[/bold]")
    if test_connection(config):
        console.print("  ✅ Service is reachable")
    else:
        console.print("  ⚠️  Health endpoint not available (may still work)")
    
    # Step 2: Initialize client
    console.print("\n[bold]Step 2: Initializing session...[/bold]")
    client = MoneyCareAPIClient(config)
    
    init_resp = client.init_session()
    if not init_resp.success:
        console.print(f"  ❌ Failed: {init_resp.error}")
        return False
    
    console.print(f"  ✅ Session initialized")
    console.print(f"     Owner Type: {client.owner_type}")
    console.print(f"     Owner ID: {client.owner_id}")
    console.print(f"     Conversation: {client.conversation_id}")
    console.print(f"     Fingerprint: {client.fingerprint}")
    console.print(f"     Latency: {init_resp.latency_ms}ms")
    
    # Step 3: Send test message
    console.print(f"\n[bold]Step 3: Sending message: '{message}'[/bold]")
    
    ask_resp = client.ask(message)
    if not ask_resp.success:
        console.print(f"  ❌ Failed: {ask_resp.error}")
        return False
    
    console.print(f"  ✅ Response received in {ask_resp.latency_ms}ms")
    
    # Step 4: Parse response
    console.print("\n[bold]Step 4: Parsing response...[/bold]")
    
    answer, parsed = client.parse_bot_response(ask_resp.data)
    
    # Display answer
    console.print("\n[bold cyan]Bot Response:[/bold cyan]")
    if len(answer) > 500:
        console.print(f"  {answer[:500]}...")
    else:
        console.print(f"  {answer}")
    
    # Display parsed transaction if any
    if parsed:
        console.print("\n[bold cyan]Parsed Transaction:[/bold cyan]")
        table = Table(show_header=True)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in parsed.items():
            if value is not None and key not in ["summary", "emotion"]:
                table.add_row(key, str(value))
        
        console.print(table)
    
    # Summary
    console.print(Panel(
        f"[green]✅ Quick test passed![/green]\n\n"
        f"Init Latency: {init_resp.latency_ms}ms\n"
        f"Ask Latency: {ask_resp.latency_ms}ms\n"
        f"Total: {init_resp.latency_ms + ask_resp.latency_ms}ms",
        title="📊 Summary"
    ))
    
    return True


def interactive_mode(config: TestConfig):
    """Interactive chat mode for manual testing"""
    
    console.print(Panel(
        f"[bold blue]Interactive Mode[/bold blue]\n\n"
        f"Type messages to chat with the bot.\n"
        f"Commands:\n"
        f"  /quit - Exit\n"
        f"  /reset - Reset session\n"
        f"  /info - Show session info",
        title="💬 Interactive Chat"
    ))
    
    client = MoneyCareAPIClient(config)
    
    # Initialize session
    init_resp = client.init_session()
    if not init_resp.success:
        console.print(f"[red]Failed to init session: {init_resp.error}[/red]")
        return
    
    console.print(f"[green]Session started as {client.owner_type}[/green]\n")
    
    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().strip()
                
                if cmd == "/quit":
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                    
                elif cmd == "/reset":
                    client.reset_session()
                    init_resp = client.init_session()
                    if init_resp.success:
                        console.print("[green]Session reset![/green]")
                    else:
                        console.print(f"[red]Reset failed: {init_resp.error}[/red]")
                    continue
                    
                elif cmd == "/info":
                    console.print(f"  Owner: {client.owner_type} - {client.owner_id}")
                    console.print(f"  Conversation: {client.conversation_id}")
                    console.print(f"  Fingerprint: {client.fingerprint}")
                    continue
                    
                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                    continue
            
            # Send message
            resp = client.ask(user_input)
            
            if not resp.success:
                console.print(f"[red]Error: {resp.error}[/red]")
                continue
            
            answer, parsed = client.parse_bot_response(resp.data)
            
            console.print(f"[bold green]Bot:[/bold green] {answer}")
            console.print(f"[dim]({resp.latency_ms}ms)[/dim]\n")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
        except EOFError:
            break
    

def main():
    parser = argparse.ArgumentParser(
        description="Quick test for MoneyCare Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:3333",
        help="Chatbot API URL (default: http://127.0.0.1:3333)"
    )
    parser.add_argument(
        "--message", "-m",
        default="chi 50k ăn trưa",
        help="Test message to send (default: 'chi 50k ăn trưa')"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive chat mode"
    )
    parser.add_argument(
        "--env",
        default="localhost",
        help="Environment name (default: localhost)"
    )
    
    args = parser.parse_args()
    
    # Create config
    config = TestConfig(
        chatbot_base_url=args.url,
        environment=args.env
    )
    
    if args.interactive:
        interactive_mode(config)
    else:
        success = run_quick_test(config, args.message)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
