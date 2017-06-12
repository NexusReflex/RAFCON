# Copyright (C) 2015-2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Franz Steinmetz <franz.steinmetz@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

from weakref import ref
from gtkmvc import ModelMT, Signal

from rafcon.gui.models.signals import Notification
from rafcon.gui.models.meta import MetaModel
from rafcon.gui.models.abstract_state import AbstractStateModel

from rafcon.utils.hashable import Hashable
from rafcon.utils import log

logger = log.get_logger(__name__)


class StateElementModel(MetaModel, Hashable):
    """This model class serves as base class for all models within a state model (ports, connections)

    Each state element model has a parent, meta and temp data. If observes itself and informs the parent about changes.

    :param rafcon.gui.models.abstract_state.AbstractStateModel parent: The state model of the state element
    :param rafcon.utils.vividict.Vividict meta: The meta data of the state element model
    """

    _parent = None
    meta_signal = Signal()

    __observables__ = ("meta_signal",)

    def __init__(self, parent, meta=None):
        MetaModel.__init__(self, meta)

        self.parent = parent

        # this class is an observer of its own properties:
        self.register_observer(self)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.core_element != other.core_element:
            return False
        if self.meta != other.meta:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def update_hash(self, obj_hash):
        Hashable.update_hash_from_dict(obj_hash, self.meta)

    @property
    def parent(self):
        """Getter for the parent state model of the state element

        :return: None if parent is not defined, else the model of the parent state
        :rtype: rafcon.gui.models.abstract_state.AbstractState
        """
        if not self._parent:
            return None
        return self._parent()

    @parent.setter
    def parent(self, parent_m):
        """Setter for the parent state model of the state element

        :param rafcon.gui.models.abstract_state.AbstractState parent_m: Parent state model or None
        """
        if isinstance(parent_m, AbstractStateModel):
            self._parent = ref(parent_m)
        else:
            self._parent = None

    @property
    def core_element(self):
        """Return the core element represented by this model

        :return: core element of the model
        :rtype: rafcon.core.state_elements.state_element.StateElement
        """
        raise NotImplementedError()

    def get_state_machine_m(self):
        if self.parent:
            return self.parent.get_state_machine_m()
        return None

    def prepare_destruction(self):
        """Prepares the model for destruction

        Unregisters the model from observing itself.
        """
        try:
            self.unregister_observer(self)
        except KeyError:  # Might happen if the observer was already unregistered
            pass

    def model_changed(self, model, prop_name, info):
        """This method notifies the parent state about changes made to the state element
        """
        if self.parent is not None:
            self.parent.model_changed(model, prop_name, info)

    @ModelMT.observe("meta_signal", signal=True)
    def meta_changed(self, model, prop_name, info):
        """This method notifies the parent state about changes made to the meta data
        """
        if self.parent is not None:
            msg = info.arg
            # Add information about notification to the signal message
            notification = Notification(model, prop_name, info)
            msg = msg._replace(notification=notification)
            info.arg = msg
            self.parent.meta_changed(model, prop_name, info)
