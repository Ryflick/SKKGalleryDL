import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import os
import json
import threading
import sys
import re

# Configuration file to store settings
CONFIG_FILE = "gallery_dl_config.json"

# Global variable to store the subprocess
process = None

# Supported browsers for the --option browser=<value>
SUPPORTED_BROWSERS = ["firefox", "chrome", "edge", "safari"]

def sanitize_directory_name(tags):
    """Sanitize the tags to create a valid directory name."""
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", tags)  # Remove invalid characters
    sanitized = re.sub(r'\s+', "_", sanitized)  # Replace spaces with underscores
    return sanitized

def run_gallery_dl():
    global process

    tags = tags_entry.get()
    directory = directory_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    browser = browser_combobox.get()

    if not tags or not directory or not username or not password:
        messagebox.showerror("Error", "Please fill in all fields!")
        return

    # Sanitize tags to create a valid sub-directory name
    sub_directory_name = sanitize_directory_name(tags)
    sub_directory = os.path.join(directory, sub_directory_name)

    # Create the sub-directory if it doesn't exist
    os.makedirs(sub_directory, exist_ok=True)

    # Save settings to config file
    save_settings(tags, directory, username, password, browser)

    command = [
        "gallery-dl",
        "-u", username,
        "-p", password,
        f"https://chan.sankakucomplex.com/?tags={tags}&commit=Search",
        "-o", f"browser={browser}",
        "-f", "/O",
        "-D", sub_directory,  # Use the sub-directory
        "--sleep", "1",
        "--download-archive", "Sankaku"
    ]

    # Clear the output text widget
    output_text.delete(1.0, tk.END)

    try:
        # Start the subprocess and capture its output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # Hide console on Windows
        )

        # Start a thread to read the output
        threading.Thread(target=read_output, args=(process,), daemon=True).start()
        result_label.config(text="Download started...", fg="green")
    except Exception as e:
        result_label.config(text=f"Error: {e}", fg="red")

def stop_gallery_dl():
    global process
    if process:
        try:
            # Terminate the subprocess
            process.terminate()
            process.wait(timeout=5)  # Wait for the process to terminate
            result_label.config(text="Download stopped.", fg="orange")
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate
            process.kill()
            result_label.config(text="Download force-stopped.", fg="red")
        process = None

def read_output(process):
    """Read the output from the subprocess and display it in the text widget."""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            output_text.insert(tk.END, output)
            output_text.see(tk.END)  # Auto-scroll to the end
            output_text.update_idletasks()  # Update the GUI

    # Read any remaining output after the process ends
    remaining_output = process.stdout.read()
    if remaining_output:
        output_text.insert(tk.END, remaining_output)
        output_text.see(tk.END)
        output_text.update_idletasks()

    # Check if the process ended with an error
    if process.poll() != 0:
        error_output = process.stderr.read()
        if error_output:
            output_text.insert(tk.END, f"Error: {error_output}", fg="red")
            output_text.see(tk.END)
            output_text.update_idletasks()

def browse_directory():
    directory = filedialog.askdirectory()
    directory_entry.delete(0, tk.END)
    directory_entry.insert(0, directory)

def save_settings(tags, directory, username, password, browser):
    settings = {
        "tags": tags,
        "directory": directory,
        "username": username,
        "password": password,
        "browser": browser
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f)

def load_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            settings = json.load(f)
            tags_entry.insert(0, settings.get("tags", ""))
            directory_entry.insert(0, settings.get("directory", ""))
            username_entry.insert(0, settings.get("username", ""))
            password_entry.insert(0, settings.get("password", ""))
            browser_combobox.set(settings.get("browser", "firefox"))

# Create the main window
root = tk.Tk()
root.title("Sankaku Complex Downloader")

# Make the window compact
root.geometry("600x400")  # Set a smaller initial size

# Create and place the labels and entries in a compact layout
tk.Label(root, text="Tags:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
tags_entry = tk.Entry(root, width=40)
tags_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(root, text="Directory:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
directory_entry = tk.Entry(root, width=40)
directory_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
tk.Button(root, text="Browse", command=browse_directory).grid(row=1, column=2, padx=5, pady=5)

tk.Label(root, text="Username:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
username_entry = tk.Entry(root, width=40)
username_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

tk.Label(root, text="Password:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
password_entry = tk.Entry(root, width=40, show="*")
password_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

# Create and place the browser selection dropdown
tk.Label(root, text="Browser:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
browser_combobox = ttk.Combobox(root, values=SUPPORTED_BROWSERS, width=37)
browser_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="w")
browser_combobox.set("firefox")  # Default value

# Create and place the run and stop buttons
tk.Button(root, text="Run", command=run_gallery_dl).grid(row=5, column=1, pady=10, sticky="w")
tk.Button(root, text="Stop", command=stop_gallery_dl).grid(row=5, column=1, pady=10, sticky="e")

# Create and place the result label
result_label = tk.Label(root, text="", fg="green")
result_label.grid(row=6, column=1, pady=5)

# Create a smaller scrolled text widget for output
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=10)
output_text.grid(row=7, column=0, columnspan=3, padx=5, pady=5)

# Load saved settings
load_settings()

# Start the main loop
root.mainloop()