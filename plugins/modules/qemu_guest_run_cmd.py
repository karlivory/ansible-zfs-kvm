import base64
import json
import time
from dataclasses import dataclass
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult, Utils)


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
    rc, stdout, _ = module.run_command(
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
            "virsh qemu-agent-command guest-exdc returned nonzero exit code"
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

    rc, stdout, _ = module.run_command(
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
            "virsh qemu-agent-command guest-exdc returned nonzero exit code",
        )
    try:
        return int(json.loads(stdout)["return"]["pid"])
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON from qemu-agent-command; stdout={stdout}",
        ) from e


@dataclass
class ModuleArgs:
    domain: str
    command: str
    timeout: float
    poll: float


def run_qemu_agent_command(module: AnsibleModule, args: ModuleArgs) -> ModuleResult:
    pid = execute_command(module, args.domain, args.command)
    start_time = datetime.now()

    while True:
        exited, raw_out = get_status(module, args.domain, pid)
        if exited:
            stdout, stderr = parse_stdout_stderr(raw_out)
            rc = int(raw_out["return"].get("exitcode", 0))
            return ModuleResult(
                changed=True,
                output={"stdout": stdout, "stderr": stderr, "rc": rc},
            )

        if (datetime.now() - start_time).total_seconds() > args.timeout:
            return ModuleResult(
                msg=f"Command timed out after {args.timeout} seconds",
                failed=True,
            )

        time.sleep(args.poll)


def main():
    # module_args = {
    #     "domain": {"type": "str", "required": True},
    #     "command": {"type": "str", "required": True},
    #     "timeout": {"type": "float", "default": 30.0},
    #     "poll": {"type": "float", "default": 0.5},
    # }

    # module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    # domain = module.params["domain"]  # type: ignore
    # command = module.params["command"]  # type: ignore
    # timeout = module.params["timeout"]  # type: ignore
    # poll = module.params["poll"]  # type: ignore

    # QemuGuestRunCmd.run(module, domain, command, timeout, poll)  # type: ignore

    Utils.run_module(ModuleArgs, run_qemu_agent_command)


if __name__ == "__main__":
    main()
