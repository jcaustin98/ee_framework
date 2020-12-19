from typing import Any, Callable, Dict, Optional


class EventNameSpace(object):
    event_hooks: Dict = {}
    event_wild_hooks: Dict = {}
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance

    def _set_handler(self, event_name: str, hooks: Dict, hook_fn: Callable[[Dict], Dict]) -> None:
        handlers = hooks.get(event_name, None)
        if handlers is None:
            hooks[event_name] = []
            handlers = hooks.get(event_name, None)
        handlers += [hook_fn]

    def get_hook_fn(self, obj: Any) -> Callable[[Dict], Dict]:
        try:
            hook_fn = getattr(obj, 'write')
        except AttributeError:
            raise ValueError(f"ERROR Event object has no write method")

        return hook_fn

    def register(self, event_names: str, hook_fn: Callable[[Dict], Dict]) -> None:
        for event_name in event_names:
            if '*' in event_name:
                self._set_handler(event_name, self.event_wild_hooks, hook_fn)
            else:
                self._set_handler(event_name, self.event_hooks, hook_fn)

    def pipeline_return(self, pipe_ret: Dict, **kwargs: str) -> Dict:
        if type(pipe_ret) == type({}):
            kwargs = {**kwargs, **pipe_ret}
        return kwargs

    def emit(self, *args: str, **kwargs: str) -> None:
        (event_name, *rest) = args
        kwargs["event_name"] = event_name

        for handler in self.event_hooks.get(event_name, []):
            hook_ret = handler(**kwargs)
            kwargs = self.pipeline_return(hook_ret, **kwargs)
            
        for name, funcs in self.event_wild_hooks.items():
            if (name[0] == '*' and event_name.endswith(name[1:])) \
                or (name[-1] == '*' and event_name.startswith(name[:-1])):
                    for func in funcs:
                        hook_ret = func(**kwargs)
                        kwargs = self.pipeline_return(hook_ret, **kwargs)

    def __str__(self) -> str:
        keys = self.event_hooks.keys()
        return ", ".join(keys)
