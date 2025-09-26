# ...existing code...
import os
import stat
import shutil
import tarfile
from typing import Dict, Iterable, List, Optional, Tuple


def build_mapping(unitypackage_path: str, working_dir: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for entry in os.listdir(working_dir):
        asset_root = os.path.join(working_dir, entry)
        if not os.path.isdir(asset_root):
            continue
        real_path = ""
        has_asset = False
        for child in os.listdir(asset_root):
            if child == "pathname":
                pathname_file = os.path.join(asset_root, child)
                with open(pathname_file, encoding="utf8") as f:
                    line = f.readline().strip()
                    real_path = line
            elif child == "asset":
                has_asset = True
        if has_asset and real_path:
            mapping[entry] = real_path
    return mapping


def extract_unitypackage(
    unitypackage_path: str,
    dest_root: str,
    conflict_policy: str = "rename",
    ask_callback=None,
) -> List[Tuple[str, str]]:
    unitypackage_path = os.path.abspath(unitypackage_path)
    dest_root = os.path.abspath(dest_root)

    os.makedirs(dest_root, exist_ok=True)

    working_dir = os.path.join(dest_root, ".working_tmp")
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)

    with tarfile.open(unitypackage_path, "r:gz", encoding="utf8") as tar:
        tar.extractall(working_dir)

    mapping = build_mapping(unitypackage_path, working_dir)

    results: List[Tuple[str, str]] = []

    for asset_hash, real_rel_path in mapping.items():
        dest_dir, filename = os.path.split(real_rel_path)
        target_dir = os.path.join(dest_root, dest_dir)
        target_path = os.path.join(target_dir, filename)
        source_path = os.path.join(working_dir, asset_hash, "asset")

        os.makedirs(target_dir, exist_ok=True)

        final_target = target_path
        if os.path.exists(target_path):
            decision = conflict_policy
            if decision == "skip":
                pass
            elif decision == "overwrite":
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    try:
                        os.remove(target_path)
                    except FileNotFoundError:
                        pass
                shutil.move(source_path, target_path)
                os.chmod(target_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                final_target = target_path
            elif decision == "rename":
                base, ext = os.path.splitext(target_path)
                i = 1
                new_path = f"{base} ({i}){ext}"
                while os.path.exists(new_path):
                    i += 1
                    new_path = f"{base} ({i}){ext}"
                shutil.move(source_path, new_path)
                os.chmod(new_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                final_target = new_path
            else:
                pass
        else:
            shutil.move(source_path, target_path)
            os.chmod(target_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            final_target = target_path

        results.append((asset_hash, real_rel_path if final_target == target_path else os.path.relpath(final_target, dest_root)))

    shutil.rmtree(working_dir, ignore_errors=True)

    return results


def extract_multiple(
    unitypackages: Iterable[str],
    output_dir: str,
    mode: str = "merge",
    conflict_policy: str = "rename",
    ask_callback=None,
):
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    all_results = {}

    for upath in unitypackages:
        upath = os.path.abspath(upath)
        name, _ = os.path.splitext(os.path.basename(upath))
        if mode == "individual":
            dest = os.path.join(output_dir, name)
        else:
            dest = output_dir
        os.makedirs(dest, exist_ok=True)
        results = extract_unitypackage(
            unitypackage_path=upath,
            dest_root=dest,
            conflict_policy=conflict_policy,
            ask_callback=ask_callback,
        )
        all_results[upath] = results

    return all_results
