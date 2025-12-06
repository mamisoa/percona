"""
Rich console rendering helpers for cluster status output.
"""

from __future__ import annotations

from typing import Any, List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from percona.models import NodeStatus
from percona.wsrep import compute_warnings


def _style_on_off(value: Any) -> Text:
    """
    Style ON/OFF values for display.

    Args:
        value: Raw ON/OFF or truthy indicator retrieved from wsrep variables.

    Returns:
        Rich Text object with green color for ON, red otherwise.
    """

    is_on = str(value).upper() == "ON"
    return Text(str(value), style="green" if is_on else "red")


def _style_local_state(state: Any, comment: Any) -> Text:
    """
    Style the wsrep local state field with its comment.

    Args:
        state: Numeric state value.
        comment: Comment describing the state (e.g., Synced).

    Returns:
        Rich Text combining state and comment, colored green when synced.
    """

    synced = str(comment).lower() == "synced" or str(state) == "4"
    text = Text(f"{state} ({comment})")
    text.stylize("green" if synced else "yellow")
    return text


def _style_lsn(applied: Any, committed: Any) -> Text:
    """
    Style the last applied/committed sequence numbers.

    Args:
        applied: wsrep_last_applied value.
        committed: wsrep_last_committed value.

    Returns:
        Rich Text highlighting mismatches in yellow; green when equal.
    """

    equal = applied == committed
    text = Text(f"{applied}")
    if applied is not None and committed is not None:
        text.append(f" / {committed}", style="green" if equal else "yellow")
    return text


def _style_health(ok: bool) -> Text:
    """
    Style the per-node health indicator.

    Args:
        ok: Boolean flag indicating local node health.

    Returns:
        Rich Text describing the node health with color.
    """

    return Text("OK" if ok else "NOT OK", style="green" if ok else "red")


def render_node_status(console: Console, idx: int, st: NodeStatus, warnings: List[str]) -> None:
    """
    Render a single node status as a Rich panel.

    Args:
        console: Rich Console used for rendering.
        idx: One-based node index.
        st: NodeStatus for the given node.
        warnings: List of warning strings for the node.
    """

    title = f"Node #{idx}: {st.host}"

    if st.error:
        console.print(
            Panel(
                Text(f"STATUS: ERROR - {st.error}", style="bold red"),
                title=title,
                border_style="red",
                title_align="left",
            )
        )
        console.print()
        return

    table = Table(show_header=False, box=box.SIMPLE_HEAVY, expand=True, padding=(0, 1))
    table.add_row("wsrep_cluster_status", Text(str(st.vars.get("wsrep_cluster_status"))))
    table.add_row("wsrep_cluster_size", Text(str(st.vars.get("wsrep_cluster_size"))))
    table.add_row("wsrep_connected", _style_on_off(st.vars.get("wsrep_connected")))
    table.add_row("wsrep_ready", _style_on_off(st.vars.get("wsrep_ready")))
    table.add_row(
        "wsrep_local_state",
        _style_local_state(
            st.vars.get("wsrep_local_state"), st.vars.get("wsrep_local_state_comment")
        ),
    )
    table.add_row(
        "wsrep_cluster_state_uuid", Text(str(st.vars.get("wsrep_cluster_state_uuid")))
    )
    table.add_row("wsrep_cluster_conf_id", Text(str(st.vars.get("wsrep_cluster_conf_id"))))
    table.add_row(
        "wsrep_last_applied / committed",
        _style_lsn(st.vars.get("wsrep_last_applied"), st.vars.get("wsrep_last_committed")),
    )
    table.add_row("NODE HEALTH (local)", _style_health(st.ok))

    if warnings:
        warn_text = Text("\n".join(f"• {w}" for w in warnings), style="yellow")
        table.add_row("Warnings", warn_text)

    console.print(
        Panel(
            table,
            title=title,
            border_style="green" if st.ok else "red",
            title_align="left",
        )
    )
    console.print()


def print_report(statuses: List[NodeStatus], cluster_ok: bool) -> None:
    """
    Print a human-readable report of node and cluster health.

    Args:
        statuses: List of NodeStatus objects for all nodes.
        cluster_ok: Result of the global cluster evaluation.
    """

    console = Console()
    warnings_map = compute_warnings(statuses)

    console.print("[bold]Percona XtraDB / Galera cluster status[/bold]")
    console.print("=====================================\n")

    for idx, st in enumerate(statuses, start=1):
        render_node_status(console, idx, st, warnings_map.get(st.host, []))

    console.print("[bold]Cluster summary[/bold]")
    console.print("---------------")

    cluster_panel = Panel(
        Text(
            "GLOBAL STATUS: CLUSTER HEALTHY AND SYNCHRONIZED ✅"
            if cluster_ok
            else "GLOBAL STATUS: CLUSTER PROBLEM DETECTED ❌",
            style="green" if cluster_ok else "red",
        ),
        border_style="green" if cluster_ok else "red",
    )
    console.print(cluster_panel)

    aggregated_warnings = [w for warn_list in warnings_map.values() for w in warn_list]
    if aggregated_warnings:
        warn_text = Text("\n".join(f"• {w}" for w in aggregated_warnings), style="yellow")
        console.print(
            Panel(
                warn_text,
                title="Warnings",
                title_align="left",
                border_style="yellow",
            )
        )

