import os
from timeit import default_timer as timer


# core elements
import rafcon.statemachine.singleton
from rafcon.statemachine.states.execution_state import ExecutionState
from rafcon.statemachine.states.hierarchy_state import HierarchyState
from rafcon.statemachine.states.barrier_concurrency_state import BarrierConcurrencyState
from rafcon.statemachine.states.preemptive_concurrency_state import PreemptiveConcurrencyState
from rafcon.statemachine.enums import UNIQUE_DECIDER_STATE_ID
from rafcon.statemachine.states.state import DataPortType
from rafcon.statemachine.state_machine import StateMachine


def measure_time(func):
    def func_wrapper(*args, **kwargs):
        start = timer()
        return_value = func(*args, **kwargs)
        end = timer()
        print "{0} (args: {1}; kwargs: {2}): {3}".format(func.__name__, str(args), str(kwargs), str((end - start)))
        return return_value
    return func_wrapper


@measure_time
def create_hierarchy_state(number_child_states=10):
    hierarchy = HierarchyState("hierarchy1")
    hierarchy.add_outcome("hierarchy_outcome", 1)
    hierarchy.add_input_data_port("hierarchy_input_port1", "float", 42.0)
    hierarchy.add_output_data_port("hierarchy_output_port1", "float")
    last_state = None

    for i in range(number_child_states):
        state = ExecutionState("state" + str(i))
        hierarchy.add_state(state)
        state.add_input_data_port("input1", "float")
        state.add_output_data_port("output1", "float")

        if not last_state:
            hierarchy.set_start_state(state.state_id)
            hierarchy.add_data_flow(hierarchy.state_id,
                                    hierarchy.get_io_data_port_id_from_name_and_type("hierarchy_input_port1",
                                                                                     DataPortType.INPUT),
                                    state.state_id,
                                    state.get_io_data_port_id_from_name_and_type("input1", DataPortType.INPUT))
        else:
            hierarchy.add_transition(last_state.state_id, 0, state.state_id, None)
            # connect data ports state 1
            hierarchy.add_data_flow(last_state.state_id,
                                 last_state.get_io_data_port_id_from_name_and_type("output1", DataPortType.OUTPUT),
                                 state.state_id,
                                 state.get_io_data_port_id_from_name_and_type("input1", DataPortType.INPUT))

        last_state = state

    hierarchy.add_data_flow(last_state.state_id,
                            last_state.get_io_data_port_id_from_name_and_type("output1",
                                                                              DataPortType.OUTPUT),
                            hierarchy.state_id,
                            hierarchy.get_io_data_port_id_from_name_and_type("hierarchy_output_port1",
                                                                             DataPortType.OUTPUT))

    hierarchy.add_transition(last_state.state_id, 0, hierarchy.state_id, 1)

    return hierarchy


def execute_state(root_state):
    state_machine = StateMachine(root_state)
    rafcon.statemachine.singleton.state_machine_manager.add_state_machine(state_machine)
    rafcon.statemachine.singleton.state_machine_manager.active_state_machine_id = state_machine.state_machine_id
    rafcon.statemachine.singleton.state_machine_execution_engine.start()
    rafcon.statemachine.singleton.state_machine_execution_engine.join()
    rafcon.statemachine.singleton.state_machine_manager.remove_state_machine(state_machine.state_machine_id)


@measure_time
def test_hierarchy_state_execution(number_child_states):
    hierarchy_state = create_hierarchy_state(number_child_states)
    execute_state(hierarchy_state)


@measure_time
def test_barrier_concurrency_state_execution(number_child_states=10, number_childs_per_child=10):

    barrier_state = BarrierConcurrencyState("barrier_concurrency")

    for i in range(number_child_states):
        hierarchy_state = create_hierarchy_state(number_childs_per_child)
        barrier_state.add_state(hierarchy_state)

    barrier_state.add_transition(barrier_state.states[UNIQUE_DECIDER_STATE_ID].state_id, 0, barrier_state.state_id, 0)
    execute_state(barrier_state)


@measure_time
def test_preemption_concurrency_state_execution(number_child_states=10, number_childs_per_child=10,
                                                number_of_childs_fast_state=3):

    preemption_state = PreemptiveConcurrencyState("preemption_concurrency")

    for i in range(number_child_states):
        hierarchy_state = create_hierarchy_state(number_childs_per_child)
        preemption_state.add_state(hierarchy_state)
        # preemption_state.add_transition(hierarchy_state.state_id, 0, preemption_state.state_id, 0)

    # add fast state
    hierarchy_state = create_hierarchy_state(number_of_childs_fast_state)
    preemption_state.add_state(hierarchy_state)
    preemption_state.add_transition(hierarchy_state.state_id, 1, preemption_state.state_id, 0)

    execute_state(preemption_state)


if __name__ == '__main__':
    # test_hierarchy_state_execution(10)
    test_hierarchy_state_execution(100)
    # TODO: state creation takes too long (> 100 seconds) => investigate
    # test_hierarchy_state_execution(1000)
    # test_barrier_concurrency_state_execution(10, 10)
    # test_barrier_concurrency_state_execution(100, 100)
    # test_preemption_concurrency_state_execution(50, 20, 3)
