from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE_ROOT))

def main():
  console = Console()

  logo = Text.from_markup("""
  [bright_blue]
      ██████████████████
      ████████████████████
      ██████████████████████
      ████[/][red]███████████████[/][bright_blue]█████
      ████████████████████████
      ██████████████████████     
      ██████  ████  █████
      ███    ██    ███
      ███        ███
      ██████████
  [/bright_blue]

  [bold bright_blue]NeoZephyre[/bold bright_blue]
  [dim]your favorite agent[/dim]
  """)

  logo = Text.from_markup("""
                [#5b7fd8]███[/]               
              [#5b7fd8]███████[/]             
            [#141d3d]█[/][#5b7fd8]███████████[/][#141d3d]█[/]          
        [#141d3d]██[/][#2e4a8f]███████████████[/][#141d3d]██[/]       
      [#141d3d]██[/][#2e4a8f]███████████████████[/][#141d3d]██[/]     
      [#141d3d]██[/][#2e4a8f]█████████████████████[/][#141d3d]██[/]    
    [#141d3d]██[/][#2e4a8f]█[/][#9d6bff]█████[/][#2e4a8f]███████████[/][#9d6bff]█████[/][#2e4a8f]█[/][#141d3d]██[/]   
    [#141d3d]██[/][#2e4a8f]█[/][#9d6bff]███[/][#d6c3ff]███[/][#9d6bff]███[/][#2e4a8f]███[/][#9d6bff]███[/][#d6c3ff]███[/][#9d6bff]███[/][#2e4a8f]█[/][#141d3d]██[/]   
      [#141d3d]██[/][#2e4a8f]████[/][#9d6bff]█████[/][#2e4a8f]███[/][#9d6bff]█████[/][#2e4a8f]████[/][#141d3d]██[/]    
      [#141d3d]██[/][#2e4a8f]█████████████████████[/][#141d3d]██[/]    
        [#141d3d]██[/][#1e2e5c]█████████████████[/][#141d3d]██[/]      
          [#141d3d]██[/][#1e2e5c]█████████████[/][#141d3d]██[/]        
            [#141d3d]████[/][#1e2e5c]█[/][#141d3d]███[/][#1e2e5c]█[/][#141d3d]████[/]          
              [#141d3d]██[/][#1e2e5c]█[/][#141d3d]███[/][#1e2e5c]█[/][#141d3d]██[/]            
              [#141d3d]███████[/]             

  [bold bright_blue]NeoZephyre[/bold bright_blue]
  [dim]your favorite agent[/dim]
  """)

  console.print(
      Align.center(logo)
  )
  with console.status(status="[#2e4a8f]Starting the agent[/#2e4a8f]", spinner="simpleDotsScrolling", spinner_style="#2e4a8f"):
      from neozephyr.Orchestrator import Orchestrator

  Orchestrator()

if(__name__=="__main__"):
   main()