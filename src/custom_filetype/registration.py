import os
import sys
import uuid
import winreg as reg
from pathlib import Path
import win32con
import win32gui
from win32comext.shell.shell import SHChangeNotify
from win32comext.shell.shellcon import SHCNE_ASSOCCHANGED, SHCNF_IDLIST


def generate_clsid():
    new_id = uuid.uuid4()
    clsid = str(new_id).upper()  # Typically CLSIDs are represented in uppercase
    return clsid


def register_custom_filetype(spec = None):
    if spec is None:
        possibilities = [p for p in Path.cwd().iterdir() if p.suffix in [".yaml", ".yml", ".json"]]
        if len(possibilities)> 1:
            good = []
            for p in possibilities:
                try:
                    s = _load_spec(p)
                    good.append((s, p))
                except Exception as e:
                    print(f"Found error in {p}: {e}")
            if not good:
                raise ValueError(f"Found {len(possibilities)} but no legal spec: {possibilities}")
            if len(good) > 1:
                raise ValueError(f"Found more than one legal spec: {[s for s, _ in good]}")
            s, p = good[0]
            app_dir = Path.cwd()
            spec = p
        else:
            app_dir = Path.cwd()
            spec = _load_spec(possibilities[0])
    elif isinstance(spec, (str, Path)):
        spec = Path(spec)
        app_dir = spec.parent
        spec = _load_spec(spec)
    else:
        app_dir = Path.cwd()

    if "app_dir" not in spec:
        spec["app_dir"] = app_dir
    return _register_custom_filetype(**spec)


def _load_spec(spec):
    if spec.suffix == ".json":
        import json
        with spec.open() as f:
            spec = json.load(f)
    elif spec.suffix in [".yaml", ".yml"]:
        try:
            import yaml
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError("run `pip install PyYAML`") from e
        with spec.open() as f:
            spec = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported filetype: {spec.suffix}")
    _validate_spec(spec)
    return spec


def _validate_spec(spec, allow_extra_keys = True):
    checks = {
        "extension": (True, str, lambda v: v.startswith(".")),
        "app_name": (True, str, lambda v: True),
        "launch_script": (True, str, lambda v: True),
        "app_dir": (False, str, lambda v: True),
        "thumbnail_script": (False, str, lambda v: True),
        "context_menu_scripts": (False, dict, lambda v: all(isinstance(_k, str) and isinstance(_v, str) for _k, _v in v.items()))
    }
    for k, v in checks.items():
        req, t, check = checks[k]
        if k not in spec:
            if req:
                raise ValueError(f"Key not found: {k}")
            continue
        val = spec[k]
        if not isinstance(val, t):
            raise TypeError(f"{k} should be {t}, but found {type(val)}")
        if not check(val):
            import inspect
            code = inspect.getsource(check)
            raise ValueError(f"{k} failed check: {code}")
    if (not allow_extra_keys) and (extra := [k not in checks for k in spec]):
        raise ValueError(f"found extra key(s): {extra}")


def _parse_inputs(extension,
                  app_name,
                  launch_script,
                  app_dir = None,
                  thumbnail_script = None,
                  context_menu_scripts = None):
    app_name = app_name.strip()
    extension = extension.strip()
    if isinstance(app_dir, Path):
        app_dir = str(app_dir.resolve())
    elif app_dir is None:
        app_dir = Path.cwd()
    app_dir = app_dir.replace("$HOME", str(Path.home().resolve())).replace("$CWD", str(Path.cwd().resolve()))
    replacements = {
        "$PYTHON": sys.executable,
        "$FILEPATH": "%1",
        "$APP_DIR": app_dir,
        "$HOME": str(Path.home().resolve()),
        "$CWD": str(Path.cwd().resolve())
    }

    def _replace(s):
        # replace placeholders in inputs
        for p, r in replacements.items():
            s = s.replace(p, r)
        return s

    # replace placeholders in inputs
    launch_script = _replace(launch_script)
    thumbnail_script = _replace(thumbnail_script) if thumbnail_script is not None else thumbnail_script

    if context_menu_scripts:
        for k, v in context_menu_scripts.items():
            context_menu_scripts[k] = _replace(v)
    return extension, app_name, launch_script, app_dir, thumbnail_script, context_menu_scripts


def _register_custom_filetype(extension,
                              app_name,
                              launch_script,
                              app_dir = None,
                              thumbnail_class_id = None,
                              thumbnail_script = None,
                              context_menu_scripts = None):

    extension, app_name, launch_script, app_dir, thumbnail_script, context_menu_scripts = _parse_inputs(extension, app_name, launch_script, app_dir, thumbnail_script, context_menu_scripts)
    prog_id = f"{app_name}{extension.upper()}"
    file_type = f'{app_name}.FileType{extension.upper()}'
    _confirm_admin_rights()
    _register_file_type(extension, file_type, thumbnail_class_id, app_name, prog_id, launch_script, context_menu_scripts)


def _confirm_admin_rights():
    """ Check if the script is run as an administrator. If not, relaunch as admin. """
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        # Windows specific check
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    print(f"Is admin: {is_admin}")

    if not is_admin:
        print("Script is not running with administrative privileges.")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)


def _register_file_type(extension, file_type, clsid, description, prog_id, launch_script, context_menu_scripts):
    # Base key for file type registration

    # Create extension key
    with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, f'Software\\Classes\\{extension}') as key:
        reg.SetValue(key, '', reg.REG_SZ, file_type)

    # Create the file type key and set a description
    with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, f'Software\\Classes\\{file_type}') as key:
        reg.SetValue(key, '', reg.REG_SZ, description)

    # Create the association to open the file
    with reg.CreateKey(reg.HKEY_LOCAL_MACHINE,
                       f"Software\\Classes\\{prog_id}\\shell\\open\\command") as key:
        reg.SetValue(key, "", reg.REG_SZ, launch_script)

    # Associate the COM server with the file type for thumbnails
    with reg.CreateKey(reg.HKEY_LOCAL_MACHINE,
                      f'Software\\Classes\\{file_type}\\shellex\\{{e357fccd-a995-4576-b01f-234630154e96}}') as key:
        reg.SetValue(key, '', reg.REG_SZ, clsid)

    with reg.CreateKey(reg.HKEY_CLASSES_ROOT,
                       f'SystemFileAssociations\\{extension}\\shellex\\{{e357fccd-a995-4576-b01f-234630154e96}}') as key:
        # Set the default value to the CLSID of your COM server
        reg.SetValue(key, '', reg.REG_SZ, clsid)

    if context_menu_scripts:
        for title, command in context_menu_scripts.items():
            with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, f"Software\\Classes\\{prog_id}\\shell\\RunScript\\command") as key:
                reg.SetValue(key, "", reg.REG_SZ, command)
            with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, f"Software\\Classes\\{prog_id}\\shell\\RunScript") as key:
                reg.SetValueEx(key, "MUIVerb", 0, reg.REG_SZ, title)


    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
