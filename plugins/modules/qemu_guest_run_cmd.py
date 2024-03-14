import base64
import json
import time
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule


def parse_stdout_stderr(raw_out):
    def decode_base64_data(key):
        try:
            return base64.b64decode(raw_out["return"].get(key, "")).decode("UTF-8")
        except KeyError:
            return ""

    return decode_base64_data("out-data"), decode_base64_data("err-data")


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
        raise RuntimeError(
            f"virsh qemu-agent-command guest-exec returned nonzero exit code; stderr={stderr}"
        )

    try:
        result_pid_json = json.loads(stdout)
        exited = result_pid_json["return"]["exited"]
        return exited, result_pid_json
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON from qemu-agent-command; stdout={stdout}",
        ) from e


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
        raise RuntimeError(
            f"virsh qemu-agent-command guest-exec returned nonzero exit code; stderr={stderr}",
        )
    try:
        return int(json.loads(stdout)["return"]["pid"])
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON from qemu-agent-command; stdout={stdout}",
        ) from e


def run_qemu_agent_command(
    module: AnsibleModule, domain: str, command: str, timeout: float, poll: float
):
    pid = execute_command(module, domain, command)
    start_time = datetime.now()

    while True:
        exited, raw_out = get_status(module, domain, pid)
        if exited:
            stdout, stderr = parse_stdout_stderr(raw_out)
            rc = int(raw_out["return"].get("exitcode", 0))
            return rc, stdout, stderr

        if (datetime.now() - start_time).total_seconds() > timeout:
            raise RuntimeError(
                f"Command timed out after {timeout} seconds",
            )

        time.sleep(poll)


def run_module(
    module: AnsibleModule, domain: str, command: str, timeout: float, poll: float
):
    try:
        rc, stdout, stderr = run_qemu_agent_command(
            module, domain, command, timeout, poll
        )
        output = {"rc": rc, "stdout": stdout, "stderr": stderr}
        module.exit_json(changed=True, output=output)
    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    module_args = {
        "domain": {"type": "str", "required": True},
        "command": {"type": "str", "required": True},
        "timeout": {"type": "float", "required": True},
        "poll": {"type": "float", "required": True},
    }
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    domain = module.params["domain"]  # type: ignore
    command = module.params["command"]  # type: ignore
    timeout = module.params["timeout"]  # type: ignore
    poll = module.params["poll"]  # type: ignore

    run_module(module, domain, command, timeout, poll)


if __name__ == "__main__":
    main()
