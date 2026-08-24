#!/usr/bin/env python3
"""
HyperTrail Trailing Order TUI - Complete Textual Application
Interactive dashboard for managing trailing limit orders on Hyperliquid DEX.
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Static, Input, Select, Button, Label, Header, Footer, 
    DataTable, TabPane, Tabs, Tree
)
from textual.containers import Horizontal, Vertical, ScrollableContainer, Container
from textual.binding import Binding


# Import engine components
from engine.models import BotConfig, BotState, TrailType, BotStatus
from engine.config import config
from engine.persistence import DatabasePersistence


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: [hypertrail] - %(levelname)s - %(message)s"
)

logger = logging.getLogger("hypertrail.tui")


class CreateBotDialog(ModalScreen):
    """Modal dialog for creating new trailing order bots."""
    
    CSS = """
    #create-bot-container {
        padding: 2;
        height: auto;
        max-height: 70%;
    }
    
    #bot-form {
        width: 80fr;
        max-width: 100%;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    
    .form-label {
        text-style: bold;
        width: 18fr;
        padding-right: 1;
    }
    
    #button-group {
        height: auto;
        margin-top: 2;
    }
"""
    
    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    
    def compose(self) -> ComposeResult:
        trail_types = [(t.value, t.value.replace('_', ' ').title()) for t in TrailType]
        
        with ScrollableContainer(id="create-bot-container"):
            title = Static("[bold]== NEW BOT CONFIGURATION ==[/]", id="dialog-title")
            yield title
            
            with Horizontal(id="bot-form"):
                # Trail Type selector (no initial value - user must select one)
                with Vertical():
                    Label("Trail Type", classes="form-label")
                    yield Select(
                        trail_types,
                        allow_blank=False,
                        id="trail_type",
                    )
                
                # Coin symbol
                with Vertical():
                    Label("Coin (e.g., BTC)", classes="form-label")
                    yield Input(id="coin", placeholder="BTC", value="BTC")
                
                # Size in USD
                with Vertical():
                    Label("Size ($USD)", classes="form-label")
                    yield Input(id="size_usd", placeholder="100.0", type="number", value="100.0")
                
                # Order side
                with Vertical():
                    Label("Side", classes="form-label")
                    yield Select(
                        [("buy", "Buy"), ("sell", "Sell")],
                        allow_blank=False,
                        id="order_side",
                    )
                
                # Offset percentage
                with Vertical():
                    Label("Initial Offset (%)", classes="form-label")
                    yield Input(id="offset_pct", placeholder="0.8", type="number", value="0.8")
                    note = Static("[dim]Min order: $50 USD[/]", id="min-size-note")
                    yield note
            
            status_static = Static(
                "[yellow]Press Enter on buttons to confirm or Cancel to close.[/]"
            )
            yield status_static
            
            # Button group
            with Horizontal(id="button-group"):
                create_btn = Button("Create Bot", id="create", variant="primary")
                cancel_btn = Button("Cancel", id="cancel", variant="default")
                
                yield create_btn
                yield cancel_btn
        
        footer_static = Footer()
        yield footer_static
    
    BINDINGS = [Binding("escape", "dismiss_cancel", "Cancel")]
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "create":
            self._submit()
        elif event.button.id == "cancel":
            self.dismiss(False)
    
    def action_dismiss_cancel(self) -> None:
        """Handle ESC key to dismiss dialog with cancel."""
        self.dismiss(False)

    def _submit(self) -> None:
        """Submit the form and return bot config."""
        # Get selected trail type - Select returns display text, need to map back to enum value
        selected_display = self.query_one("#trail_type", Select).value
        # Map display labels back to TrailType enum values
        trail_type_value = {
            "Long Entry": "long_entry",
            "Short Entry": "short_entry", 
            "Long Exit": "long_exit",
            "Short Exit": "short_exit"
        }.get(selected_display, "long_entry")  # fallback to long_entry
        trail_type = TrailType(trail_type_value)
        
        coin = self.query_one("#coin", Input).value.upper() if self.query_one("#coin", Input).value else "BTC"
        
        try:
            size_usd = float(self.query_one("#size_usd", Input).value)
            offset_pct = float(self.query_one("#offset_pct", Input).value) or 0.8
        except ValueError:
            self.notify("Invalid numbers entered", severity="error")
            return
        
        order_side = self.query_one("#order_side", Select).value
        
        bot_config = {
            "id": str(uuid.uuid4())[:8],
            "coin": coin,
            "trail_type": trail_type.value,
            "size_usd": size_usd,
            "offset_pct": offset_pct,
            "max_chase_pct": 1.5,
            "order_side": order_side,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat()
        }
        
        self.notify(f"Creating bot: {coin} (ID: {bot_config['id']})!", severity="success")
        self.dismiss(bot_config)


class HelpModal(ModalScreen):
    """Help information modal."""
    
    CSS = """
    #help-content {
        padding: 2;
    }
    
    .key-badge {
        background: $primary-darken-1;
        color: white;
        text-style: bold;
        padding: 1;
        width: auto;
    }
