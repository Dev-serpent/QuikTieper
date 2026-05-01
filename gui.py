from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from fiona.bindings import parse_bindings
from fiona.config import load_config, save_config
from fiona.launcher import get_mouse_location


class ConfigEditorApp:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.root = tk.Tk()
        self.root.title("Fiona")
        self.root.geometry("1040x620")

        self.listener = None
        self.listener_running = False
        self.tree_index: dict[str, dict] = {}
        self._build_ui()
        self.root.bind_all("<Alt-c>", self.capture_mouse_position_hotkey)
        self.root.bind_all("<Alt-C>", self.capture_mouse_position_hotkey)
        self._load()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        bindings_tab = ttk.Frame(self.notebook, padding=12)
        json_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(bindings_tab, text="Bindings")
        self.notebook.add(json_tab, text="Raw JSON")

        self._build_bindings_tab(bindings_tab)
        self._build_json_tab(json_tab)

        footer = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        footer.grid(row=1, column=0, sticky="ew")
        footer.columnconfigure(1, weight=1)

        self.listener_var = tk.StringVar(value="Listener: stopped")
        self.status_var = tk.StringVar(value=f"Config: {self.config_path}")

        ttk.Label(footer, textvariable=self.listener_var).grid(row=0, column=0, sticky="w", padx=(0, 18))
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=1, sticky="w")
        self.listener_button = ttk.Button(footer, text="Start Listener", command=self.toggle_listener)
        self.listener_button.grid(row=0, column=2, sticky="e", padx=(12, 6))
        ttk.Button(footer, text="Save All", command=self.save_all).grid(row=0, column=3, sticky="e")

    def _build_bindings_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        left = ttk.Frame(parent)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        self.binding_tree = ttk.Treeview(left, show="tree")
        self.binding_tree.grid(row=0, column=0, sticky="nsew")
        self.binding_tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        actions = ttk.Frame(left)
        actions.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for index in range(4):
            actions.columnconfigure(index, weight=1)
        ttk.Button(actions, text="Add App", command=self.add_app).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="Add Shortcut", command=self.add_shortcut).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(actions, text="Delete", command=self.delete_selected).grid(row=0, column=2, sticky="ew", padx=6)
        ttk.Button(actions, text="Save Selected", command=self.save_selected).grid(
            row=0, column=3, sticky="ew", padx=(6, 0)
        )

        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        app_frame = ttk.LabelFrame(right, text="App", padding=12)
        app_frame.grid(row=0, column=0, sticky="ew")
        app_frame.columnconfigure(1, weight=1)

        ttk.Label(app_frame, text="App Name").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(app_frame, text="Window Match").grid(row=1, column=0, sticky="w", pady=6)

        self.app_name_var = tk.StringVar()
        self.window_match_var = tk.StringVar()

        ttk.Entry(app_frame, textvariable=self.app_name_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Entry(app_frame, textvariable=self.window_match_var).grid(row=1, column=1, sticky="ew", pady=6)

        binding_frame = ttk.LabelFrame(right, text="Binding", padding=12)
        binding_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        binding_frame.columnconfigure(1, weight=1)

        ttk.Label(binding_frame, text="Binding Name").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(binding_frame, text="Keys").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(binding_frame, text="Run Command").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Label(binding_frame, text="Instruction").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Label(binding_frame, text="Fiona Cmds").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Label(binding_frame, text="Cooldown").grid(row=5, column=0, sticky="w", pady=6)

        self.binding_name_var = tk.StringVar()
        self.keys_var = tk.StringVar()
        self.command_var = tk.StringVar()
        self.instruction_var = tk.StringVar()
        self.fiona_cmds_var = tk.StringVar()
        self.cooldown_var = tk.StringVar(value="0.8")

        ttk.Entry(binding_frame, textvariable=self.binding_name_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Entry(binding_frame, textvariable=self.keys_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Entry(binding_frame, textvariable=self.command_var).grid(row=2, column=1, sticky="ew", pady=6)
        ttk.Entry(binding_frame, textvariable=self.instruction_var).grid(row=3, column=1, sticky="ew", pady=6)
        ttk.Entry(binding_frame, textvariable=self.fiona_cmds_var).grid(row=4, column=1, sticky="ew", pady=6)
        ttk.Entry(binding_frame, textvariable=self.cooldown_var).grid(row=5, column=1, sticky="ew", pady=6)

        command_actions = ttk.Frame(binding_frame)
        command_actions.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        command_actions.columnconfigure(0, weight=1)
        command_actions.columnconfigure(1, weight=1)
        ttk.Button(command_actions, text="Capture Mouse Position", command=self.capture_mouse_position).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ttk.Button(command_actions, text="Clear Instruction", command=self.clear_instruction).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        hint = (
            "Select an app node to edit app metadata.\n"
            "Select Launch or a shortcut under an app to edit that binding.\n"
            "Press Alt+C inside this window to capture the current mouse position.\n"
            "Use instruction like mouse:1200,420 to move the pointer first.\n"
            "Fiona Cmds accepts values like mouse-left-click, mouse-right-click."
        )
        ttk.Label(binding_frame, text=hint, justify="left").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )

    def _build_json_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.json_text = tk.Text(parent, wrap="none")
        self.json_text.grid(row=0, column=0, sticky="nsew")

        buttons = ttk.Frame(parent)
        buttons.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="Reload From Disk", command=self._load).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(buttons, text="Validate JSON", command=self.validate_json).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _load(self) -> None:
        self.config = load_config(self.config_path)
        self._refresh_tree()
        self._refresh_json_text()
        self._clear_form()
        self.status_var.set(f"Loaded {self.config_path}")

    def _refresh_tree(self) -> None:
        self.binding_tree.delete(*self.binding_tree.get_children())
        self.tree_index.clear()
        for app_index, app in enumerate(self.config.get("apps", [])):
            app_id = self.binding_tree.insert("", tk.END, text=app["name"], open=True)
            self.tree_index[app_id] = {"kind": "app", "app_index": app_index}

            launch = app.get("launch", {})
            launch_keys = " + ".join(launch.get("keys", []))
            launch_id = self.binding_tree.insert(app_id, tk.END, text=f"Launch [{launch_keys}]")
            self.tree_index[launch_id] = {
                "kind": "launch",
                "app_index": app_index,
            }

            for shortcut_index, shortcut in enumerate(app.get("shortcuts", [])):
                shortcut_keys = " + ".join(shortcut.get("keys", []))
                shortcut_id = self.binding_tree.insert(
                    app_id,
                    tk.END,
                    text=f"{shortcut.get('name', 'shortcut')} [{shortcut_keys}]",
                )
                self.tree_index[shortcut_id] = {
                    "kind": "shortcut",
                    "app_index": app_index,
                    "shortcut_index": shortcut_index,
                }

    def _refresh_json_text(self) -> None:
        self.json_text.delete("1.0", tk.END)
        self.json_text.insert("1.0", json.dumps(self.config, indent=2))

    def _clear_form(self) -> None:
        self.app_name_var.set("")
        self.window_match_var.set("")
        self.binding_name_var.set("")
        self.keys_var.set("")
        self.command_var.set("")
        self.instruction_var.set("")
        self.fiona_cmds_var.set("")
        self.cooldown_var.set("0.8")

    def _selected_item(self) -> tuple[str | None, dict | None]:
        selection = self.binding_tree.selection()
        if not selection:
            return None, None
        item_id = selection[0]
        return item_id, self.tree_index.get(item_id)

    def on_tree_select(self, _event: object) -> None:
        _item_id, info = self._selected_item()
        if info is None:
            return

        app = self.config["apps"][info["app_index"]]
        self.app_name_var.set(app.get("name", ""))
        self.window_match_var.set(app.get("window_match", ""))

        if info["kind"] == "app":
            self.binding_name_var.set("")
            self.keys_var.set("")
            self.command_var.set("")
            self.instruction_var.set("")
            self.fiona_cmds_var.set("")
            self.cooldown_var.set("0.8")
            return

        binding = app["launch"] if info["kind"] == "launch" else app["shortcuts"][info["shortcut_index"]]
        self.binding_name_var.set(binding.get("name", ""))
        self.keys_var.set(", ".join(binding.get("keys", [])))
        self.command_var.set(binding.get("cmd", ""))
        self.instruction_var.set(binding.get("instruction", ""))
        self.fiona_cmds_var.set(", ".join(binding.get("fiona_cmds", binding.get("quiktieper_cmds", []))))
        self.cooldown_var.set(str(binding.get("cooldown_seconds", 0.8)))

    def add_app(self) -> None:
        app = {
            "name": "new-app",
            "window_match": "",
            "launch": {
                "name": "launch",
                "keys": ["alt"],
                "cmd": "",
                "instruction": "",
                "fiona_cmds": [],
                "cooldown_seconds": 0.8,
            },
            "shortcuts": [],
        }
        self.config.setdefault("apps", []).append(app)
        self._refresh_tree()
        self._refresh_json_text()
        self.status_var.set("Added app")

    def add_shortcut(self) -> None:
        _item_id, info = self._selected_item()
        if info is None:
            messagebox.showwarning("No selection", "Select an app or one of its bindings first.")
            return

        app = self.config["apps"][info["app_index"]]
        app.setdefault("shortcuts", []).append(
            {
                "name": "new-shortcut",
                "keys": ["alt"],
                "cmd": "",
                "instruction": "",
                "fiona_cmds": [],
                "cooldown_seconds": 0.8,
            }
        )
        self._refresh_tree()
        self._refresh_json_text()
        self.status_var.set(f"Added shortcut under {app['name']}")

    def delete_selected(self) -> None:
        _item_id, info = self._selected_item()
        if info is None:
            messagebox.showwarning("No selection", "Select an app or shortcut to delete.")
            return

        if info["kind"] == "app":
            del self.config["apps"][info["app_index"]]
        elif info["kind"] == "shortcut":
            del self.config["apps"][info["app_index"]]["shortcuts"][info["shortcut_index"]]
        else:
            messagebox.showwarning("Protected binding", "Each app must keep its Launch binding.")
            return

        self._refresh_tree()
        self._refresh_json_text()
        self._clear_form()
        self.status_var.set("Deleted selection")

    def save_selected(self) -> None:
        _item_id, info = self._selected_item()
        if info is None:
            messagebox.showwarning("No selection", "Select an app or binding to save.")
            return

        app = self.config["apps"][info["app_index"]]
        app_name = self.app_name_var.get().strip()
        window_match = self.window_match_var.get().strip().lower()
        if not app_name:
            messagebox.showerror("Missing app name", "App name is required.")
            return

        app["name"] = app_name
        app["window_match"] = window_match

        if info["kind"] != "app":
            binding = self._binding_from_form()
            if binding is None:
                return
            if info["kind"] == "launch":
                app["launch"] = binding
            else:
                app["shortcuts"][info["shortcut_index"]] = binding

        self._refresh_tree()
        self._refresh_json_text()
        self.status_var.set("Saved selection into editor state")

    def validate_json(self) -> None:
        try:
            json.loads(self.json_text.get("1.0", tk.END))
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", str(exc))
            return
        messagebox.showinfo("Valid JSON", "The raw JSON tab is valid.")

    def save_all(self) -> None:
        if self.notebook.tab(self.notebook.select(), "text") == "Bindings":
            if self.binding_tree.selection():
                self.save_selected()
            parsed = self.config
        else:
            try:
                parsed = json.loads(self.json_text.get("1.0", tk.END))
            except json.JSONDecodeError as exc:
                messagebox.showerror("Invalid JSON", f"Fix the raw JSON first.\n\n{exc}")
                return

        save_config(parsed, self.config_path)
        self.config = load_config(self.config_path)
        self._refresh_tree()
        self._refresh_json_text()
        if self.listener_running:
            self._restart_listener()
        self.status_var.set(f"Saved {self.config_path}")

    def toggle_listener(self) -> None:
        if self.listener_running:
            self._stop_listener()
            return
        self._start_listener()

    def _start_listener(self) -> None:
        try:
            from fiona.listener import ChordListener
        except Exception as exc:
            messagebox.showerror("Listener error", f"Could not import keyboard hook.\n\n{exc}")
            return

        try:
            bindings = parse_bindings(self.config.get("apps", []))
            self.listener = ChordListener(bindings)
            self.listener.start()
        except Exception as exc:
            self.listener = None
            messagebox.showerror("Listener error", f"Could not start listener.\n\n{exc}")
            return

        self.listener_running = True
        self.listener_var.set("Listener: running")
        self.listener_button.configure(text="Stop Listener")
        self.status_var.set("Global chord listener is active")

    def _stop_listener(self) -> None:
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception as exc:
                messagebox.showerror("Listener error", f"Could not stop listener cleanly.\n\n{exc}")
                return

        self.listener = None
        self.listener_running = False
        self.listener_var.set("Listener: stopped")
        self.listener_button.configure(text="Start Listener")
        self.status_var.set("Global chord listener is stopped")

    def _restart_listener(self) -> None:
        self._stop_listener()
        self._start_listener()

    def _binding_from_form(self) -> dict | None:
        name = self.binding_name_var.get().strip()
        command = self.command_var.get().strip()
        instruction = self.instruction_var.get().strip()
        fiona_cmds = [item.strip() for item in self.fiona_cmds_var.get().split(",") if item.strip()]
        keys = [key.strip().lower() for key in self.keys_var.get().split(",") if key.strip()]
        cooldown_text = self.cooldown_var.get().strip()

        if not name or not keys:
            messagebox.showerror("Missing fields", "Binding name and keys are required.")
            return None

        if not command and not instruction and not fiona_cmds:
            messagebox.showerror(
                "Missing action",
                "Provide at least one of Run Command, Instruction, or Fiona Cmds.",
            )
            return None

        try:
            cooldown_seconds = float(cooldown_text)
        except ValueError:
            messagebox.showerror("Invalid cooldown", "Cooldown must be a number.")
            return None

        return {
            "name": name,
            "keys": keys,
            "cmd": command,
            "instruction": instruction,
            "fiona_cmds": fiona_cmds,
            "cooldown_seconds": cooldown_seconds,
        }

    def capture_mouse_position(self) -> None:
        position = get_mouse_location()
        if position is None:
            messagebox.showerror("Mouse capture failed", "Could not read the current mouse position from xdotool.")
            return
        x_pos, y_pos = position
        self.instruction_var.set(f"mouse:{x_pos},{y_pos}")
        self.status_var.set(f"Captured mouse position {x_pos},{y_pos}")

    def capture_mouse_position_hotkey(self, _event: tk.Event[tk.Misc]) -> str:
        self.capture_mouse_position()
        return "break"

    def clear_instruction(self) -> None:
        self.instruction_var.set("")
        self.status_var.set("Cleared instruction")

    def _on_close(self) -> None:
        if self.listener_running:
            self._stop_listener()
        self.root.destroy()


def launch_editor(config_path: Path) -> None:
    ConfigEditorApp(config_path).run()
