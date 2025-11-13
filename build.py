
import os
import yaml
import requests
import argparse
import html
import json

args = argparse.ArgumentParser(description="Builds the keira app and mod files")
args.add_argument("--build", help="Build json files for mods and apps", action='store_true', default=False)
args.add_argument("--shortjson", help="Build short json files for mods and apps", action='store_true', default=False)
args = args.parse_args()

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

    if type == "app":
        manifest['executionfile']['location'] = download_file(manifest['executionfile']['location'], static_files_path)
    elif type == "mod":
        for file in manifest['modfiles']:
            file['location'] = download_file(file['location'], static_files_path)
    else:
        pass

    path_to_modapp = type+"s/"+manifest['path']

    for screenshot in manifest['screenshots']:
        if screenshot.startswith('https://') or screenshot.startswith('http://'):
            download_file(screenshot, static_files_path)
        else:
            os.system(f"cp {os.path.join(path_to_modapp, screenshot)} {static_files_path}")
    if manifest['icon'].startswith('https://') or manifest['icon'].startswith('http://'):
        download_file(manifest['icon'], static_files_path)
    else:
        os.system(f"cp {os.path.join(path_to_modapp, manifest['icon'])} {static_files_path}")

    return manifest

def process_manifest(manifest, type) -> None:
    output_dir = os.path.join("./build", type+"s", manifest['path'])

    if args.build:
        os.makedirs("./build", exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        def escape_for_json(value):
            return json.dumps(value).strip('"')
        
        manifest = gen_static_folder(manifest, type, output_dir)

        if type == "app":
            with open(os.path.join(output_dir, 'index_short.json'), 'w') as file:
                file.write('{\n')
                file.write(f'  "name": "{escape_for_json(manifest["name"])}",\n')
                file.write(f'  "short_description": "{escape_for_json(manifest["short_description"])}",\n')
                file.write(f'  "executionfile": "{escape_for_json(str(manifest["executionfile"]))}"\n')
                file.write('}\n')
            
        with open(os.path.join(output_dir, 'index.json'), 'w') as file:
            file.write('{\n')
            file.write(f'  "name": "{escape_for_json(manifest["name"])}",\n')
            file.write(f'  "description": "{escape_for_json(manifest["description"])}",\n')
            file.write(f'  "short_description": "{escape_for_json(manifest["short_description"])}",\n')
            file.write(f'  "changelog": "{escape_for_json(manifest["changelog"])}",\n')
            file.write(f'  "author": "{escape_for_json(manifest["author"])}",\n')
            file.write(f'  "icon": "{escape_for_json(manifest["icon"])}",\n')
            file.write(f'  "sources": "{escape_for_json(str(manifest["sources"]))}",\n')
            if type == "app":
                file.write(f'  "executionfile": "{escape_for_json(str(manifest["executionfile"]))}"\n')
            elif type == "mod":
                file.write(f'  "modfiles": "{escape_for_json(str(manifest["modfiles"]))}"\n')
            else: 
                pass
            file.write('}\n')


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

def check_manifest(src, type) -> dict:
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
    apps: list[str] = scan_apps_folder()
    mods: list[str] = scan_mods_folder()

    print(apps)
    print(mods)

    process_apps_folder(apps)
    process_mods_folder(mods)


    if args.build:
        gen_json_index_manifests(apps, "app")
        gen_json_index_manifests(mods, "mod")

if __name__ == '__main__': 
    main()
