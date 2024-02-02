import base64
import json
import time
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule


class QemuGuestRunCmd:
    @staticmethod
    def parse_stdout_stderr(raw_out):
        def decode_base64_data(key):
            try:
                return base64.b64decode(raw_out["return"].get(key, "")).decode("UTF-8")
            except KeyError:
                return ""

        return decode_base64_data("out-data"), decode_base64_data("err-data")

    @staticmethod
    def get_status(module: AnsibleModule, domain: str, pid: int):
        my_cmd_json_pid = json.dumps(
            {"execute": "guest-exec-status", "arguments": {"pid": pid}}
        )
        rc, stdout, stderr = module.run_command(
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

        if rc != 0:
            module.fail_json(
                msg="virsh guest-exec-status failed", stdout=stdout, stderr=stderr
            )

        try:
            result_pid_json = json.loads(stdout)
            exited = result_pid_json["return"]["exited"]
            return exited, result_pid_json
        except json.JSONDecodeError:
            module.fail_json(
                msg="Failed to parse JSON from guest-exec-status", stdout=stdout
            )

        return False, {}

    # execute cmd via guest-exec, return process id (pid)
    @staticmethod
    def execute_command(module: AnsibleModule, domain: str, command: str):
        guest_exec_cmd_json = json.dumps(
            {
                "execute": "guest-exec",
                "arguments": {
                    "path": "/bin/bash",
                    "arg": ["-c", command],
                    "capture-output": True,
                },
            }
        )

        rc, stdout, stderr = module.run_command(
            [
                "virsh",
                "-c",
                "qemu:///system",
                "qemu-agent-command",
                domain,
                guest_exec_cmd_json,
            ],
            encoding="utf-8",
        )
        if rc != 0:
            module.fail_json(
                msg="virsh qemu-agent-command failed", stdout=stdout, stderr=stderr
            )
            return 0, True

        try:
            pid = int(json.loads(stdout)["return"]["pid"])
            return pid, False
        except json.JSONDecodeError:
            module.fail_json(
                msg="Failed to parse JSON from qemu-agent-command", stdout=stdout
            )
            return 0, True

    @staticmethod
    def run(
        module: AnsibleModule, domain: str, command: str, timeout: float, poll: float
    ):
        pid, failed = QemuGuestRunCmd.execute_command(module, domain, command)
        if failed:
            return

        start_time = datetime.now()

        while True:
            exited, raw_out = QemuGuestRunCmd.get_status(module, domain, pid)
            if exited:
                stdout, stderr = QemuGuestRunCmd.parse_stdout_stderr(raw_out)
                rc = int(raw_out["return"].get("exitcode", 0))
                module.exit_json(
                    changed=True,
                    output={"stdout": stdout, "stderr": stderr, "rc": rc},
                )
                break

            if (datetime.now() - start_time).total_seconds() > timeout:
                module.fail_json(
                    msg=f"Command timed out after {timeout} seconds",
                )
                break

            time.sleep(poll)


def main():
    module_args = {
        "domain": {"type": "str", "required": True},
        "command": {"type": "str", "required": True},
        "timeout": {"type": "float", "default": 30.0},
        "poll": {"type": "float", "default": 0.5},
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    domain = module.params["domain"]  # type: ignore
    command = module.params["command"]  # type: ignore
    timeout = module.params["timeout"]  # type: ignore
    poll = module.params["poll"]  # type: ignore

    QemuGuestRunCmd.run(module, domain, command, timeout, poll)  # type: ignore


if __name__ == "__main__":
    main()
