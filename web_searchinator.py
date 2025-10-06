# -*- coding: utf-8 -*-
"""
The Web Search-inator (Auto Search Tool)
Supports English and Devanagari script - paste your client list and go!
Automatically opens Google searches for all clients
Now with persistent settings saved to AppData!
FIXED: Devanagari input now works properly!
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import webbrowser
import time
import urllib.parse
import threading
from datetime import datetime, timedelta
import os
import sys
import json

# Helper function to compute last N days as Google tbs parameter
def get_last_n_days_param(n: int) -> str:
    end_date = datetime.today()
    start_date = end_date - timedelta(days=n)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    return f"cdr:1,cd_min:{start_str},cd_max:{end_str}"


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_appdata_path():
    """Get the AppData path for storing settings"""
    if sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
    elif sys.platform == 'darwin':
        appdata = os.path.expanduser('~/Library/Application Support')
    else:
        appdata = os.path.expanduser('~/.config')
    
    app_folder = os.path.join(appdata, 'WebSearchinator')
    os.makedirs(app_folder, exist_ok=True)
    return app_folder


class GoaNewsSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("The Web Search-inator")
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        
        # Settings file path
        self.settings_file = os.path.join(get_appdata_path(), 'settings.json')
        
        # Set window icon
        self.set_window_icon()
        
        # Configure style
        self.setup_styles()
        
        # Variables
        self.clients = []
        self.is_searching = False
        
        # Create GUI
        self.create_widgets()
        
        # Load saved settings
        self.load_settings()
        
        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def set_window_icon(self):
        """Set the window icon from icon.png"""
        try:
            icon_path = get_resource_path('icon.png')
            
            if os.path.exists(icon_path):
                from PIL import Image, ImageTk
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, self.icon_photo)
                
        except ImportError:
            try:
                icon_path = get_resource_path('icon.png')
                if os.path.exists(icon_path):
                    self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
            except Exception:
                pass
        except Exception:
            pass
        
    def setup_styles(self):
        """Setup GUI styling"""
        self.root.configure(bg="#8f8ce8")
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
    
    def get_devanagari_font(self):
        """Find an appropriate font that supports Devanagari script"""
        import tkinter.font as tkfont
        
        # List of fonts known to support Devanagari (prioritized)
        devanagari_fonts = [
            'Nirmala UI',
            'Mangal',
            'Aparajita',
            'Kokila',
            'Utsaah',
            'Sanskrit Text',
            'Devanagari MT',
            'Kohinoor Devanagari',
            'Noto Sans Devanagari',
            'Arial Unicode MS',
            'Segoe UI',
            'Microsoft Sans Serif'
        ]
        
        available_fonts = tkfont.families()
        
        # Try to find a Devanagari-supporting font
        for font in devanagari_fonts:
            if font in available_fonts:
                return (font, 11)
        
        # Fallback
        return ('TkDefaultFont', 11)
    
    def load_settings(self):
        """Load settings from AppData"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Load client list
                if 'client_list' in settings:
                    self.client_text.delete('1.0', 'end')
                    self.client_text.insert('1.0', settings['client_list'])
                
                # Load search term
                if 'search_term' in settings:
                    self.search_term_var.set(settings['search_term'])
                
                # Load time period
                if 'time_period' in settings:
                    self.time_var.set(settings['time_period'])
                
                # Load delay
                if 'delay' in settings:
                    self.delay_var.set(settings['delay'])
                
                # Load batch size
                if 'batch_size' in settings:
                    self.batch_var.set(settings['batch_size'])
                
                self.update_client_count()
                self.log_message("✅ Settings loaded from AppData")
        except Exception as e:
            self.log_message(f"⚠️ Could not load settings: {e}")
    
    def save_settings(self):
        """Save settings to AppData"""
        try:
            settings = {
                'client_list': self.client_text.get('1.0', 'end-1c'),
                'search_term': self.search_term_var.get(),
                'time_period': self.time_var.get(),
                'delay': self.delay_var.get(),
                'batch_size': self.batch_var.get()
            }
            
            # Use ensure_ascii=False to properly save Devanagari and other Unicode characters
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False
    
    def on_closing(self):
        """Handle window closing event"""
        self.save_settings()
        self.root.destroy()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Create main container with scrollbar
        main_container = tk.Frame(self.root, bg="#7bceff")
        main_container.pack(fill='both', expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_container, bg='#7bceff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#7bceff')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Title
        title_frame = tk.Frame(scrollable_frame, bg='#7bceff')
        title_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = tk.Label(title_frame, 
                              text="🚀 The Web Search-inator", 
                              font=('Arial', 16, 'bold'),
                              bg='#7bceff',
                              fg="#000000")
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Supports English script",
                                 font=('Nirmala UI', 10),
                                 bg='#7bceff',
                                 fg="#182122")
        subtitle_label.pack()
        
        # Client input section
        input_frame = tk.LabelFrame(scrollable_frame, text="📝 Client List", 
                                   font=('Arial', 12, 'bold'),
                                   padx=10, pady=10)
        input_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Instructions with file import button
        instructions_frame = tk.Frame(input_frame)
        instructions_frame.pack(fill='x', pady=(0, 5))
        
        instructions = tk.Label(instructions_frame,
                               text="Type or paste your client list below (one name per line):",
                               font=('Arial', 10),
                               justify='left')
        instructions.pack(side='left')
        
        import_btn = tk.Button(instructions_frame,
                              text="📁 Import from File",
                              command=self.import_from_file,
                              font=('Arial', 9),
                              bg='#7bceff',
                              fg='white',
                              padx=10,
                              pady=2)
        import_btn.pack(side='right')
        
        # Text area for clients - FIXED for Devanagari input
        text_container = tk.Frame(input_frame)
        text_container.pack(fill='both', expand=True, pady=5)
        
        # Get Devanagari font
        devanagari_font = self.get_devanagari_font()
        
        # Create Text widget with scrollbar
        text_scroll = tk.Scrollbar(text_container)
        text_scroll.pack(side='right', fill='y')
        
        # FIXED: Added insertunfocussed='solid' to prevent IME issues
        self.client_text = tk.Text(text_container,
                                   height=8,
                                   width=70,
                                   font=devanagari_font,
                                   wrap='word',
                                   yscrollcommand=text_scroll.set,
                                   insertunfocussed='solid',  # This helps with IME
                                   undo=True,  # Enable undo
                                   maxundo=-1)  # Unlimited undo
        self.client_text.pack(side='left', fill='both', expand=True)
        text_scroll.config(command=self.client_text.yview)
        
        # FIXED: Bind proper events for text changes that work with IME
        self.client_text.bind('<KeyRelease>', self.on_text_modified)
        # Remove <<Modified>> binding as it can interfere with IME
        
        # Counter label
        self.count_label = tk.Label(input_frame,
                                    text="Clients: 0",
                                    font=('Arial', 9),
                                    fg='#7bceff')
        self.count_label.pack(anchor='e', pady=(2, 0))
        
        # Search term customization
        search_term_frame = tk.LabelFrame(scrollable_frame, text="🔍 Search Terms",
                                         font=('Arial', 12, 'bold'),
                                         padx=10, pady=10)
        search_term_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(search_term_frame, 
                text="Add custom search terms after client name:",
                font=('Arial', 10)).pack(anchor='w', pady=(0, 5))
        
        self.search_term_var = tk.StringVar(value="Goa news")
        self.search_term_var.trace('w', self.on_setting_changed)
        
        # FIXED: Use Entry with better IME support
        search_term_entry = tk.Entry(search_term_frame, 
                                     textvariable=self.search_term_var,
                                     font=devanagari_font,
                                     width=40)
        search_term_entry.pack(anchor='w')
        
        tk.Label(search_term_frame,
                text='Example: "news" will search for "Client Name news"',
                font=('Arial', 8),
                fg='#7f8c8d').pack(anchor='w', pady=(2, 0))
        
        # Time period section
        time_frame = tk.LabelFrame(scrollable_frame, text="⏰ Time Period", 
                                  font=('Arial', 12, 'bold'),
                                  padx=10, pady=10)
        time_frame.pack(fill='x', padx=10, pady=5)
        
        self.time_var = tk.StringVar(value="qdr:d")
        self.time_var.trace('w', self.on_setting_changed)
        
        # Time options in a grid
        time_options = [
            ("Last 24 hours", "qdr:d"),
            ("Last 2 days", get_last_n_days_param(2)),
            ("Last 3 days", get_last_n_days_param(3)),
            ("Last 4 days", get_last_n_days_param(4)),
            ("Last week", "qdr:w"),
            ("Last month", "qdr:m"),
            ("Last year", "qdr:y"),
            ("Any time", "")
        ]
        
        # Create grid layout for radio buttons
        time_grid = tk.Frame(time_frame)
        time_grid.pack(fill='x')
        
        for i, (text, value) in enumerate(time_options):
            rb = tk.Radiobutton(time_grid,
                               text=text,
                               variable=self.time_var,
                               value=value,
                               font=('Arial', 10))
            rb.grid(row=i//2, column=i%2, sticky='w', padx=5, pady=2)
        
        # Settings section
        settings_frame = tk.LabelFrame(scrollable_frame, text="⚙️ Settings",
                                      font=('Arial', 12, 'bold'),
                                      padx=10, pady=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Delay setting
        delay_frame = tk.Frame(settings_frame)
        delay_frame.pack(fill='x', pady=2)
        
        tk.Label(delay_frame, text="Delay between tabs (seconds):", 
                font=('Arial', 10)).pack(side='left')
        
        self.delay_var = tk.StringVar(value="2")
        self.delay_var.trace('w', self.on_setting_changed)
        delay_entry = tk.Entry(delay_frame, textvariable=self.delay_var, width=10)
        delay_entry.pack(side='right')
        
        # Batch size setting
        batch_frame = tk.Frame(settings_frame)
        batch_frame.pack(fill='x', pady=2)
        
        tk.Label(batch_frame, text="Open tabs in batches of:", 
                font=('Arial', 10)).pack(side='left')
        
        self.batch_var = tk.StringVar(value="10")
        self.batch_var.trace('w', self.on_setting_changed)
        batch_entry = tk.Entry(batch_frame, textvariable=self.batch_var, width=10)
        batch_entry.pack(side='right')
        
        tk.Label(settings_frame,
                text="(Pause after each batch to avoid browser overload)",
                font=('Arial', 8),
                fg='#7f8c8d').pack(anchor='w')
        
        # Buttons section
        button_frame = tk.Frame(scrollable_frame, bg="#ed9393")
        button_frame.pack(fill='x', padx=10, pady=10)
        
        self.search_button = tk.Button(button_frame,
                                      text="🔍 Start Search",
                                      command=self.start_search,
                                      font=('Arial', 12, 'bold'),
                                      bg='#3498db',
                                      fg='white',
                                      padx=20,
                                      pady=10)
        self.search_button.pack(side='left', padx=5)
        
        self.clear_button = tk.Button(button_frame,
                                     text="🗑️ Clear",
                                     command=self.clear_clients,
                                     font=('Arial', 12),
                                     bg='#e74c3c',
                                     fg='white',
                                     padx=20,
                                     pady=10)
        self.clear_button.pack(side='left', padx=5)
        
        save_btn = tk.Button(button_frame,
                            text="💾 Save List",
                            command=self.save_to_file,
                            font=('Arial', 12),
                            bg='#16a085',
                            fg='white',
                            padx=20,
                            pady=10)
        save_btn.pack(side='left', padx=5)
        
        # Status section
        status_frame = tk.LabelFrame(scrollable_frame, text="📊 Status",
                                    font=('Arial', 12, 'bold'),
                                    padx=10, pady=5)
        status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame,
                                                    height=8,
                                                    width=70,
                                                    font=('Consolas', 9),
                                                    bg='#2c3e50',
                                                    fg='#7bceff',
                                                    wrap='word')
        self.status_text.pack(fill='both', expand=True, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(scrollable_frame, mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
        # Initial status message
        self.log_message("Ready! Enter your clients and click 'Start Search'")
        self.log_message(f"💾 Settings saved to: {get_appdata_path()}")
        self.log_message(f"🔤 Font used: {devanagari_font[0]}")
        self.log_message("✅ Devanagari input enabled - you can type in Hindi!")
    
    def on_text_modified(self, event=None):
        """Handle text modifications"""
        self.update_client_count()
        # Use after_idle to avoid too frequent saves while typing
        if hasattr(self, '_save_job'):
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(1000, self.save_settings)
    
    def on_setting_changed(self, *args):
        """Auto-save when any setting changes"""
        self.save_settings()
        
    def update_client_count(self, event=None):
        """Update the client counter"""
        clients = self.get_clients_from_text()
        self.count_label.config(text=f"Clients: {len(clients)}")
    
    def import_from_file(self):
        """Import client list from a text file"""
        filename = filedialog.askopenfilename(
            title="Select Client List File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.client_text.delete('1.0', 'end')
                    self.client_text.insert('1.0', content)
                    self.log_message(f"Imported from: {os.path.basename(filename)}")
                    self.update_client_count()
                    self.save_settings()
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import file: {e}")
    
    def save_to_file(self):
        """Save client list to a text file"""
        filename = filedialog.asksaveasfilename(
            title="Save Client List",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                content = self.client_text.get('1.0', 'end-1c')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_message(f"Saved to: {os.path.basename(filename)}")
                messagebox.showinfo("Success", "Client list saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {e}")
        
    def log_message(self, message):
        """Add message to status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        self.root.update()
        
    def clear_clients(self):
        """Clear the client text area"""
        self.client_text.delete('1.0', 'end')
        self.log_message("Client list cleared")
        self.update_client_count()
        self.save_settings()
        
    def get_clients_from_text(self):
        """Extract clients from text area"""
        text_content = self.client_text.get('1.0', 'end-1c')
        clients = []
        
        for line in text_content.split('\n'):
            line = line.strip()
            if line:
                clients.append(line)
                
        return clients
    
    def create_search_query(self, client_name):
        """Create a Google search query for client + custom search terms"""
        search_term = self.search_term_var.get().strip()
        if search_term:
            return f'"{client_name}" {search_term}'
        else:
            return f'"{client_name}"'
    
    def create_search_url(self, query, time_param=""):
        """Create complete Google search URL"""
        encoded_query = urllib.parse.quote_plus(query)
        google_url = f"https://www.google.com/search?q={encoded_query}"
        if time_param:
            google_url += f"&tbs={time_param}"
        return google_url
    
    def open_google_search(self, query, time_param="", delay=1.0):
        """Open a Google search in the browser"""
        try:
            search_url = self.create_search_url(query, time_param)
            webbrowser.open(search_url)
            self.log_message(f"🔍 Opened: {query}")
            time.sleep(delay)
            return True
        except Exception as e:
            self.log_message(f"❌ Error opening search for '{query}': {e}")
            return False
    
    def search_worker(self):
        """Worker function for search operations (runs in separate thread)"""
        try:
            clients = self.get_clients_from_text()
            if not clients:
                messagebox.showwarning("No Clients", "Please enter some client names first!")
                return
            
            # Get settings
            time_param = self.time_var.get()
            try:
                delay = float(self.delay_var.get())
            except ValueError:
                delay = 1.5
                self.log_message("Invalid delay, using 1.5 seconds")
            
            try:
                batch_size = int(self.batch_var.get())
                if batch_size < 1:
                    batch_size = 10
            except ValueError:
                batch_size = 10
                self.log_message("Invalid batch size, using 10")
            
            # Generate queries
            queries = [self.create_search_query(client) for client in clients]
            
            self.log_message(f"✅ Found {len(clients)} clients")
            self.log_message(f"⚠️ Will open {len(queries)} browser tabs in batches of {batch_size}")
            
            # Show preview
            self.log_message("🔍 Preview of searches:")
            for i, query in enumerate(queries[:3], 1):
                self.log_message(f"  {i}. {query}")
            if len(queries) > 3:
                self.log_message(f"  ... and {len(queries) - 3} more")
            
            # Ask for confirmation
            if len(queries) > 10:
                response = messagebox.askyesno("Confirm", 
                    f"This will open {len(queries)} browser tabs.\n\nContinue?")
                if not response:
                    self.log_message("❌ Search cancelled by user")
                    return
            
            # Configure progress bar
            self.progress['maximum'] = len(queries)
            self.progress['value'] = 0
            
            # Perform searches
            self.log_message("🔄 Starting searches...")
            successful_opens = 0
            
            for i, query in enumerate(queries):
                if not self.is_searching:
                    break
                
                # Batch pause
                if i > 0 and i % batch_size == 0:
                    self.log_message(f"⏸️ Batch complete ({i}/{len(queries)}). Pausing 3 seconds...")
                    time.sleep(3)
                    
                if self.open_google_search(query, time_param, delay):
                    successful_opens += 1
                
                # Update progress bar
                self.progress['value'] = i + 1
                self.root.update_idletasks()
            
            # Summary
            self.log_message("=" * 50)
            self.log_message("📊 SEARCH SUMMARY")
            self.log_message("=" * 50)
            self.log_message(f"Total clients: {len(clients)}")
            self.log_message(f"Browser tabs opened: {successful_opens}/{len(queries)}")
            
            if successful_opens < len(queries):
                self.log_message(f"⚠️ {len(queries) - successful_opens} searches failed")
            else:
                self.log_message("✅ All searches opened successfully!")
                
            self.log_message("🎉 Done! Check your browser tabs.")
            
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")
        
        finally:
            self.progress['value'] = 0
            self.is_searching = False
            self.search_button.config(text="🔍 Start Search", state='normal')
    
    def start_search(self):
        """Start the search process"""
        if self.is_searching:
            self.is_searching = False
            self.search_button.config(text="🔍 Start Search")
            self.log_message("⚠️ Cancelling search...")
            return
        
        self.is_searching = True
        self.search_button.config(text="⏹️ Cancel", state='normal')
        
        self.status_text.delete('1.0', 'end')
        self.log_message("🚀 The Web Search-inator")
        
        search_thread = threading.Thread(target=self.search_worker)
        search_thread.daemon = True
        search_thread.start()


def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = GoaNewsSearchGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")