"""
    
    BINDINGS = [Binding("escape", "dismiss", "Exit")]
    
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]== HYPERTRAIL TUI HELP ==[/]\n"
        )
        
        yield Static("[bold]Keyboard Controls:[/]")
        yield Static("  [yellow][q] [/]. Quit the application")
        yield Static("  [yellow][c] [/]. Create new bot (creates dialog)")
        yield Static("  [yellow][d] [/]. Delete selected bots")
        yield Static("  [yellow][m] [/]. Toggle monitoring mode")
        yield Static("  [yellow][h] [/]. This help screen\n")
        
        yield Static("[bold]Trailing Order Types:[/]")
        for trail_type in TrailType:
            yield Static(f"  • {trail_type.value.replace('_', ' ').title()}")
        
        yield Static("\n[bold]Bot Management:[/] \n  ")
        yield Static("  • Use arrow keys and Enter to select bots\n  ")
        yield Static("  • Select bot from queue table below\n  ")
        yield Static("  • Delete with D key when selected")
        
        status_static = Static(
            "[dim]Press ESC or click Close to exit help.[/]"
        )
        yield status_static
        
        close_btn = Button("Close", id="help-close", variant="default")
        yield close_btn
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help-close":
            self.dismiss(None)
    
    def action_dismiss(self) -> None:
        """Handle ESC key to dismiss help modal."""
        self.dismiss(None)


class BotManagementScreen(Screen):
    """Main screen for bot management and order operations."""
    
    CSS = """
    Screen {
        background: $background;
        width: 100%;
        height: 100%;
    }
    
    #main-panel {
        height: 100%;
        margin: 1;
    }
    
    #stats-bar {
        height: auto;
        padding: 1;
        background: $secondary-background;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .stat-item {
        width: 25fr;
        text-align: center;
        padding: 1;
    }
    
    #bot-table-container {
        height: 8fr;
        border: solid $primary-darken-1;
        background: $surface;
    }
    
    DataTable {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #action-buttons {
        height: auto;
        margin-top: 1;
        padding: 1;
        background: $secondary-background;
        align: left middle;
    }
    """
    
    BINDINGS = [
        Binding("d", "action_delete_selected", "Delete (d)", show=True),  # Must match method name
        Binding("q",  "quit_app", "Quit", show=True),
        Binding("c", "open_create_bot", "New Bot", show=True),
        Binding("d", "delete_selected", "Delete (d)", show=True),
        Binding("m", "toggle_monitor", "Monitor (m)", show=True),
        Binding("h", "show_help", "Help (h)", show=True),
    ]
    
    def __init__(self, persistence=None):
        super().__init__()
        self.bots = {}  # Store bot data {id: dict}  
        self.table_widget = None
        self._persistence = persistence
        
    @property
    def persistence(self):
        """Get persistence layer instance."""
        return self._persistence or getattr(self.app, "persistence", None)

    def compose(self) -> ComposeResult:
        """Create the main layout."""
        
        yield Header()
        
        # Stats panel
        with Horizontal(id="stats-bar"):
            yield Static("Network:", id="_status_label", classes="stat-item")
            yield Static(config.NETWORK_MODE.upper(), classes="stat-item")
            
            config_valid = config.is_valid()
            status_color = "green" if config_valid else "red"
            status_text = f"[{status_color}]Valid[/]" if config_valid else "[red]Invalid[/]"
            yield Static(f"API: {status_text}", id="_api_status", classes="stat-item")
            
            yield Static("Active Bots:", id="_bots_label", classes="stat-item")
            yield Static(str(len(self.bots)), id="_active_counter", classes="stat-item")
        
        # Main table container with DataTable widget
        with ScrollableContainer(id="bot-table-container"):
            self.table_widget = DataTable()
            for header in ["ID", "Coin", "Trail Type", "Side", "Size ($)", "Offset %", "Status"]:
                self.table_widget.add_column(header, width=8)
            yield self.table_widget
        
        # Action buttons
        with Horizontal(id="action-buttons"):
            create_btn = Button("Create Bot (c)", variant="primary")
            delete_btn = Button("Delete Selected (d)")
            monitor_btn = Button("Monitor Orders (m)")
            help_btn = Button("Help (h)")
            
            yield create_btn
            yield delete_btn
            yield monitor_btn
            yield help_btn
        
        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen after mount - load persisted bots and populate table."""
        super().on_mount() if hasattr(super(), "on_mount") else None
        
        # Load bots from persistence layer now that table_widget exists from compose
        asyncio.create_task(self._load_bots())

    async def _load_bots(self) -> None:
        """Load bots from database persistence layer."""
        # Ensure we have a table_widget before proceeding
        if self.table_widget is None:
            logger.warning("Table widget not ready during load")
            return
        
        logger.info(f"[LOAD] Starting bot load, current bots count: {len(self.bots)}")
        
        self.table_widget.clear()
        
        # Load all persisted bot configurations from database
        if self.persistence:
            loaded_bots = await self.persistence.load_all_bots()
            
            logger.info(f"[LOAD] Loaded {len(loaded_bots)} bot(s) from database")
            
            if loaded_bots:
                self.bots = self._convert_loaded_bots_to_internal_format(loaded_bots)
                logger.info(f"[LOAD] Converted to internal format: {len(self.bots)} bots")
                
                # Refresh the table to display loaded bots
                self.refresh_table()
        
        # Update the active bots counter
        try:
            if active_static := self.query_one("#_active_counter", Static):
                active_static.update(str(len(self.bots)))
                logger.info(f"[LOAD] Updated counter to {len(self.bots)}")
        except Exception as e:
            logger.error(f"[LOAD] Could not update counter: {e}")

    def _convert_loaded_bots_to_internal_format(self, loaded_bots: dict) -> dict:
        """Convert database bot records to internal dictionary format."""
        converted = {}
        
        for bot_id, db_record in loaded_bots.items():
            # Map database fields to internal format
            internal_bot = {
                "id": db_record.get("id") or db_record.get("bot_id"),
                "coin": db_record.get("coin", ""),
                "trail_type": self._map_order_side_to_value(db_record.get("order_side", "buy")),
                "size_usd": float(db_record.get("size_usd", 0)),
                "offset_pct": float(db_record.get("offset_pct", 0)),
                "max_chase_pct": float(db_record.get("max_chase_pct", 1.5)),
                "order_side": db_record.get("order_side", db_record.get("order_side", "buy")),
                "status": db_record.get("status", "ACTIVE"),
                "created_at": db_record.get("created_at"),
            }
            
            converted[bot_id] = internal_bot
        
        return converted

    def _map_order_side_to_value(self, side: str) -> str:
        """Map order side to trail type based on buy/sell side."""
        if side.lower() == "buy":
            # Buying => long entry
            return "long_entry"
        elif side.lower() == "sell":
            # Selling => short entry
            return "short_entry"
        return "long_entry"

    def action_quit_app(self) -> None:
        """Exit the application."""
        self.app.exit()
        
    def show_help(self) -> None:
        """Open the help modal."""
        if hasattr(self.app, 'push_screen'):
            def handle_result(result=None):
                self._on_help_closed(result)
            
            help_modal = HelpModal()
            self.app.push_screen(help_modal, handle_result)
    
    def _on_help_closed(self, result=None):
        """Callback when help modal is closed."""
        logger.info("Help modal closed")
        
    def open_create_bot(self) -> None:
        """Open the create bot dialog."""
        # Use the app's push_screen method (Screen doesn't have push_screen)
        if hasattr(self.app, 'push_screen'):
            # Callback that directly calls the async handler
            def handle_result(config):
                logger.info(f"[DIALOG] Result received: {config is not None}")
                # Call async function - create_task wraps it automatically
                asyncio.create_task(self._on_create_bot_created(config))
            
            dialogue = CreateBotDialog()
            self.app.push_screen(dialogue, handle_result)
    
    async def _execute_delete_selection(self) -> None:
        """Internal: Execute deletion selection (async)."""
        # Check if table exists and has bots
        if not self.table_widget or len(self.bots) == 0:
            logger.error("[DELETE] Table widget unavailable or no bots")
            self.notify("No bots to delete", severity="warning")
            return

        try:
            # Try multiple approaches to get selection
            logger.info(f"[DELETE] Checking selection in DataTable with {len(self.bots)} bots shown in table")
            
            # Get available attributes related to selection
            sel_attrs = [a for a in dir(self.table_widget) if 'select' in a.lower() or 'cursor' in a.lower()]
            logger.info(f"[DELETE] Relevant attrs: {sel_attrs}")

            # Approach 1: Check selection (set-based, multi-select mode)
            if hasattr(self.table_widget, 'selection'):
                sel_value = self.table_widget.selection
                logger.info(f"[DELETE] Selection value: {type(sel_value).__name__} = {sel_value}")
                
                if isinstance(sel_value, set) and len(sel_value):
                    # Multi-select mode with actual selections
                    for row_idx in sorted(sel_value):
                        if 0 <= row_idx < len(self.bots):
                            bot_id = list(self.bots.keys())[row_idx]
                            asyncio.create_task(self._handle_single_deletion(bot_id))
                            logger.info(f"[DELETE] ✓ Deleted {bot_id} from selected row {row_idx}")
                    return

            # Approach 2: Check cursor position (arrow keys mode)
            if hasattr(self.table_widget, 'cursor_row') and self.table_widget.cursor_row is not None:
                cursor = self.table_widget.cursor_row
                logger.info(f"[DELETE] Cursor at row {cursor}, total rows {len(self.bots)}")
                
                if 0 <= cursor < len(self.bots):
                    bot_id = list(self.bots.keys())[cursor]
                    asyncio.create_task(self._handle_single_deletion(bot_id))
                    logger.info(f"[DELETE] ✓ Deleted {bot_id} from cursor row {cursor}")
                    return
            
            # Approach 3: First selection (if exists)
            if hasattr(self.table_widget, 'first_selected') and self.table_widget.first_selected is not None:
                first = self.table_widget.first_selected
                logger.info(f"[DELETE] First selected index: {first}")
                
                if isinstance(first, int) and 0 <= first < len(self.bots):
                    bot_id = list(self.bots.keys())[first]
                    asyncio.create_task(self._handle_single_deletion(bot_id))
                    logger.info(f"[DISPLAY] ✓ Deleted {bot_id} from first_selected")
                    return

            # No valid selection found
            logger.error("[DELETE] No valid row selected - please select with arrow keys or click")
            self.notify("Select a bot row (arrow keys or click to highlight), then press D", severity="warning")

        except Exception as e:
            logger.exception(f"[DELETE] Error checking selection: {e}")
            import traceback
            traceback.print_exc()
            self.notify(f"Error: {str(e)}", severity="error")


    async def _handle_single_deletion(self, bot_id: str) -> None:
        """Handle deletion of a single bot asynchronously with UI updates."""
        try:
            # Delete from database
            if self.persistence:
                await self.persistence.delete_bot(bot_id)
                logger.info(f"[DELETE] ✓ Removed {bot_id} from database")
            
            # Remove from memory and update UI
            if bot_id in self.bots:
                del self.bots[bot_id]
                logger.info(f"[DELETE] ✓ Deleted bot {bot_id}")
                
                # Refresh table to remove deleted row
                self.refresh_table()
                
                # Update active bots counter
                try:
                    if active_static := self.query_one("#_active_counter", Static):
                        active_static.update(str(len(self.bots)))
                        logger.info(f"[DELETE] ✓ Counter updated to {len(self.bots)}")
                except Exception as e:
                    logger.warning(f"[DELETE] Could not update counter: {e}")
            
            # Show confirmation
            self.notify(f"✓ Bot {bot_id} deleted", severity="success")
        except Exception as e:
            logger.error(f"[DELETE] Error deleting {bot_id}: {e}")
            import traceback
            traceback.print_exc()
            self.notify(f"Error deleting bot: {str(e)}", severity="error")

        """Refresh UI after bot creation - called synchronously."""
        logger.info(f"[UI] Refreshing table and counter for new bot")
        
        # Always refresh table (no guard clauses!)
        if self.table_widget:
            self.refresh_table()
            logger.info(f"[UI] Table refreshed with {len(self.bots)} bots")
            
            # Update counter
            try:
                if active_static := self.query_one("#_active_counter", Static):
                    active_static.update(str(len(self.bots)))
                    logger.info(f"[UI] Counter updated to {len(self.bots)}")
            except Exception as e:
                logger.warning(f"[UI] Could not update counter: {e}")
        else:
            logger.error("[UI] Table widget is None - cannot refresh!")

    def _map_trail_type(self, trail_type) -> str:
        """Map trail type to proper value."""
        if isinstance(trail_type, str):
            return trail_type.lower()
        elif hasattr(trail_type, 'value'):
            return trail_type.value
        return "long_entry"  # default fallback


    def refresh_table(self) -> None:
        """Update the table with current bots."""
        if not self.table_widget:
            logger.warning("[TABLE] Table widget is None")
            return
            
        logger.info(f"[TABLE] Clearing and refreshing {len(self.bots)} bots")
        self.table_widget.clear()
        
        for bot_id, bot_data in sorted(self.bots.items()):
            row_data = (
                str(bot_data.get("id", ""))[:8],
                str(bot_data.get("coin", "")),
                str(bot_data.get("trail_type", "")).replace('_', ' ').title(),
                str(bot_data.get("order_side", "UNKNOWN")).upper(),
                f"${bot_data.get('size_usd', 0):.2f}",
                f"{bot_data.get('offset_pct', 0)}%",
                "ACTIVE" if bot_data.get("status") == "ACTIVE" else "INACTIVE",
            )
            self.table_widget.add_row(*row_data)
        
        logger.info(f"[TABLE] Added {len(self.bots)} rows to table")


