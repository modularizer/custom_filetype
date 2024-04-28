import os
import sys
import uuid
import winreg as reg


def register_custom_filetype(extension, app_name, script, ThumbnailProviderClass, context_actions=None):
    _confirm_admin_rights()

    prog_id = f"{app_name}{extension.upper()}"
    file_type = f'{app_name}.FileType{extension.upper()}'
    cls_id = _generate_clsid()

    program_path = script if isinstance(script, list) else [script]
    if str(script).endswith(".py"):
        program_path = [sys.executable] + program_path

    _register_file_type(".cft", file_type, cls_id, app_name)
    _register_program_id(prog_id, program_path, ["--open"])
    for title, arg in context_actions.items():
        _add_context_menu_option(prog_id, program_path, title, [arg])

    import win32com.server.register
    print(f"Registering {ThumbnailProviderClass}")
    win32com.server.register.UseCommandLine(ThumbnailProviderClass)

    print("done!")


def _generate_clsid():
    new_id = uuid.uuid4()
    clsid = str(new_id).upper()  # Typically CLSIDs are represented in uppercase
    return clsid


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


def _register_program_id(prog_id, application_path, args):
    """ Register the application to handle the file type. """
    command = '"' + '" "'.join(application_path) + '" "%1" "' + '" "'.join(args) + '"'
    print(f"Registering {prog_id} with command: `{command}`")
    with reg.CreateKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\shell\\open\\command") as key:
        reg.SetValue(key, "", reg.REG_SZ, command)


def _add_context_menu_option(prog_id, application_path, menu_name, args):
    """ Add a context menu option for the file type. """
    command = '"' + '" "'.join(application_path) + '" "%1" "' + '" "'.join(args) + '"'
    print(f"Adding context menu option for {prog_id} with command: `{command}`")
    with reg.CreateKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\shell\\RunScript\\command") as key:
        reg.SetValue(key, "", reg.REG_SZ, command)
    with reg.CreateKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\shell\\RunScript") as key:
        reg.SetValueEx(key, "MUIVerb", 0, reg.REG_SZ, menu_name)


def _register_file_type(extension, file_type, clsid, description):
    # Base key for file type registration
    base_key_path = f'Software\\Classes\\'

    print(f"Registering file type: {file_type} with extension: {extension} and description: {description}")

    # Create extension key
    with reg.CreateKey(reg.HKEY_CURRENT_USER, base_key_path + extension) as key:
        reg.SetValue(key, '', reg.REG_SZ, file_type)

    # Create the file type key and set a description
    with reg.CreateKey(reg.HKEY_CURRENT_USER, base_key_path + file_type) as key:
        reg.SetValue(key, '', reg.REG_SZ, description)

    # Associate the COM server with the file type for thumbnails
    with reg.CreateKey(reg.HKEY_CURRENT_USER,
                          f'{base_key_path}{file_type}\\shellex\\{{e357fccd-a995-4576-b01f-234630154e96}}') as key:
        reg.SetValue(key, '', reg.REG_SZ, clsid)
