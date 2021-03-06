import pytest

from copy import deepcopy

from tests import utils


class GUITester(object):

    def __init__(self, with_gui=True, config=None):
        import rafcon.core.singleton as core_singletons
        import rafcon.gui.singleton as gui_singletons

        self.with_gui = with_gui
        self.config = config or {}
        self.post_test = None

        self.expected_warnings = 0
        self.expected_errors = 0

        self.singletons = gui_singletons
        self.core_singletons = core_singletons

    def restart(self, force_quit=False):
        utils.close_gui(force_quit=force_quit)
        utils.shutdown_environment()
        utils.run_gui(**deepcopy(self.config))

    def __call__(self, *args, **kwargs):
        from rafcon.gui.utils import wait_for_gui
        if self.with_gui:
            from rafcon.utils.gui_functions import call_gui_callback
            return_values = call_gui_callback(*args, **kwargs)
            call_gui_callback(wait_for_gui)
            return return_values
        else:
            func = args[0]
            result = func(*args[1:], **kwargs)
            # Now we manually need to run the GTK main loop to handle all asynchronous notifications
            # E.g., when a state machine is added to the manager (in the core), the models are in certain cases created
            # asynchronously, depending in which thread the manager model was created.
            wait_for_gui()
            return result



@pytest.fixture
def gui(request, caplog):
    parameters = {} if not hasattr(request, "param") else request.param
    with_gui = parameters.get("with_gui", True)

    config = {parameter_name: parameters.get(parameter_name) for parameter_name in
              ["core_config", "gui_config", "runtime_config", "libraries"]}

    utils.dummy_gui(caplog)
    if with_gui:
        utils.run_gui(**deepcopy(config))
    else:
        utils.initialize_environment(gui_already_started=False, **deepcopy(config))

    gui_tester = GUITester(with_gui, config)
    yield gui_tester

    try:
        if with_gui:
            utils.close_gui()
    finally:
        utils.shutdown_environment(caplog=caplog, unpatch_threading=with_gui,
                                   expected_warnings=gui_tester.expected_warnings,
                                   expected_errors=gui_tester.expected_errors)

        gui_tester.post_test and gui_tester.post_test()

