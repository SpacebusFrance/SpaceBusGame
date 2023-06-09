import inspect
from typing import Union, List

from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger

from engine.utils.logger import Logger


def send_event(_event_name, *_, **kwargs) -> None:
    """
    Dispatch an event. Any function listening to this event with the :func:`@event` decorator will be triggered.

    Args:
        _event_name (str): event name
        *_: **ignored**
        **kwargs: optional named arguments
    """
    # Logger.info(f'sending event "{_event_name}" with params, {kwargs}')
    # check if this event is recorded somewhere
    if f'event_{_event_name}' not in event_handler.events:
        Logger.error(f'-> no listener for event "{_event_name}" !')
    else:
        # send it
        messenger.send(f'event_{_event_name}', sentArgs=[kwargs])


class _EventHandler:
    """
    A utility class for handling events. Responsible for triggering **all** methods registered for an event whereas
    using :func:`messenger.accept` would trigger only the last registered function.

    Do not instantiate this class.
    """
    def __init__(self):
        self._methods = dict()

    def _on_event(self, name, kwargs):
        if name in self._methods:
            # Logger.info(f'-> catching event "{name}" with kwargs: {kwargs}')
            for func, args in self._methods[name]:
                func(*args, kwargs)

    def ignore(self, name: str, method: callable) -> None:
        if name in self._methods:
            self._methods[name] = [
                element for element in self._methods[name] if element[0] != method
            ]
            if len(self._methods[name]) == 0:
                messenger.ignore(name, self)
                self._methods.pop(name)

    @property
    def events(self):
        return list(self._methods.keys())

    def accept(self, name, method, extra_args):
        if name not in self._methods:
            self._methods[name] = []
            messenger.accept(name, self, lambda z: self._on_event(name, z), extraArgs=[], persistent=1)

        self._methods[name].append([method, extra_args])


event_handler = _EventHandler()
"""The event handler"""


def event(events: Union[str, List[str]]) -> callable:
    """
    Event listener decorator. Should be used to decorate any function that should be triggered for one or more events
    with

    .. code-block::

        @event('my_event')
        def on_my_event(self, arg1, arg2):
            print('event "my_event" triggered !')

    or with several events

    .. code-block::

        @event(['my_event_1', 'my_event_1'])
        def on_my_event(self, arg1, arg2):
            print('event "my_event_1" or "my_event_2" triggered !')

    .. important::

        If a class has one or more methods that should be triggered on event (decorated), it must inherits from
        :class:`EventClass` otherwise, no event will be triggered

    Args:
        events (str or list[str]): event(s) to listen to

    Returns:
        callable: decorator
    """
    def decorator(method):
        method.event_anchor = events
        doc = method.__doc__ or ""
        method.__doc__ = f'.. admonition:: Event \n\tTriggered by ``{events}`` event\n\n' + doc
        return method
    return decorator


class EventObject(DirectObject):
    """
    Base class from which any class listening to events should derive
    """
    def __init__(self):
        super().__init__()
        self.__events = []

        for name in dir(self):
            if not name.startswith('_') and not name.startswith('__'):
                method = getattr(self, name)
                if hasattr(method, 'event_anchor'):
                    events = getattr(method, 'event_anchor')

                    def _call(_method, kwargs):
                        # only send relevant arguments, ignore other ones
                        func_args = inspect.getfullargspec(_method).args
                        for key in kwargs.copy():
                            if key not in func_args:
                                kwargs.pop(key)
                        _method(**kwargs)

                    if isinstance(events, list):
                        for evt in events:
                            self.__events.append((f'event_{evt}', _call))
                            event_handler.accept(f'event_{evt}', _call, extra_args=[method])
                    elif isinstance(events, str):
                        self.__events.append((f'event_{events}', _call))
                        event_handler.accept(f'event_{events}', _call, extra_args=[method])

    def destroy(self):
        for evt in self.__events:
            event_handler.ignore(*evt)
        self.__events.clear()


if __name__ == '__main__':
    class A(EventObject):
        @event('test')
        def on_test(self, x=1, y=3):
            print('in on_test with', x, y)

        @event(['a', 'b'])
        def on_a_or_b(self, z):
            print('in on_a_or_b', z)


    class B(EventObject):
        @event('test')
        def test(self):
            print('inside test !')

    test = A()
    test2 = B()

    send_event('test', x=2, z=4)
    send_event('a', z=2)
    send_event('b', z=1)
