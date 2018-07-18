from collections import namedtuple

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from conf import settings

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()

MODULE_PATH = settings['ansible']['module_path']


class ResultCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        display.warning('v2_runner_on_unreachable')
        display.warning(result)
        self.host_unreachable[result._host.get_name()] = {
            "unreachable": result._result.get("unreachable"),
            "msg": result._result.get("msg")}

    def v2_runner_on_failed(self, result, *args, **kwargs):
        display.warning('v2_runner_on_failed')
        display.warning(result)
        self.host_failed[result._host.get_name()] = {
            "stdout_lines": result._result.get("stdout_lines"),
            "stderr_lines": result._result.get("stderr_lines"),
            "cmd": result._result.get("cmd"),
            "delta": result._result.get("delta"),
            "start": result._result.get("start"),
            "msg": result._result.get("msg"),
            'end': result._result.get("end"),
            "rc": result._result.get("rc"),
            "changed": result._result.get("changed")
        }

    def v2_runner_on_ok(self, result, **kwargs):
        display.warning('v2_runner_on_failed')
        display.warning(result)
        self.host_ok[result._host.get_name()] = {
            "stdout_lines": result._result.get("stdout_lines"),
            "stderr_lines": result._result.get("stderr_lines"),
            "cmd": result._result.get("cmd"),
            "delta": result._result.get("delta"),
            "start": result._result.get("start"),
            'end': result._result.get("end"),
            "rc": result._result.get("rc"),
            "changed": result._result.get("changed")}


def exec_ansible(host, tasks, remote_user='product', become=False, become_user=None):
    # initialize needed objects
    loader = DataLoader()

    Options = namedtuple('Options', [
        'connection', 'module_path', 'forks', 'become', 'become_method',
        'become_user', 'check', 'diff', 'remote_user'])
    options = Options(
        connection='smart',
        module_path=MODULE_PATH,
        forks=200,
        become=become,
        become_method='sudo',
        become_user=become_user,
        remote_user=remote_user,
        check=False,
        diff=False)

    passwords = dict(vault_pass='secret')

    # Instantiate our ResultCallback for handling results as they come in
    results_callback = ResultCallback()

    # create inventory and pass to var manager
    inventory = InventoryManager(loader=loader)
    inventory.add_host(host)

    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # create play with tasks
    play_source = dict(
        name="Ansible Play",
        hosts=[host],
        gather_facts='no',
        tasks=tasks)
    play = Play().load(
        play_source, variable_manager=variable_manager, loader=loader)

    # actually run it
    tqm = None
    try:
        display.warning(tasks)
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
            stdout_callback=results_callback
        )
        tqm.run(play)
    except Exception as e:
        display.warning('error')
        display.warning(e)
    finally:
        if tqm is not None:
            tqm.cleanup()

    def get_result():
        results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
        for _hosts, result in results_callback.host_ok.items():
            results_raw['success'][_hosts] = result
        for _hosts, result in results_callback.host_failed.items():
            results_raw['failed'][_hosts] = result
        for _hosts, result in results_callback.host_unreachable.items():
            results_raw['unreachable'][_hosts] = result

        return results_raw

    _get_result = get_result()
    return _get_result
