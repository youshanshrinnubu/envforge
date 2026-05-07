"""CLI subcommand for managing envforge notification settings."""

from __future__ import annotations

import argparse

from envforge.notifier import (
    SUPPORTED_EVENTS,
    NotifyConfig,
    load_config,
    save_config,
)


def add_notifier_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("notify", help="Manage notification settings")
    sub = parser.add_subparsers(dest="notify_cmd", required=True)

    sub.add_parser("show", help="Show current notification config")

    enable_p = sub.add_parser("enable", help="Enable notifications globally")
    enable_p.set_defaults(notify_cmd="enable")

    disable_p = sub.add_parser("disable", help="Disable notifications globally")
    disable_p.set_defaults(notify_cmd="disable")

    set_p = sub.add_parser("set", help="Configure events and handlers")
    set_p.add_argument(
        "--events",
        nargs="+",
        choices=sorted(SUPPORTED_EVENTS),
        help="Events to subscribe to",
    )
    set_p.add_argument(
        "--handlers",
        nargs="+",
        choices=["print", "log"],
        help="Notification handlers",
    )
    set_p.add_argument("--log-path", dest="log_path", help="Path for log handler output")

    parser.set_defaults(func=cmd_notify)


def cmd_notify(args: argparse.Namespace) -> None:
    cfg = load_config()

    if args.notify_cmd == "show":
        print(f"enabled:  {cfg.enabled}")
        print(f"events:   {', '.join(sorted(cfg.events)) or '(none)'}")
        print(f"handlers: {', '.join(cfg.handlers) or '(none)'}")
        print(f"log_path: {cfg.log_path or '(none)'}")
        return

    if args.notify_cmd == "enable":
        cfg.enabled = True
        save_config(cfg)
        print("Notifications enabled.")
        return

    if args.notify_cmd == "disable":
        cfg.enabled = False
        save_config(cfg)
        print("Notifications disabled.")
        return

    if args.notify_cmd == "set":
        if args.events is not None:
            cfg.events = args.events
        if args.handlers is not None:
            cfg.handlers = args.handlers
        if args.log_path is not None:
            cfg.log_path = args.log_path
        save_config(cfg)
        print("Notification config updated.")
        return

    print(f"Unknown notify subcommand: {args.notify_cmd}")
