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

APP_NAME = config.app_name

_TIMERS = dict()
_COUNTERS = dict()


def _func_package_and_name(fn):
    if str(fn.__class__) == "<type 'instancemethod'>":
        return "{0}.{1}.{2}".format(APP_NAME, fn.im_class, fn.__name__)
    else:
        return "{0}.{1}.{2}".format(APP_NAME, fn.__module__, fn.__name__)

def timer(fn):
    """A decorator for timing a function invocation."""
    def decorated(fn, *args, **kwargs):
        func_package_and_name = _func_package_and_name(fn)
        try:
            my_timer = _TIMERS[func_package_and_name]
        except KeyError:
            my_timer = statsd.Timer(func_package_and_name)
            _TIMERS[func_package_and_name] = my_timer
        my_timer.start()
        rval = fn(*args, **kwargs)
        my_timer.stop(func_package_and_name)
        return rval
    return decorator(decorated, fn)

    
def counter(fn): 
    """A decorator for counting function invocations for a particular function"""
    def decorated(fn, *args, **kwargs):
        func_package_and_name = _func_package_and_name(fn)
        try:
            my_counter = _COUNTERS[func_package_and_name]
        except KeyError:
            my_counter = statsd.Counter(func_package_and_name)
            _COUNTERS[func_package_and_name] = my_counter
        my_counter += 1
        return fn(*args, **kwargs)

    print "decorator: counter called for {0}".format(_func_package_and_name(fn))
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
