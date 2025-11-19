
import os
import yaml
import requests
import argparse
import html
import json
from PIL import Image

args = argparse.ArgumentParser(description="Builds the keira app and mod files")
args.add_argument("--build", help="Build json files for mods and apps", action='store_true', default=False)
args.add_argument("--shortjson", help="Build short json files for mods and apps", action='store_true', default=False)
args = args.parse_args()

# Global warnings tracker
build_warnings = []

def add_warning(name, warning_type, message, item_type=None):
    """Add a warning to the global warnings list"""
    warning = {
        "name": name,
        "type": warning_type,
        "message": message
    }
    if item_type:
        warning["item_type"] = item_type
    build_warnings.append(warning)
    print(f"WARNING [{name}]: {message}")

# Maximum dimensions for images (width, height)
MAX_IMAGE_WIDTH = 1920
MAX_IMAGE_HEIGHT = 1080
MAX_ICON_SIZE = 512
MIN_ICON_SIZE = 64  # For ESP32-S3 display
JPEG_QUALITY = 85

def generate_min_icon(icon_path, output_path):
    """Generate 64x64 minimized icon for ESP32-S3 in RGB565 binary format"""
    try:
        with Image.open(icon_path) as img:
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 64x64
            img_resized = img.resize((MIN_ICON_SIZE, MIN_ICON_SIZE), Image.Resampling.LANCZOS)
            
            # Convert to RGB565 binary format
            pixels = img_resized.load()
            rgb565_data = bytearray()
            
            for y in range(MIN_ICON_SIZE):
                for x in range(MIN_ICON_SIZE):
                    r, g, b = pixels[x, y]
                    # Convert RGB888 to RGB565
                    r5 = (r >> 3) & 0x1F
                    g6 = (g >> 2) & 0x3F
                    b5 = (b >> 3) & 0x1F
                    rgb565 = (r5 << 11) | (g6 << 5) | b5
                    # Write as little-endian 16-bit value
                    rgb565_data.append(rgb565 & 0xFF)
                    rgb565_data.append((rgb565 >> 8) & 0xFF)
            
            # Save binary file
            with open(output_path, 'wb') as f:
                f.write(rgb565_data)
            
            print(f"  Generated min icon: {output_path} (64x64 RGB565, {len(rgb565_data)} bytes)")
    except Exception as e:
        print(f"  Warning: Could not generate min icon: {e}")

def compress_image(image_path, max_width=MAX_IMAGE_WIDTH, max_height=MAX_IMAGE_HEIGHT, quality=JPEG_QUALITY):
    """Compress and resize image if it's too large"""
    try:
        with Image.open(image_path) as img:
            # Get original size
            original_size = os.path.getsize(image_path)
            width, height = img.size
            
            # Check if image needs resizing
            if width > max_width or height > max_height:
                print(f"  Resizing image from {width}x{height} to fit {max_width}x{max_height}")
                # Calculate new dimensions maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save compressed image
                if image_path.lower().endswith('.png'):
                    img.save(image_path, 'PNG', optimize=True)
                else:
                    # Convert to RGB if needed (for JPEG)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    img.save(image_path, 'JPEG', quality=quality, optimize=True)
                
                new_size = os.path.getsize(image_path)
                print(f"  Compressed: {original_size} bytes -> {new_size} bytes ({100 - int(new_size/original_size*100)}% reduction)")
            elif original_size > 500 * 1024:  # If larger than 500KB, optimize anyway
                print(f"  Optimizing large image ({original_size} bytes)")
                if image_path.lower().endswith('.png'):
                    img.save(image_path, 'PNG', optimize=True)
                else:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    img.save(image_path, 'JPEG', quality=quality, optimize=True)
                
                new_size = os.path.getsize(image_path)
                print(f"  Compressed: {original_size} bytes -> {new_size} bytes ({100 - int(new_size/original_size*100)}% reduction)")
    except Exception as e:
        print(f"  Warning: Could not compress image {image_path}: {e}")

def download_file(path, output_dir) -> str:
    url = path['origin'] if isinstance(path, dict) else path
    response = requests.head(url)

    filename = url.split('/')[-1]
    output_path = os.path.join(output_dir, filename)

    if response.status_code == 404:
        raise FileNotFoundError(f"File not found: {url}")
    if(args.build):
        print(f"Downloading {url} to {output_path}")
        os.system(f"wget '{url}' -O '{output_path}'")

    return filename

