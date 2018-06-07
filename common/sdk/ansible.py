from collections import namedtuple

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from conf import settings

MODULE_PATH = settings['ansible']['module_path']


class ResultCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    """A sample basecallback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` basecallback plugin
    or writing your own custom basecallback plugin
    """

    def v2_runner_on_unreachable(self, result):
        # self.host_unreachable[result._host.get_name()] = result
        self.host_unreachable[result._host.get_name()] = {"unreachable": result._result.get("unreachable"),
                                                          "msg": result._result.get("msg")}

        # print(json.dumps({host.name: result._result}, indent=4))

    def v2_runner_on_failed(self, result, *args, **kwargs):
        # self.host_failed[result._host.get_name()] = result
        self.host_failed[result._host.get_name()] = {"stdout_lines": result._result.get("stdout_lines"),
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
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        # self.host_ok[result._host.get_name()] = result
        self.host_ok[result._host.get_name()] = {"stdout_lines": result._result.get("stdout_lines"),
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
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
            stdout_callback=results_callback
            # Use our custom basecallback instead of the ``default`` basecallback plugin

        )
        tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()

    def get_result():
        results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
        for _hosts, result in results_callback.host_ok.items():
            # results_raw['success'][_hosts] = result._result
            results_raw['success'][_hosts] = result
        for _hosts, result in results_callback.host_failed.items():
            # results_raw['failed'][_hosts] = result._result
            results_raw['failed'][_hosts] = result
        for _hosts, result in results_callback.host_unreachable.items():
            # results_raw['unreachable'][_hosts] = result._result
            results_raw['unreachable'][_hosts] = result

        return results_raw

    _get_result = get_result()
    return _get_result
