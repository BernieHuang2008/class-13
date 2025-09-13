import csv
import yaml
import os
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import ctypes
from ctypes import wintypes
from crypto_utils import load_encrypted_text_file, load_encrypted_binary_file
from io import StringIO, BytesIO

def read_csv_data(csv_path):
    """Read birthday data from encrypted CSV file"""
    people = []
    print(csv_path)
    try:
        # Load encrypted CSV content
        csv_content = load_encrypted_text_file(csv_path)
        if csv_content is None:
            print(f"Error: Could not load encrypted CSV file: {csv_path}")
            return []
        
        # Parse CSV from string
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        for row in reader:
            # Clean up the data
            person = {}
            for key, value in row.items():
                person[key.strip()] = value.strip()
            people.append(person)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
    return people

def read_config(config_path):
    """Read configuration from encrypted YAML file"""
    try:
        # Load encrypted YAML content
        yaml_content = load_encrypted_text_file(config_path)
        if yaml_content is None:
            print(f"Error: Could not load encrypted config file: {config_path}")
            return None
        
        # Parse YAML from string
        config = yaml.safe_load(yaml_content)
        return config
    except Exception as e:
        print(f"Error reading config: {e}")
        return None

def check_birthday_today(people):
    """Check if anyone has a birthday today"""
    today = datetime.now()
    today_str = f"{today.month}.{today.day}"
    
    birthday_people = []
    for person in people:
        if person.get('birthday') == today_str:
            birthday_people.append(person)
    
    return birthday_people

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def render_birthday_image(template_path, config, person, output_path):
    """Render birthday image with person's information"""
    try:
        # Load encrypted template image
        template_data = load_encrypted_binary_file(template_path)
        if template_data is None:
            print(f"Error: Could not load encrypted template: {template_path}")
            return False
        
        # Open image from bytes
        image = Image.open(BytesIO(template_data))
        draw = ImageDraw.Draw(image)
        
        # Process each render item from config
        for render_item in config.get('render', []):
            pos = render_item.get('pos', {})
            x = pos.get('x', 0)
            y = pos.get('y', 0)
            
            info_field = render_item.get('info', '')
            text = person.get(info_field, '')
            
            font_config = render_item.get('font', {})
            font_size = font_config.get('size', 50)
            font_family = font_config.get('family', 'arial.ttf')
            font_color = font_config.get('color', 'ffffff')
            
            # Load font
            try:
                font = ImageFont.truetype(font_family, font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Convert color
            color = hex_to_rgb(font_color)
            
            # Draw text
            draw.text((x, y), text, font=font, fill=color)
        
        # Save rendered image
        image.save(output_path)
        return True
        
    except Exception as e:
        print(f"Error rendering image: {e}")
        return False

def set_wallpaper(image_path):
    """Set desktop wallpaper using Windows API"""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(image_path)
        
        # Define constants
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        
        # Set wallpaper
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            abs_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        return result != 0
        
    except Exception as e:
        print(f"Error setting wallpaper: {e}")
        return False

def main():
    """Main program execution"""
    # Define paths (using original names for crypto_utils)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = 'data.csv'  # crypto_utils will handle the encrypted path
    config_path = 'config.yaml'  # crypto_utils will handle the encrypted path
    template_path = 'bgs/template.png'  # crypto_utils will handle the encrypted path
    default_path = 'bgs/default.png'  # crypto_utils will handle the encrypted path
    rendered_path = os.path.join(base_dir, 'bgs', 'birthday_rendered.png')
    
    # Read data and config
    people = read_csv_data(csv_path)
    config = read_config(config_path)
    
    if not people or not config:
        print("Failed to load data or config")
        sys.exit(1)
    
    # Check for birthdays today
    birthday_people = check_birthday_today(people)
    
    wallpaper_path = default_path
    
    if birthday_people:
        # Someone has a birthday today - render template
        person = birthday_people[0]  # Use first person if multiple birthdays
        
        if render_birthday_image(template_path, config, person, rendered_path):
            wallpaper_path = rendered_path
        else:
            # Fallback to default if rendering fails
            wallpaper_path = default_path
    
    # Handle wallpaper setting
    if wallpaper_path == default_path:
        # For default image, check if encrypted version exists
        default_data = load_encrypted_binary_file(default_path)
        if default_data:
            # Save decrypted default image temporarily
            temp_default_path = os.path.join(base_dir, 'bgs', 'temp_default.png')
            with open(temp_default_path, 'wb') as f:
                f.write(default_data)
            wallpaper_path = temp_default_path
    
    # Set wallpaper
    if os.path.exists(wallpaper_path):
        success = set_wallpaper(wallpaper_path)
        if success:
            print(f"Wallpaper set successfully: {wallpaper_path}")
        else:
            print("Failed to set wallpaper")
        
        # Clean up temporary file if created
        if wallpaper_path.endswith('temp_default.png'):
            try:
                os.remove(wallpaper_path)
            except:
                pass
    else:
        print(f"Wallpaper file not found: {wallpaper_path}")
    
    # Exit immediately
    sys.exit(0)

if __name__ == "__main__":
    if os.path.exists("D:/099/1009.txt"):
        main()
# The above line is a placeholder to prevent automatic execution in certain environments.