def gen_static_folder(manifest, type, output_dir) -> dict:
    static_files_path = output_dir+"/static"

    os.makedirs(static_files_path, exist_ok=True)

    if type == "app" and manifest.get('executionfile'):
        manifest['executionfile']['location'] = download_file(manifest['executionfile']['location'], static_files_path)
    elif type == "mod":
        for file in manifest['modfiles']:
            file['location'] = download_file(file['location'], static_files_path)
    else:
        pass

    path_to_modapp = type+"s/"+manifest['path']

    # Copy and compress screenshots
    for screenshot in manifest['screenshots']:
        try:
            if screenshot.startswith('https://') or screenshot.startswith('http://'):
                download_file(screenshot, static_files_path)
            else:
                source_path = os.path.join(path_to_modapp, screenshot)
                dest_path = os.path.join(static_files_path, screenshot)
                if os.path.exists(source_path):
                    os.system(f"cp '{source_path}' '{dest_path}'")
                    # Compress the screenshot
                    if os.path.exists(dest_path):
                        compress_image(dest_path, MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT)
                else:
                    print(f"WARNING: Screenshot not found, skipping: {screenshot}")
        except Exception as e:
            print(f"WARNING: Failed to process screenshot {screenshot}: {str(e)}")
    
    # Copy and compress icon
    if manifest.get('icon'):
        try:
            if manifest['icon'].startswith('https://') or manifest['icon'].startswith('http://'):
                download_file(manifest['icon'], static_files_path)
                icon_dest_path = os.path.join(static_files_path, manifest['icon'].split('/')[-1])
            else:
                source_path = os.path.join(path_to_modapp, manifest['icon'])
                dest_path = os.path.join(static_files_path, manifest['icon'])
                if os.path.exists(source_path):
                    os.system(f"cp '{source_path}' '{dest_path}'")
                    icon_dest_path = dest_path
                    # Compress the icon (smaller size for icons)
                    if os.path.exists(dest_path):
                        compress_image(dest_path, MAX_ICON_SIZE, MAX_ICON_SIZE)
                else:
                    print(f"WARNING: Icon not found, skipping: {manifest['icon']}")
                    icon_dest_path = None
            
            # Generate minimized 64x64 icon for ESP32-S3 in RGB565 format
            if icon_dest_path and os.path.exists(icon_dest_path):
                icon_name = os.path.splitext(manifest['icon'])[0]
                min_icon_name = f"{icon_name}_min.bin"
                min_icon_path = os.path.join(static_files_path, min_icon_name)
                generate_min_icon(icon_dest_path, min_icon_path)
                manifest['icon_min'] = min_icon_name
        except Exception as e:
            print(f"WARNING: Failed to process icon: {str(e)}")

    return manifest

