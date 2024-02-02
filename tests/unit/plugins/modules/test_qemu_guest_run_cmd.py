import base64
import json

import pytest
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.karlivory.zk.plugins.modules.qemu_guest_run_cmd import \
    run_module


def test_successful_command_execution(ansible_module):
    stdout = "some random words"
    stderr = "error executing command"
    ansible_module.run_command.side_effect = [
        exec_response(1234),
        status_response(False),
        status_response(True, 0, stdout, stderr),
    ]

    run_module(ansible_module, "testvm", "echo foo", 1, 0.01)
    ansible_module.exit_json.assert_called_once()
    call_args = ansible_module.exit_json.call_args[1]

    assert call_args["changed"] is True
    assert call_args["output"]["stdout"] == stdout
    assert call_args["output"]["stderr"] == stderr
    assert call_args["output"]["rc"] == 0


def test_nonzero_rc_execution(ansible_module):
    stdout = "123"
    stderr = "error executing command"

    ansible_module.run_command.side_effect = [
        exec_response(1234),
        status_response(False),
        status_response(False),
        status_response(True, 21, stdout, stderr),
    ]

    run_module(ansible_module, "testvm", "echo foo", 1, 0.01)
    ansible_module.exit_json.assert_called_once()
    call_args = ansible_module.exit_json.call_args[1]

    assert call_args["changed"] is True
    assert call_args["output"]["stdout"] == stdout
    assert call_args["output"]["stderr"] == stderr
    assert call_args["output"]["rc"] == 21


def test_timeout(ansible_module):
    ansible_module.run_command.side_effect = [
        exec_response(1234),
        *[status_response(False) for _ in range(11)],
        status_response(True, 0),
    ]

    run_module(ansible_module, "testvm", "echo foo", 1, 0.1)
    ansible_module.fail_json.assert_called_once()
    call_args = ansible_module.fail_json.call_args[1]

    assert "timed out" in call_args["msg"]


## -------------------------------------------------------------------------- ##
##                                 utils                                      ##
## -------------------------------------------------------------------------- ##


@pytest.fixture
def ansible_module(mocker):
    mock_module = mocker.MagicMock(spec=AnsibleModule)
    mock_module.run_command.return_value = (
        0,
        "",
        "",
    )
    return mock_module


def exec_response(pid: int):
    status: dict = {
        "return": {
            "pid": pid,
        }
    }
    return (
        0,
        json.dumps(status),
        "",
    )


def status_response(
    exited: bool, exit_code: int = 0, out_data: str = "", err_data: str = ""
):
    status: dict = {
        "return": {
            "exited": exited,
        }
    }
    if exited:
        status["return"]["exitcode"] = exit_code
        status["return"]["out-data"] = base64.b64encode(
            out_data.encode("utf-8")
        ).decode("utf-8")
        status["return"]["err-data"] = base64.b64encode(
            err_data.encode("utf-8")
        ).decode("utf-8")
    return (
        0,
        json.dumps(status),
        "",
    )
