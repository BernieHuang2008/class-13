import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import yaml
import csv
import pandas as pd
import os
import glob
from PIL import Image, ImageTk, ImageDraw, ImageFont
import shutil
from crypto_utils import (load_encrypted_text_file, save_encrypted_text_file,
                         load_encrypted_binary_file, save_encrypted_binary_file)
from io import StringIO, BytesIO

class PasswordDialog:
    def __init__(self, parent=None, mode=1):
        self.result = None
        self.password = ""
        self.mode = mode  # 0: normal mode, 1: blind input mode
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title("密码验证 - Password Authentication")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Center the window
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make window modal
        if parent:
            self.dialog.focus_set()
        
        self.setup_ui()
        
        # Bind window close event
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # In blind mode, disable all keyboard input to the dialog
        if self.mode == 1:
            self.dialog.bind('<Key>', lambda e: "break")
            self.dialog.bind('<KeyPress>', lambda e: "break")
            self.dialog.bind('<KeyRelease>', lambda e: "break")
        
        # Center window on screen
        self.center_window()
    
    def center_window(self):
        """Center the dialog window on screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the password dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_text = "请输入密码 / Enter Password"
        
        title_label = ttk.Label(main_frame, text=title_text,
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Password input frame (only show in normal mode)
        input_frame = ttk.LabelFrame(main_frame, text="密码输入 / Password Input", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        if self.mode == 0:
            # Password entry
            self.password_var = tk.StringVar()
            self.password_entry = ttk.Entry(input_frame, textvariable=self.password_var,
                                           show="*", font=("Arial", 14), width=30)
            self.password_entry.pack(pady=(0, 10))
            self.password_entry.bind('<Return>', lambda e: self.on_ok())
            
            # Show/Hide password button
            self.show_password = tk.BooleanVar()
            show_check = ttk.Checkbutton(input_frame, text="显示密码 / Show Password",
                                        variable=self.show_password, command=self.toggle_password)
            show_check.pack(anchor=tk.W)
        else:
            # In blind mode, create hidden password variable and disable keyboard input
            self.password_var = tk.StringVar()
            self.password_entry = None
            self.show_password = tk.BooleanVar()
            
            
            instruction_text = "盲输模式：密码不可见，仅可通过虚拟键盘输入\nBlind Input Mode: Password invisible, virtual keyboard only"
            instruction_label = ttk.Label(input_frame, text=instruction_text,
                                         font=("Arial", 10), justify=tk.CENTER)
            instruction_label.pack()
        
        # Virtual keyboard frame
        keyboard_frame = ttk.LabelFrame(main_frame, text="虚拟键盘 / Virtual Keyboard", padding=10)
        keyboard_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.create_virtual_keyboard(keyboard_frame)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="确定 / OK", command=self.on_ok).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消 / Cancel", command=self.on_cancel).pack(side=tk.RIGHT)
        
        # Focus management
        if self.mode == 0 and self.password_entry:
            self.password_entry.focus_set()
        else:
            # In blind mode, focus on the dialog itself
            self.dialog.focus_set()
    
    def create_virtual_keyboard(self, parent):
        """Create virtual keyboard"""
        # Number row
        num_frame = ttk.Frame(parent)
        num_frame.pack(fill=tk.X, pady=2)
        
        # First row: 1 2 3
        row1_frame = ttk.Frame(num_frame)
        row1_frame.pack(fill=tk.X, pady=2)
        for num in "123":
            btn = ttk.Button(row1_frame, text=num, width=4,
                   command=lambda n=num: self.add_char(n))
            btn.pack(side=tk.LEFT, padx=1)
        
        # Second row: 4 5 6
        row2_frame = ttk.Frame(num_frame)
        row2_frame.pack(fill=tk.X, pady=2)
        for num in "456":
            btn = ttk.Button(row2_frame, text=num, width=4,
                   command=lambda n=num: self.add_char(n))
            btn.pack(side=tk.LEFT, padx=1)
        
        # Third row: 7 8 9
        row3_frame = ttk.Frame(num_frame)
        row3_frame.pack(fill=tk.X, pady=2)
        for num in "789":
            btn = ttk.Button(row3_frame, text=num, width=4,
                   command=lambda n=num: self.add_char(n))
            btn.pack(side=tk.LEFT, padx=1)
        
        # Fourth row: 0 and OK button
        row4_frame = ttk.Frame(num_frame)
        row4_frame.pack(fill=tk.X, pady=2)
        btn = ttk.Button(row4_frame, text="0", width=4,
                   command=lambda: self.add_char("0"))
        btn.pack(side=tk.LEFT, padx=2)

    def add_char(self, char):
        """Add character to password"""
        current = self.password_var.get()
        self.password_var.set(current + char)
        # Only focus on password entry in normal mode
        if self.mode == 0 and self.password_entry:
            self.password_entry.focus_set()
    
    def backspace(self):
        """Remove last character"""
        current = self.password_var.get()
        if current:
            self.password_var.set(current[:-1])
        # Only focus on password entry in normal mode
        if self.mode == 0 and self.password_entry:
            self.password_entry.focus_set()
    
    def clear_password(self):
        """Clear password field"""
        self.password_var.set("")
        # Only focus on password entry in normal mode
        if self.mode == 0 and self.password_entry:
            self.password_entry.focus_set()
    
    def toggle_password(self):
        """Toggle password visibility (only works in normal mode)"""
        if self.mode == 0 and self.password_entry:
            if self.show_password.get():
                self.password_entry.config(show="")
            else:
                self.password_entry.config(show="*")
    
    def on_ok(self):
        """Handle OK button click"""
        password = self.password_var.get().strip()
        if not password:
            messagebox.showwarning("警告 / Warning", "请输入密码 / Please enter password")
            return
        
        # Here you can add password validation logic
        # For now, we'll accept any non-empty password
        # You can modify this to check against a specific password
        if self.validate_password(password):
            self.result = True
            self.password = password
            self.dialog.destroy()
        else:
            messagebox.showerror("错误 / Error", "密码错误 / Incorrect password")
            self.password_var.set("")
            self.password_entry.focus_set()
    
    def validate_password(self, password):
        """Validate the entered password"""
        # Default password validation - you can modify this
        # For demonstration, let's accept "admin" or "123456" as valid passwords
        # valid_passwords = ["admin", "123456", "password"]
        return (password[0] == "0" and password[-1] == "0")
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return result"""
        self.dialog.wait_window()
        return self.result

class BirthdayBackgroundEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Birthday Background Editor")
        self.root.geometry("1400x900")
        
        # Initialize data
        self.config = self.load_config()
        self.data = self.load_data()
        self.template_image = None
        self.preview_image = None
        self.current_item_index = -1
        
        # Setup UI
        self.setup_ui()
        self.refresh_preview()
        
    def load_config(self):
        """Load configuration from encrypted YAML file"""
        try:
            yaml_content = load_encrypted_text_file('config.yaml')
            if yaml_content:
                return yaml.safe_load(yaml_content)
            else:
                return {'render': []}
        except:
            return {'render': []}
    
    def save_config(self):
        """Save configuration to encrypted YAML file"""
        try:
            yaml_content = yaml.dump(self.config, default_flow_style=False, allow_unicode=True)
            success = save_encrypted_text_file('config.yaml', yaml_content)
            if not success:
                messagebox.showerror("Error", "Failed to save encrypted config file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def load_data(self):
        """Load data from encrypted CSV file"""
        try:
            csv_content = load_encrypted_text_file('data.csv')
            if csv_content:
                csv_file = StringIO(csv_content)
                reader = csv.DictReader(csv_file)
                data = []
                for row in reader:
                    clean_row = {}
                    for key, value in row.items():
                        clean_row[key.strip()] = value.strip()
                    data.append(clean_row)
                return data
            else:
                return []
        except:
            return []
    
    def get_system_fonts(self):
        """Get list of system fonts"""
        font_dir = "C:/Windows/Fonts/"
        fonts = []
        for ext in ['*.ttf', '*.otf', '*.ttc']:
            fonts.extend(glob.glob(os.path.join(font_dir, ext)))
        return sorted(fonts)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main frames
        left_frame = ttk.Frame(self.root, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left_frame.pack_propagate(False)
        
        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File upload section
        upload_frame = ttk.LabelFrame(left_frame, text="File Upload", padding=10)
        upload_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(upload_frame, text="Upload Template", 
                  command=self.upload_template).pack(fill=tk.X, pady=2)
        ttk.Button(upload_frame, text="Upload Default", 
                  command=self.upload_default).pack(fill=tk.X, pady=2)
        ttk.Button(upload_frame, text="Upload Data", 
                  command=self.upload_data).pack(fill=tk.X, pady=2)
        
        # Render items section
        render_frame = ttk.LabelFrame(left_frame, text="Render Items", padding=10)
        render_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Render items listbox
        self.render_listbox = tk.Listbox(render_frame, height=6)
        self.render_listbox.pack(fill=tk.X, pady=(0, 10))
        self.render_listbox.bind('<<ListboxSelect>>', self.on_render_select)
        
        # Render item buttons
        button_frame = ttk.Frame(render_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Add", command=self.add_render_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_render_item).pack(side=tk.LEFT, padx=2)
        
        # Edit section
        edit_frame = ttk.LabelFrame(left_frame, text="Edit Item", padding=10)
        edit_frame.pack(fill=tk.BOTH, expand=True)
        
        # Position controls
        ttk.Label(edit_frame, text="Position:").pack(anchor=tk.W, pady=(0, 5))
        pos_frame = ttk.Frame(edit_frame)
        pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pos_frame, text="X:").pack(side=tk.LEFT)
        self.x_var = tk.StringVar()
        self.x_var.trace('w', self.on_edit_change)
        x_entry = ttk.Entry(pos_frame, textvariable=self.x_var, width=8)
        x_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(pos_frame, text="Y:").pack(side=tk.LEFT)
        self.y_var = tk.StringVar()
        self.y_var.trace('w', self.on_edit_change)
        y_entry = ttk.Entry(pos_frame, textvariable=self.y_var, width=8)
        y_entry.pack(side=tk.LEFT, padx=5)
        
        # Info field
        ttk.Label(edit_frame, text="Info Field:").pack(anchor=tk.W, pady=(0, 5))
        self.info_var = tk.StringVar()
        self.info_var.trace('w', self.on_edit_change)
        self.info_combo = ttk.Combobox(edit_frame, textvariable=self.info_var)
        if self.data:
            self.info_combo['values'] = list(self.data[0].keys())
        self.info_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Font size
        ttk.Label(edit_frame, text="Font Size:").pack(anchor=tk.W, pady=(0, 5))
        self.size_var = tk.StringVar()
        self.size_var.trace('w', self.on_edit_change)
        size_entry = ttk.Entry(edit_frame, textvariable=self.size_var)
        size_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Font family
        ttk.Label(edit_frame, text="Font Family:").pack(anchor=tk.W, pady=(0, 5))
        self.font_var = tk.StringVar()
        self.font_var.trace('w', self.on_edit_change)
        self.font_combo = ttk.Combobox(edit_frame, textvariable=self.font_var)
        self.font_combo['values'] = self.get_system_fonts()
        self.font_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Font color
        ttk.Label(edit_frame, text="Font Color:").pack(anchor=tk.W, pady=(0, 5))
        color_frame = ttk.Frame(edit_frame)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.color_var = tk.StringVar()
        self.color_var.trace('w', self.on_edit_change)
        self.color_entry = ttk.Entry(color_frame, textvariable=self.color_var, width=10)
        self.color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(color_frame, text="Choose", command=self.choose_color).pack(side=tk.LEFT)
        
        # # Save button
        # ttk.Button(edit_frame, text="Save Changes", command=self.save_current_item).pack(fill=tk.X, pady=10)
        
        # Preview section
        preview_frame = ttk.LabelFrame(right_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for preview
        self.canvas = tk.Canvas(preview_frame, bg='white', width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Update render items list
        self.update_render_list()
        self.clear_edit_fields()
    
    def on_edit_change(self, *args):
        """Handle real-time edit changes"""
        if self.current_item_index >= 0:
            # Update preview in real-time
            self.root.after_idle(self.refresh_preview)
            self.save_current_item()
    
    def get_current_edit_values(self):
        """Get current values from edit fields"""
        try:
            return {
                'pos': {
                    'x': int(self.x_var.get() or 0),
                    'y': int(self.y_var.get() or 0)
                },
                'info': self.info_var.get() or 'name',
                'font': {
                    'size': int(self.size_var.get() or 50),
                    'family': self.font_var.get() or 'C:/Windows/Fonts/arial.ttf',
                    'color': self.color_var.get() or 'ffffff'
                }
            }
        except ValueError:
            return None
    
    def upload_template(self):
        """Upload template image"""
        file_path = filedialog.askopenfilename(
            title="Select Template Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            try:
                # Read the image file and encrypt it
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                success = save_encrypted_binary_file('bgs/template.png', image_data)
                if success:
                    messagebox.showinfo("Success", "Template uploaded and encrypted successfully!")
                    self.refresh_preview()
                else:
                    messagebox.showerror("Error", "Failed to encrypt and save template")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload template: {e}")
    
    def upload_default(self):
        """Upload default image"""
        file_path = filedialog.askopenfilename(
            title="Select Default Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            try:
                # Read the image file and encrypt it
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                success = save_encrypted_binary_file('bgs/default.png', image_data)
                if success:
                    messagebox.showinfo("Success", "Default image uploaded and encrypted successfully!")
                else:
                    messagebox.showerror("Error", "Failed to encrypt and save default image")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload default image: {e}")
    
    def upload_data(self):
        """Upload data file (CSV or XLSX)"""
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    # Convert XLSX to CSV string
                    df = pd.read_excel(file_path)
                    csv_content = df.to_csv(index=False)
                else:
                    # Read CSV file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        csv_content = f.read()
                
                # Encrypt and save CSV content
                success = save_encrypted_text_file('data.csv', csv_content)
                if success:
                    # Reload data
                    self.data = self.load_data()
                    if self.data:
                        self.info_combo['values'] = list(self.data[0].keys())
                    messagebox.showinfo("Success", "Data uploaded and encrypted successfully!")
                    self.refresh_preview()
                else:
                    messagebox.showerror("Error", "Failed to encrypt and save data file")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload data: {e}")
    
    def update_render_list(self):
        """Update the render items listbox"""
        self.render_listbox.delete(0, tk.END)
        for i, item in enumerate(self.config.get('render', [])):
            info = item.get('info', 'unknown')
            pos = item.get('pos', {})
            x, y = pos.get('x', 0), pos.get('y', 0)
            self.render_listbox.insert(tk.END, f"{i+1}. {info} at ({x}, {y})")
    
    def on_render_select(self, event):
        """Handle render item selection"""
        selection = self.render_listbox.curselection()
        if selection:
            self.current_item_index = selection[0]
            self.load_item_to_edit(self.current_item_index)
        # else:
            # self.current_item_index = -1
            # self.clear_edit_fields()
    
    def load_item_to_edit(self, index):
        """Load selected item into edit fields"""
        if 0 <= index < len(self.config.get('render', [])):
            item = self.config['render'][index]
            
            # Temporarily disable trace to avoid triggering refresh
            self.x_var.trace_vdelete('w', self.x_var.trace_info()[0][1])
            self.y_var.trace_vdelete('w', self.y_var.trace_info()[0][1])
            self.info_var.trace_vdelete('w', self.info_var.trace_info()[0][1])
            self.size_var.trace_vdelete('w', self.size_var.trace_info()[0][1])
            self.font_var.trace_vdelete('w', self.font_var.trace_info()[0][1])
            self.color_var.trace_vdelete('w', self.color_var.trace_info()[0][1])
            
            # Set values
            self.x_var.set(str(item['pos']['x']))
            self.y_var.set(str(item['pos']['y']))
            self.info_var.set(item['info'])
            self.size_var.set(str(item['font']['size']))
            self.font_var.set(item['font']['family'])
            self.color_var.set(item['font']['color'])
            
            # Re-enable trace
            self.x_var.trace('w', self.on_edit_change)
            self.y_var.trace('w', self.on_edit_change)
            self.info_var.trace('w', self.on_edit_change)
            self.size_var.trace('w', self.on_edit_change)
            self.font_var.trace('w', self.on_edit_change)
            self.color_var.trace('w', self.on_edit_change)
    
    def clear_edit_fields(self):
        """Clear all edit fields"""
        self.x_var.set("")
        self.y_var.set("")
        self.info_var.set("")
        self.size_var.set("")
        self.font_var.set("")
        self.color_var.set("")
    
    def add_render_item(self):
        """Add new render item"""
        new_item = {
            'pos': {'x': 100, 'y': 100},
            'info': 'name',
            'font': {
                'size': 50,
                'family': 'C:/Windows/Fonts/arial.ttf',
                'color': 'ffffff'
            }
        }
        
        if 'render' not in self.config:
            self.config['render'] = []
        
        self.config['render'].append(new_item)
        self.save_config()
        self.update_render_list()
        
        # Select the new item
        new_index = len(self.config['render']) - 1
        self.render_listbox.selection_set(new_index)
        self.current_item_index = new_index
        self.load_item_to_edit(new_index)
        self.refresh_preview()
    
    def delete_render_item(self):
        """Delete selected render item"""
        selection = self.render_listbox.curselection()
        if selection:
            index = selection[0]
            del self.config['render'][index]
            self.save_config()
            self.update_render_list()
            self.current_item_index = -1
            self.clear_edit_fields()
            self.refresh_preview()
    
    def save_current_item(self):
        """Save current item changes"""
        if self.current_item_index >= 0:
            new_values = self.get_current_edit_values()
            if new_values:
                self.config['render'][self.current_item_index] = new_values
                self.save_config()
                self.update_render_list()
                # Reselect the item
                self.render_listbox.selection_set(self.current_item_index)
                self.refresh_preview()
                # messagebox.showinfo("Success", "Item saved successfully!")
    
    def choose_color(self):
        """Choose color using color picker"""
        color = colorchooser.askcolor(title="Choose color")
        if color[1]:
            self.color_var.set(color[1].lstrip('#'))
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def refresh_preview(self):
        """Refresh the preview canvas"""
        try:
            # Load encrypted template image
            template_data = load_encrypted_binary_file("bgs/template.png")
            if template_data is None:
                self.canvas.delete("all")
                self.canvas.create_text(400, 300, text="No template image found",
                                      font=("Arial", 16), fill="red")
                return
            
            # Open and resize image for preview
            image = Image.open(BytesIO(template_data))
            
            # Calculate scaling to fit canvas
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            
            img_width, img_height = image.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y, 1.0)  # Don't scale up
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(image)
            
            # Render text from config and current edit
            if self.data:
                person = self.data[0]  # Use first person for preview
                
                render_items = self.config.get('render', []).copy()
                
                # If editing an item, use current edit values for preview
                if self.current_item_index >= 0:
                    current_values = self.get_current_edit_values()
                    if current_values:
                        render_items[self.current_item_index] = current_values
                
                for i, render_item in enumerate(render_items):
                    pos = render_item.get('pos', {})
                    x = int(pos.get('x', 0) * scale)
                    y = int(pos.get('y', 0) * scale)
                    
                    info_field = render_item.get('info', '')
                    text = person.get(info_field, f'[{info_field}]')
                    
                    font_config = render_item.get('font', {})
                    font_size = int(font_config.get('size', 50) * scale)
                    font_family = font_config.get('family', 'arial.ttf')
                    font_color = font_config.get('color', 'ffffff')
                    
                    # Load font
                    try:
                        font = ImageFont.truetype(font_family, font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    # Convert color
                    try:
                        color = self.hex_to_rgb(font_color)
                    except:
                        color = (255, 255, 255)
                    
                    # Highlight current item being edited
                    if i == self.current_item_index:
                        # Draw a border around current item
                        bbox = draw.textbbox((x, y), text, font=font)
                        draw.rectangle(bbox, outline=(255, 0, 0), width=2)
                    
                    # Draw text
                    draw.text((x, y), text, font=font, fill=color)
            
            # Convert to PhotoImage and display
            self.preview_image = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            
            # Center the image
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            
            self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_image)
            
        except Exception as e:
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text=f"Preview error: {str(e)}", 
                                  font=("Arial", 12), fill="red")

def main():
    # Show password dialog first - use mode=1 for blind input mode
    password_dialog = PasswordDialog(mode=1)  # Change to mode=0 for normal mode
    if not password_dialog.show():
        # User cancelled or closed the dialog
        return
    
    # If password is correct, proceed to main application
    root = tk.Tk()
    app = BirthdayBackgroundEditor(root)
    
    # Bind canvas resize to refresh preview
    def on_canvas_configure(event):
        app.refresh_preview()
    
    app.canvas.bind('<Configure>', on_canvas_configure)
    
    root.mainloop()

if __name__ == "__main__":
    main()