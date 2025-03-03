
import os
import yaml

def download_file(path, type, output_dir):
    if type == "git":
        os.system(f"git clone {path} --depth 1 {output_dir}")
    else:
        os.system(f"wget {path} -O {output_dir}")

def process_manifest(manifest, type):
    os.makedirs("./build", exist_ok=True)
    output_dir = os.path.join("./build", type+"s", manifest['name'])
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, 'index.json'), 'w') as file:
        file.write('{\n')
        file.write(f'  "name": "{manifest["name"]}",\n')
        file.write(f'  "description": "{manifest["description"]}",\n')
        file.write(f'  "short_description": "{manifest["short_description"]}",\n')
        file.write(f'  "changelog": "{manifest["changelog"]}",\n')
        file.write(f'  "author": "{manifest["author"]}",\n')
        file.write(f'  "icon": "{manifest["icon"]}",\n')
        file.write(f'  "sources": "{manifest["sources"]}",\n')
        if type == "app":
            file.write(f'  "executionfile": "{manifest["executionfile"]}"\n')
        elif type == "mod":
            file.write(f'  "modfiles": "{manifest["modfiles"]}"\n')
        else: 
            pass
        file.write('}\n')

    download_file(manifest['sources']['location']['origin'], manifest['sources']['type'], output_dir)

    if type == "app":
        download_file(manifest['executionfile']['location'], manifest['executionfile']['type'], output_dir)
    elif type == "mod":
        for file in manifest['modfiles']:
            print(file)
            download_file(file['location'], file['type'], output_dir)
    else:
        pass





def check_folder_sturcture(folder):
    return os.path.isfile(os.path.join(folder, 'manifest.yml'))

def check_manifest(src, type):
    manifest_path = os.path.join(type+"s", src, 'manifest.yml')
    print(manifest_path)
    with open(manifest_path, 'r') as file:
        manifest = yaml.safe_load(file)
        if 'name' in manifest:
            print(f"Name: {manifest['name']}")
        else:
            raise ValueError(f"Name not found in manifest file: {manifest_path}")
        if type == "app":
            if 'keira_version' in manifest:
                print(f"keira_version: {manifest['keira_version']}")
            else:
                raise ValueError(f"keira_version not found in manifest file: {manifest_path}")

        if 'description' in manifest:
            if manifest['description'][0] == '@':
                manifest['description'] = open(os.path.join(type+"s", src, manifest['description'][1:]), 'r').read()
            else:
                pass
            print(f"Description: {manifest['description']}")
        else:
            raise ValueError(f"Description not found in manifest file: {manifest_path}")
        
        if 'short_description' in manifest:
            if manifest['short_description'][0] == '@':
                manifest['short_description'] = open(os.path.join(type+"s", src, manifest['short_description'][1:]), 'r').read()
            else:
                pass
            print(f"Short Description: {manifest['short_description']}")
        else:
            raise ValueError(f"Short Description not found in manifest file: {manifest_path}")
        
        if 'changelog' in manifest:
            if(manifest['changelog'][0] == '@'):
                manifest['changelog'] = open(os.path.join(type+"s", src, manifest['changelog'][1:]), 'r').read()
            else:
                pass
            print(f"Changelog: {manifest['changelog']}")
        else:
            raise ValueError(f"Changelog not found in manifest file: {manifest_path}")

        if 'author' in manifest:
            print(f"Author: {manifest['author']}")
        else:
            raise ValueError(f"Author not found in manifest file: {manifest_path}")
        
        if 'icon' in manifest:
            print(f"Icon: {manifest['icon']}")
        else:
            raise ValueError(f"Icon not found in manifest file: {manifest_path}")
        
        if 'sources' in manifest:
            print(f"sources: {manifest['sources']}")
            if 'type' in manifest['sources']:
                print(f"sources type: {manifest['sources']['type']}")
            else:
                raise ValueError(f"sources type not found in manifest file: {manifest_path}")
            if 'location' in manifest['sources']:
                print(f"sources location: {manifest['sources']['location']}")
                if 'origin' in manifest['sources']['location']:
                    print(f"sources origin: {manifest['sources']['location']['origin']}")
                else:
                    raise ValueError(f"sources origin not found in manifest file: {manifest_path}")
            else:
                raise ValueError(f"sources location not found in manifest file: {manifest_path}")
        else:
            raise ValueError(f"sources not found in manifest file: {manifest_path}")
        
        if type == "app":
            if 'executionfile' in manifest:
                print(f"executionfile: {manifest['executionfile']}")
            else:
                raise ValueError(f"executionfile not found in manifest file: {manifest_path}")
        elif type == "mod":
            if 'modfiles' in manifest:
                print(f"Modfile: {manifest['modfiles']}")
            else:
                raise ValueError(f"modfiles not found in manifest file: {manifest}")
        else:
            raise ValueError(f"Type not found in manifest file: {manifest_path}")
        
        return manifest
        

def scan_apps_folder():
    return [d for d in os.listdir('./apps') if os.path.isdir(os.path.join('./apps', d))]

def scan_mods_folder():
    return [d for d in os.listdir('./mods') if os.path.isdir(os.path.join('./mods', d))]

def process_apps_folder(apps):
    for app in apps:
        if(check_folder_sturcture(os.path.join('./apps', app))):
            app = check_manifest(app, 'app')
            process_manifest(app, 'app')
        else:
            raise ValueError(f"Incorrect folder structure for app: {app}")
        
def process_mods_folder(mods):
    for mod in mods:
        if(check_folder_sturcture(os.path.join('./mods', mod))):
            mod = check_manifest(mod, 'mod')
            process_manifest(mod, 'mod')
        else:
            raise ValueError(f"Incorrect folder structure for app: {mod}")
        
def main():
    apps = scan_apps_folder()
    mods = scan_mods_folder()

    print(apps)
    print(mods)

    process_apps_folder(apps)
    process_mods_folder(mods)

if __name__ == '__main__': 
    main()