class HyperTrailApp(App):
    """Main application entry point for TUI."""
    
    CSS = """
    Screen { background: $background; }
    DataTable { padding: 1; }
    .stat-item { padding: 1; text-align: center; }
    #stats-bar { height: auto; padding: 1; background: $secondary-background; }
    """
    
    TITLE = "HyperTrail - Trailing Order Manager"
    
    BINDINGS = [
        Binding("d", "action_delete_selected", "Delete (d)", show=True),  # Must match method name
        Binding("q",  "quit_app_app", "Quit"),
        Binding("c", "open_create_bot", "Create Bot"),
        Binding("d", "delete_selected", "Delete Bot"),
        Binding("m", "toggle_monitor", "Monitor"),
        Binding("h", "show_help", "Help"),
    ]
    
    def __init__(self):
        super().__init__()
        
        # Initialize persistence layer
        db_path = Path("logs") / "hypertrail_bots.db"
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
        self.persistence = DatabasePersistence(str(db_path))

    async def on_mount(self) -> None:
        """Set up the main screen."""
        logger.info("[APP] HyperTrail TUI starting...")
        
        # Push the bot management screen with persistence layer
        main_screen = BotManagementScreen(persistence=self.persistence)
        self.push_screen(main_screen, callback=self._on_main_screen_ready)

    def _on_main_screen_ready(self, result=None):
        """Callback after main screen is loaded."""
        logger.info("[APP] Main bot management screen ready")
    
    def action_quit_app(self) -> None:
        """Exit the application."""
        self.exit()
        sys.exit(0)
    
    def action_open_create_bot(self) -> None:
        """Delegate to main screen to create bot."""
        if self.screen and hasattr(self.screen, 'open_create_bot'):
            self.screen.open_create_bot()
        else:
            self.notify("Opening create dialog...", severity="info")
    
    def action_delete_selected(self) -> None:
        """Delegate to main screen to delete selected bots."""
        if self.screen and hasattr(self.screen, 'delete_selected'):
            self.screen.delete_selected()
        else:
            self.notify("Please select a bot to delete", severity="warning")
    
    def action_toggle_monitor(self) -> None:
        """Toggle monitoring mode."""
        self.notify("✓ Monitoring mode activated", severity="success")
    
    def action_show_help(self) -> None:
        """Show help modal."""
        if self.screen and hasattr(self.screen, 'show_help'):
            self.screen.show_help()


async def run_with_debug():
    """Debug run function (kept for backwards compatibility)."""
    print("=" * 70)
    print("🚀 HYPERTRAIL TRAILING ORDER MANAGER")
    print("=" * 70)
    print()
    print(f"✅ Network: {config.NETWORK_MODE.upper()}")
    print(f"✅ API Configuration: {'Valid' if config.is_valid() else 'Invalid - Check credentials'}")
    print("✅ Database initialized at logs/hypertrail_bots.db")
    print("=" * 70)
    
    app = HyperTrailApp()
    try:
        await app.run_async()
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    """Main entry point for the TUI application."""
    try:
        asyncio.run(run_with_debug())
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"\n❌ Application crashed: {e}", file=sys.stderr)
        sys.exit(1)
