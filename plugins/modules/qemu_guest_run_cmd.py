# credit: https://technekey.com/simplifying-vm-management-executing-commands-in-guest-vms-using-virsh/

import base64
import json
import time
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule


class QemuGuestRunCmd:
    @staticmethod
    def parse_stdout_stderr(raw_out):
        try:
            base64_out = base64.b64decode(raw_out["return"]["out-data"]).decode("UTF-8")
        except KeyError as _:
            base64_out = ""
        try:
            base64_err = base64.b64decode(raw_out["return"]["err-data"]).decode("UTF-8")
        except KeyError as _:
            base64_err = ""
        return base64_out, base64_err

    @staticmethod
    def get_status(module, domain, pid):
        # build the JSON body for PID status check
        my_cmd_json_pid = json.dumps(
            {"execute": "guest-exec-status", "arguments": {"pid": pid}}
        )
        # Get the status of the PID
        cmd_return_code, cmd_run_stdout, cmd_run_stderr = module.run_command(
            [
                "virsh",
                "-c",
                "qemu:///system",
                "qemu-agent-command",
                domain,
                my_cmd_json_pid,
            ],
            encoding="utf-8",
        )

        if cmd_return_code != 0:
            module.fail_json(
                msg={
                    "msg": "virsh guest-exec-status failed!",
                    "stdout": cmd_run_stdout,
                    "stderr": cmd_run_stderr,
                }
            )

        try:
            result_pid_json = json.loads(cmd_run_stdout)
            if result_pid_json["return"]["exited"]:
                return True, result_pid_json
        except ValueError:
            module.fail_json(
                msg=f"Failed to parse command output as JSON in getting status. Output: {cmd_run_stdout}"
            )

        return False, {}

    @staticmethod
    def run(
        module: AnsibleModule, domain: str, command: str, timeout: int, poll: float
    ):
        try:
            my_cmd_json = json.dumps(
                {
                    "execute": "guest-exec",
                    "arguments": {
                        "path": "/bin/bash",
                        "arg": ["-c", f"{command}"],
                        "capture-output": True,
                    },
                }
            )

            cmd_return_code, cmd_run_stdout, cmd_run_stderr = module.run_command(
                [
                    "virsh",
                    "-c",
                    "qemu:///system",
                    "qemu-agent-command",
                    domain,
                    my_cmd_json,
                ],
                encoding="utf-8",
            )
            if cmd_return_code != 0:
                module.fail_json(
                    msg={
                        "msg": "virsh qemu-agent-command failed",
                        "stdout": cmd_run_stdout,
                        "stderr": cmd_run_stderr,
                    },
                )
            try:
                cmd_run_stdout_json = json.loads(cmd_run_stdout)
                pid = cmd_run_stdout_json["return"]["pid"]

                cmd_exited = False
                start_time = datetime.now()

                raw_out = {}
                while not cmd_exited:
                    cmd_exited, raw_out = QemuGuestRunCmd.get_status(
                        module, domain, pid
                    )
                    time_delta = datetime.now() - start_time
                    if time_delta.total_seconds() >= float(timeout):
                        module.fail_json(
                            msg=f"virsh qemu-agent-command timed out! (timeout={timeout})"
                        )
                    time.sleep(poll)

                stdout, stderr = QemuGuestRunCmd.parse_stdout_stderr(raw_out)

                failed = False
                rc = raw_out["return"]["exitcode"]
                if rc:
                    try:
                        rc = int(rc)
                        failed = rc != 0
                    except:
                        pass

                module.exit_json(
                    changed=True,
                    output={"stdout": stdout, "stderr": stderr, "rc": rc},
                    failed=failed,
                )
            except ValueError:
                module.fail_json(
                    msg={
                        "msg": "Failed to parse command stdout as JSON",
                        "stdout": cmd_run_stdout,
                    },
                )
        except Exception as e:
            module.fail_json(
                msg=str(e),
            )


def main():
    module_args = {
        "domain": {"type": "str", "required": True},
        "command": {"type": "str", "required": True},
        "timeout": {"type": "float", "default": 30.0},
        "poll": {"type": "float", "default": 0.5},
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    domain = str(module.params["domain"])
    command = str(module.params["command"])
    timeout = int(module.params["timeout"])
    poll = float(module.params["poll"])
    QemuGuestRunCmd.run(module, domain, command, timeout, poll)


if __name__ == "__main__":
    main()
