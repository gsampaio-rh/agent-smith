"""CLI entrypoint — dispatches to TUI or direct subcommands."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from smith.config import SmithConfig, check_bind_shell, resolve_agent_ip
from smith.registry import ATTACKS, Phase, attacks_by_phase, get_attack
from smith.runner import ScriptRunner


console = Console()

DEMO_SEQUENCE = [
    "trigger",
    "wait-shell",
    "connect",
    "exploit",
    "hold-shell",
    "recon",
    "steal-secrets",
    "steal-tokens",
    "lateral-db",
    "persist-claude",
    "persist-cronjob",
    "exfil-dns",
    "miner",
    "scale-zero",
    "log-flood",
    "hijack-model",
    "agent-worm",
]


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a single attack by ID."""
    try:
        attack = get_attack(args.attack_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1

    target = getattr(args, "target", None)
    if target:
        console.print(f"[bold]Target:[/bold]  {target}")

    console.print(f"[bold]Running:[/bold] {attack.name} ({attack.script})")
    console.print()

    env_overrides = {}
    if target:
        env_overrides["AGENT_POD_IP"] = target
    runner = ScriptRunner(env_overrides=env_overrides)
    result = runner.run(args.attack_id)

    if result.output.strip():
        console.print(result.output, highlight=False)

    if result.timed_out:
        console.print("[yellow]Script timed out.[/yellow]")
        return 1
    if result.exit_code != 0:
        console.print(f"[red]Exited with code {result.exit_code}[/red]")
        return result.exit_code

    console.print("[green]Done.[/green]")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show current environment and bind-shell state."""
    cfg = SmithConfig.from_env()

    title = "Smith Status [yellow](DEV LOCAL)[/yellow]" if cfg.local_dev else "Smith Status"
    table = Table(title=title, show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Mode", "[yellow]dev-local[/yellow]" if cfg.local_dev else "[green]in-cluster[/green]")
    table.add_row("Scripts Dir", cfg.scripts_dir)
    table.add_row("Agent Namespace", cfg.agent_ns)
    table.add_row("Bind Port", str(cfg.bind_port))
    table.add_row("Neo UI Service", cfg.neo_ui_svc)
    table.add_row("Attacker Namespace", cfg.attacker_ns)

    if cfg.local_dev:
        table.add_row("Agent Pod IP", "[dim]N/A (local)[/dim]")
        table.add_row("Bind Shell", "[dim]N/A (local)[/dim]")
    else:
        agent_ip = resolve_agent_ip(cfg)
        table.add_row("Agent Pod IP", agent_ip or "[dim]unknown[/dim]")

        if agent_ip:
            shell_ok = check_bind_shell(agent_ip, cfg.bind_port)
            status = "[green]OPEN[/green]" if shell_ok else "[red]CLOSED[/red]"
        else:
            status = "[dim]N/A[/dim]"
        table.add_row("Bind Shell", status)

    console.print(table)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Print the recommended workshop demo sequence."""
    console.print("[bold]Recommended Workshop Demo Sequence[/bold]")
    console.print()

    for i, attack_id in enumerate(DEMO_SEQUENCE, 1):
        try:
            attack = get_attack(attack_id)
        except ValueError:
            continue
        phase_color = attack.phase.color
        marker = "[bold red]* bind shell[/bold red]" if attack.requires_bind_shell else ""
        console.print(
            f"  {i:2d}. [{phase_color}]{attack.phase.label:20s}[/{phase_color}] "
            f"{attack.name}  {marker}"
        )

    console.print()
    console.print("[dim]* = requires bind shell to be open on the agent pod[/dim]")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all available attacks grouped by phase."""
    grouped = attacks_by_phase()

    for phase in Phase:
        group = grouped.get(phase, [])
        if not group:
            continue
        console.print(f"\n[bold {phase.color}]{phase.label}[/bold {phase.color}]")
        for attack in group:
            shell = " [dim](bind shell)[/dim]" if attack.requires_bind_shell else ""
            console.print(f"  {attack.id:22s} {attack.name}{shell}")

    console.print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smith",
        description="Agent Smith — interactive red-team toolkit for The Matrix workshop",
    )
    parser.add_argument(
        "--no-tui", action="store_true",
        help="Skip the interactive TUI, use CLI-only mode",
    )
    parser.add_argument(
        "--guided", action="store_true",
        help="Launch guided workshop walkthrough",
    )

    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a specific attack")
    run_p.add_argument("attack_id", help="Attack ID (e.g. recon, steal-secrets)")
    run_p.add_argument(
        "--target", metavar="IP_OR_POD",
        help="Target pod IP or name (skips k8s pod discovery)",
    )
    run_p.set_defaults(func=cmd_run)

    status_p = sub.add_parser("status", help="Show environment and bind-shell state")
    status_p.set_defaults(func=cmd_status)

    plan_p = sub.add_parser("plan", help="Show recommended workshop demo sequence")
    plan_p.set_defaults(func=cmd_plan)

    list_p = sub.add_parser("list", help="List all available attacks")
    list_p.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args.func(args)

    if args.no_tui:
        parser.print_help()
        return 0

    try:
        from smith.app import SmithApp
        app = SmithApp(guided=args.guided)
        app.run()
        return 0
    except ImportError:
        console.print("[yellow]Textual not available, falling back to CLI.[/yellow]")
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
