#!/usr/bin/env python

"""This module imports python-statsd and the decorator module (both
available under those name from pypy.python.org via e.g. the pip
command).

This makes two decorators available:

@timer
@counter

@timer will time the invocation of the function/method it's decorating
and send this info to the configured statsd server

@counter will increment a counter related to the function/method it's
decorating and send this info to the configured statsd server

There are the following utility methods, too:

instrument.disable_stats(): disables the statsd default config, so
    no stats will be sent unless and until enable_stats() is called

instrument.enable_stats(): enables reporting of stats to a statsd
    based on the configuration in config.py.

instrument.init_stats(): invokes instrument.enable_stats

config.py needs to have the following configuration present:

app_name         = "graph-explorer" # name that will prefix stats shipped to statsd.
statsd_params    = { "host"        : "your_statsd_host",
                     "port"        : 8125,
                     "sample_rate" : 1}


TODO: When the import fails, just provide noop decorators

"""

import statsd # uses https://pypi.python.org/pypi/python-statsd
from decorator import decorator 
import config
import threading
import inspect

APP_NAME = config.app_name

_TIMERS = dict()
_COUNTERS = dict()


def _func_package_and_name_thread(fn):
    if str(fn.__class__) == "<type 'instancemethod'>":
        return "{0}.{1}.{2}.{3}".format(APP_NAME, fn.im_class, fn.__name__, threading.current_thread().name)
    else:
        return "{0}.{1}.{2}.{3}".format(APP_NAME, fn.__module__, fn.__name__, threading.current_thread().name)

def _func_package_class_name(fn, args):
    """In a bound method, self is the first argument.  Generator
    functions/methods make asking some questions difficult, so this
    function should only be invoked when we know it'll be applied to a
    class method.  So only use it in the *_for_subclasses()
    decorators.

    """
    if len(args) > 0: # Must have self as the first argument
        is_class = inspect.isclass(args[0])  # we'll infer that this is self
        return "{0}.{1}.{2}.{3}".format(APP_NAME, args[0].__class__.__module__, args[0].__class__.__name__, fn.__name__)
    else:
        # The first invocation of this decorator will be called before the
        # method is bound.
        return "{0}.{1}.{2}".format(APP_NAME, fn.__module__, fn.__name__)
        
def _func_package_and_name(fn):
    if str(fn.__class__) == "<type 'instancemethod'>":
        return "{0}.{1}.{2}".format(APP_NAME, fn.im_class, fn.__name__)
    else:
        return "{0}.{1}.{2}".format(APP_NAME, fn.__module__, fn.__name__)

def timer_for_subclasses(fn):
    """A decorator to be used in a parent class.  This is specifically
    for timing a method that will be invoked in a subclass, where it's
    important that the metric name be tied to the name of the subclass
    of the decorated methods class.  So if I have class Foo, and I
    have a method called Foo.SomeThing, and I expect to invoke it from
    the subclasses of Foo: AFoo, BFoo, and CFoo.

    This case is when I need to distinguish between them or the data just
    won't make much sense.

    This works by looking at the first argument passed to this method,
    and if it is a class, it'll use the class name to distinctly
    associate the metric with the name of the subclass.

    """
    def decorated(fn, *args, **kwargs):
        """Decorates a function.  Reports the stats by function
        package/class and name.
        """
        func_info = _func_package_class_name(fn, args)
        my_timer = statsd.Timer(func_info)
        my_timer.start()
        rval = fn(*args, **kwargs)
        my_timer.stop()
        return rval
    return decorator(decorated, fn)
        
def timer(fn):
    """A decorator for timing a function invocation"""
    def decorated(fn, *args, **kwargs):
        """Decorates a function.  Reports the stats by function
        package/class and name.
        """
        func_info = _func_package_and_name(fn)
        my_timer = statsd.Timer(func_info)
        my_timer.start()
        rval = fn(*args, **kwargs)
        my_timer.stop()
        return rval
    return decorator(decorated, fn)


def counter_for_subclasses(fn): 
    """A decorator for counting function invocations for a particular
    function, but have the naming be aware of which class is invoking
    the method.

    """
    def decorated(fn, *args, **kwargs):
        func_info = _func_package_class_name(fn, args)
        try:
            my_counter = _COUNTERS[func_info]
        except KeyError:
            my_counter = statsd.Counter(func_info)
            _COUNTERS[func_info] = my_counter
        my_counter += 1
        return fn(*args, **kwargs)

    # print "decorator: counter called for {0}".format(_func_package_class_name(fn))
    return decorator(decorated, fn)

    
def counter(fn): 
    """A decorator for counting function invocations for a particular function"""
    def decorated(fn, *args, **kwargs):
        func_info = _func_package_and_name(fn)
        try:
            my_counter = _COUNTERS[func_info]
        except KeyError:
            my_counter = statsd.Counter(func_info)
            _COUNTERS[func_info] = my_counter
        my_counter += 1
        return fn(*args, **kwargs)

    # print "decorator: counter called for {0}".format(_func_package_class_name(fn))
    return decorator(decorated, fn)

def init_stats():
    enable_stats()
    
def enable_stats():
    statsd.Connection.set_defaults(
        host=config.statsd_params['host'],
        port=int(config.statsd_params['port']),
        sample_rate=int(config.statsd_params['sample_rate']),
        disabled=False
    )


def disable_stats():
    statsd.Connection.set_defaults(
        host=config.statsd_params['host'],
        port=int(config.statsd_params['port']),
        sample_rate=int(config.statsd_params['sample_rate']),
        disabled=True
    )