def process_manifest(manifest, type) -> None:
    output_dir = os.path.join("./build", type+"s", manifest['path'])

    if args.build:
        os.makedirs("./build", exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        manifest = gen_static_folder(manifest, type, output_dir)

        if type == "app":
            short_data = {
                "name": manifest["name"],
                "short_description": manifest["short_description"]
            }
            # Only include executionfile if it exists
            if manifest.get("executionfile"):
                short_data["executionfile"] = manifest["executionfile"]
            
            with open(os.path.join(output_dir, 'index_short.json'), 'w', encoding='utf-8') as file:
                json.dump(short_data, file, indent=2, ensure_ascii=False)
            
        full_data = {
            "name": manifest["name"],
            "description": manifest["description"],
            "short_description": manifest["short_description"],
            "author": manifest["author"],
            "sources": manifest["sources"],
            "screenshots": manifest.get("screenshots", [])
        }
        
        # Only include icon if it exists
        if manifest.get("icon"):
            full_data["icon"] = manifest["icon"]
        
        # Include minimized icon for ESP32-S3 if it exists
        if manifest.get("icon_min"):
            full_data["icon_min"] = manifest["icon_min"]
        
        # Only include changelog if it exists and is not empty
        if manifest.get("changelog"):
            full_data["changelog"] = manifest["changelog"]
        
        if type == "app":
            # Only include executionfile if it exists
            if manifest.get("executionfile"):
                full_data["executionfile"] = manifest["executionfile"]
        elif type == "mod":
            full_data["modfiles"] = manifest["modfiles"]
        
        with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as file:
            json.dump(full_data, file, indent=2, ensure_ascii=False)


def gen_json_index_manifests(manifests, type) -> None:
    jsons_per_page = 12
    page = 1
    jsons = []
    pages = len(manifests) // jsons_per_page
    if len(manifests) % jsons_per_page != 0:
        pages += 1
    output_dir = os.path.join("./build", type+"s")
    os.makedirs(output_dir, exist_ok=True)
    for i in range(0, pages):
        with open(os.path.join("./build", type+"s", f"index_{i}.json"), 'w') as file:
            file.write('{\n')
            file.write(f'  "page": {i},\n')
            file.write(f'  "total_pages": {pages},\n')
            file.write(f'  "manifests": [\n')
            page_manifests = []
            for j in range(0, jsons_per_page):
                if i*jsons_per_page+j >= len(manifests):
                    break
                page_manifests.append(f'    "{manifests[i*jsons_per_page+j]}"')
            file.write(',\n'.join(page_manifests) + '\n')
            file.write('  ]\n')
            file.write('}\n')
        

def check_folder_sturcture(folder) -> bool:
    return os.path.isfile(os.path.join(folder, 'manifest.yml'))

def validate_app_files(src, manifest, type) -> bool:
    """Validate that all required files exist. Returns True if valid, False otherwise.
    Only returns False for critical errors that should skip the app/mod."""
    path_to_app = os.path.join(type + "s", src)
    is_valid = True
    
    print(f"Validating {src}...")
    
    if manifest.get('icon'):
        icon_path = os.path.join(path_to_app, manifest['icon'])
        if not os.path.exists(icon_path) and not (manifest['icon'].startswith('http://') or manifest['icon'].startswith('https://')):
            add_warning(src, "missing_icon", f"Icon file not found: {manifest['icon']}", type)
    
    if manifest.get('screenshots'):
        for screenshot in manifest['screenshots']:
            if not (screenshot.startswith('http://') or screenshot.startswith('https://')):
                screenshot_path = os.path.join(path_to_app, screenshot)
                if not os.path.exists(screenshot_path):
                    add_warning(src, "missing_screenshot", f"Screenshot file not found: {screenshot}", type)
    
    if manifest.get('sources'):
        sources = manifest['sources']
        if isinstance(sources, dict) and sources.get('location', {}).get('origin'):
            repo_url = sources['location']['origin']
            if 'github.com' in repo_url:
                try:
                    response = requests.head(repo_url, timeout=5)
                    if response.status_code == 404:
                        add_warning(src, "repo_not_found", f"Repository not found: {repo_url}", type)
                        is_valid = False
                except Exception as e:
                    add_warning(src, "repo_check_failed", f"Could not verify repository: {str(e)}", type)
    
    if type == "app" and manifest.get('executionfile'):
        exec_file = manifest['executionfile']
        if isinstance(exec_file, dict) and exec_file.get('location'):
            location = exec_file['location']
            if isinstance(location, dict) and location.get('origin'):
                exec_url = location['origin']
                try:
                    response = requests.head(exec_url, timeout=5)
                    if response.status_code == 404:
                        add_warning(src, "exec_file_not_found", f"Execution file not found: {exec_url}", type)
                        # Don't mark as invalid - just warn
                except Exception as e:
                    add_warning(src, "exec_file_check_failed", f"Could not verify execution file: {str(e)}", type)
    
    return is_valid

def check_manifest(src, type) -> dict:
    manifest_path = os.path.join(type+"s", src, 'manifest.yml')
    print(manifest_path)
    
    try:
        with open(manifest_path, 'r') as file:
            manifest = yaml.safe_load(file)
    except Exception as e:
        add_warning(src, "manifest_error", f"Failed to read manifest.yml: {str(e)}", type)
        return None
    
    if 'name' in manifest:
        print(f"Name: {manifest['name']}")
    else:
        add_warning(src, "missing_field", "Name not found in manifest file", type)
        return None
    
    if type == "app":
        if 'keira_version' in manifest:
            print(f"keira_version: {manifest['keira_version']}")
        else:
            add_warning(src, "missing_field", "keira_version not found in manifest file", type)
            return None

    if 'description' in manifest:
        if manifest['description'][0] == '@':
            try:
                manifest['description'] = open(os.path.join(type+"s", src, manifest['description'][1:]), 'r').read()
            except Exception as e:
                add_warning(src, "file_read_error", f"Failed to read description file: {str(e)}", type)
                manifest['description'] = ""
        else:
            pass
        print(f"Description: {manifest['description']}")
    else:
        manifest['description'] = ""
        print("Description: (not provided)")
    
    if 'short_description' in manifest:
        if manifest['short_description'][0] == '@':
            try:
                manifest['short_description'] = open(os.path.join(type+"s", src, manifest['short_description'][1:]), 'r').read()
            except Exception as e:
                add_warning(src, "file_read_error", f"Failed to read short_description file: {str(e)}", type)
                return None
        else:
            pass
        print(f"Short Description: {manifest['short_description']}")
    else:
        add_warning(src, "missing_field", "Short Description not found in manifest file", type)
        return None
    
    if 'changelog' in manifest:
        if(manifest['changelog'][0] == '@'):
            try:
                manifest['changelog'] = open(os.path.join(type+"s", src, manifest['changelog'][1:]), 'r').read()
            except Exception as e:
                add_warning(src, "file_read_error", f"Failed to read changelog file: {str(e)}", type)
                manifest['changelog'] = ""
        else:
            pass
        print(f"Changelog: {manifest['changelog']}")
    else:
        manifest['changelog'] = ""
        print("Changelog: (not provided)")

    if 'author' in manifest:
        print(f"Author: {manifest['author']}")
    else:
        add_warning(src, "missing_field", "Author not found in manifest file", type)
        return None
    
    if 'icon' in manifest:
        print(f"Icon: {manifest['icon']}")
    else:
        add_warning(src, "missing_field", "Icon not found in manifest file (optional)", type)
        # Don't return None - icon is now optional
    
    if 'sources' in manifest:
        print(f"sources: {manifest['sources']}")
        if 'type' in manifest['sources']:
            print(f"sources type: {manifest['sources']['type']}")
        else:
            add_warning(src, "missing_field", "sources type not found in manifest file", type)
            return None
        if 'location' in manifest['sources']:
            print(f"sources location: {manifest['sources']['location']}")
            if 'origin' in manifest['sources']['location']:
                print(f"sources origin: {manifest['sources']['location']['origin']}")
            else:
                add_warning(src, "missing_field", "sources origin not found in manifest file", type)
                return None
        else:
            add_warning(src, "missing_field", "sources location not found in manifest file", type)
            return None
    else:
        add_warning(src, "missing_field", "sources not found in manifest file", type)
        return None
    
    if type == "app":
        if 'executionfile' in manifest:
            print(f"executionfile: {manifest['executionfile']}")
        else:
            add_warning(src, "missing_field", "executionfile not found in manifest file (optional)", type)
            # Don't return None - executionfile is now optional
    elif type == "mod":
        if 'modfiles' in manifest:
            print(f"Modfile: {manifest['modfiles']}")
        else:
            add_warning(src, "missing_field", "modfiles not found in manifest file", type)
            return None
    else:
        add_warning(src, "unknown_type", f"Unknown type: {type}", type)
        return None
    
    # Validate all files exist
    if not validate_app_files(src, manifest, type):
        return None
    
    manifest['path'] = src.split('/')[-1]

    return manifest
        

def scan_apps_folder() -> list[str]:
    folders_list = [d for d in os.listdir('./apps') if os.path.isdir(os.path.join('./apps', d))]
    folders_list = sorted(folders_list)
    return folders_list

def scan_mods_folder() -> list[str]:
    folder_list = [d for d in os.listdir('./mods') if os.path.isdir(os.path.join('./mods', d))]
    folder_list = sorted(folder_list)
    return folder_list

def process_apps_folder(apps):
    for app in apps:
        if(check_folder_sturcture(os.path.join('./apps', app))):
            manifest = check_manifest(app, 'app')
            if manifest is not None:
                process_manifest(manifest, 'app')
            else:
                print(f"Skipping app: {app} (validation failed)")
        else:
            add_warning(app, "missing_manifest", "manifest.yml file not found", "app")
            print(f"Skipping app: {app} (manifest.yml not found)")
        
def process_mods_folder(mods):
    for mod in mods:
        if(check_folder_sturcture(os.path.join('./mods', mod))):
            manifest = check_manifest(mod, 'mod')
            if manifest is not None:
                process_manifest(manifest, 'mod')
            else:
                print(f"Skipping mod: {mod} (validation failed)")
        else:
            add_warning(mod, "missing_manifest", "manifest.yml file not found", "mod")
            print(f"Skipping mod: {mod} (manifest.yml not found)")
        
def main():
    apps: list[str] = scan_apps_folder()
    mods: list[str] = scan_mods_folder()

    print(apps)
    print(mods)

    process_apps_folder(apps)
    process_mods_folder(mods)


    if args.build:
        gen_json_index_manifests(apps, "app")
        gen_json_index_manifests(mods, "mod")
    
    # Write warnings to JSON file
    from datetime import datetime
    warnings_data = {
        "build_date": datetime.now().isoformat(),
        "total_warnings": len(build_warnings),
        "warnings": build_warnings
    }
    
    os.makedirs("./build", exist_ok=True)
    with open("./build/warnings.json", 'w') as f:
        json.dump(warnings_data, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Build completed with {len(build_warnings)} warnings")
    print(f"Warnings saved to: build/warnings.json")
    print(f"{'='*50}")

if __name__ == '__main__': 
    main()
