"""Function time decorator moddule.

Classes:
--------
- ProfilePlotter: Profile and plot given function execution time.

Functions:
----------
- ret_time_decorator: Decorator to time function. returning time taken.
"""

import functools
import timeit
from inspect import signature
import matplotlib.pyplot as plt


def ret_time_decorator(func):
    """Decorator to time function execution. Returns time taken."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return timeit.timeit(lambda: func(*args, **kwargs), number=1)
    return wrapper

def _dup_dict_without_keys(x, *args):
    """Duplicate given dict, exclude all other given keys."""
    return {k: v for k, v in x.items() if k not in args}


class _AbstractProfiler:
    def __init__(self):
        raise NotImplementedError

    def _get_profilefunc(self):
        return self._func

    def _run_and_time(self, kwargs):
        """Return a number representing function runtime."""
        return timeit.timeit(lambda: self._get_profilefunc()(**kwargs),
                             number=1)

    def _check_var_kwargs_and_key(self, init_kwargs, var_key):
        if len(init_kwargs) == 0:
            raise ValueError("Cannot take init with no parameters.")
        if not isinstance(init_kwargs, dict):
            raise TypeError("Kwargs must be of type dict.")
        if var_key not in init_kwargs:
            raise ValueError(f"Given varriable key {var_key} is not"
                             " in init_kwargs.")

    def _validate_func_in(self, func, kwargs):
        ret = _dup_dict_without_keys(kwargs, 'self')
        func_params = self._ret_func_param_list(func)
        if func_params != list(ret.keys()):
            raise ValueError("kwargs must match function parameter names.")
        return ret

    def _ret_func_param_list(self, method):
        # remove self as this appears in class method signature and not in
        # init signature
        return [k for k in signature(method).parameters.keys() if k != "self"]


class ProfilePlotter:
    """Profile and plot given functions by varying the designated variable.

    Methods:
    --------
    - set_func_profile: Add given profile under the label provided.
    - set_var_init_profile: Set a variable init profiler to the given label.
    - plot: Plot the results of all profilers and return fig, ax objs.
    """

    class _Profiler(_AbstractProfiler):
        """Class to store function with arguments and execute profiling of it.

        This class provides a means of generating lists of points for
        an x vs runtime graph.

        Usage Example:
        --------------
        def mergesort(array):
            ...
        kwargs = {'array': ([randomint() for j in range(i)] for i in range(50)}
        var_key = 'array' # the name of whatever parameter we wish to vary.
        var_conv_func = lambda x: len(x)
        prof = Profiler(mergesort, kwargs, var_key, var_conv_func)
        prof.profile()

        Methods:
        -------
        profile:
        """

        def __init__(self, func, kwargs, var_key, var_conv_func=None):
            """Initialise Profile object.

            Input:
            ------
            - func: function to profile
            - kwargs: a dictionary with keys matching the function's
                    variable names. The values in this dictionary should
                    be of the type required to execute the function one time
                    with one of the parameters being a list of different
                    valid inputs such that we have one variable agument and
                    the rest constant. If the function doesn't take any input
            - var_key: The key/name of the parameter that is being varied. This
                       arugment must be an object present in kwargs.

            Kwargs:
            -------
            var_conv_func -- function to apply to each input to the function
                             under the variable parameter. The return of this
                             function should be of the type and value required
                             to plot an x vs runtime plot.

            Raises:
            -------
            -- ValueError: Function with no arguments given,
                           kwargs keys and function argument names differ,
                           var_key is not in kwargs
            -- TypeError: Kwargs is not dict
            """
            self._check_var_kwargs_and_key(kwargs, var_key)
            self._kwargs = self._validate_func_in(func, kwargs)
            self._func = func
            self._var_key = var_key
            self._var_conv_func = var_conv_func

        def profile(self):
            """Run the function with the given inputs, return lists of points.

            Return:
            -------
            - lists of points [x1, x2...] [y1, y2...]. The x values are either
              the variable input to the function or the results of applying the
              conversion function to them. y values are function runtimes.
            """
            x = []
            runtimes = []
            var_values = self._kwargs[self._var_key]
            for var_val in var_values:
                # make var one value for call
                self._kwargs[self._var_key] = var_val
                runtime = self._run_and_time(self._kwargs)
                x_val = (var_val if self._var_conv_func is None
                         else self._var_conv_func(var_val))
                x.append(x_val)
                runtimes.append(runtime)
            self._kwargs[self._var_key] = var_values     # restore kwargs
            return x, runtimes

    class _VariableInitMethodProfiler(_AbstractProfiler):
        def __init__(self, class_init, init_kwargs, var_key,
                     method, method_kwargs, var_conv_func=None):
            """Initialise _VariableInitMethodProfiler.

            This profiler is for classes that are to have some init parameter
            modified to affect the time taken for the given function call
            to execute.

            Usage Example:
            --------------
            class NoFuncParam:
                def __init__(self, s_time):
                    self._s_time = s_time
                def func(self):
                    time.sleep(self._s_time)
            # give iterable for init param that will change function runtime
            ikwarg = {"s_time": (i/100 for i in range(10))}
            var_key = "s_time"  # name of argument (key) that is to vary
            mkwarg = {} # arguments of method
            conv_func = lamba x:100*x
            profiler = _VariableInitMethodProfiler(NoFuncParam, ikwarg, var_key,
                                                   NoFuncParam.func, mkwarg,
                                                   conv_func)
            x_vals, runtimes = profiler.profile()
            x_vals
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            runtimes
            [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]

            Input:
            ------
            class_init -- class object such that running class_init(...) creates
                          an instance of the class
            init_kwargs -- dict, keys are class init arguments. This can include
                           self, but the object stored in this key is discarded.
                           The object under each key should be such that they
                           will run the function with one of them being an
                           iterable of objects that will allow the function to
                           run. This argument is the variable argument that
                           should change the runtime of the function.
            var_key -- the argument that is to be varied in the class init to
                       change function runtime.
            method -- class method to profile
            method_kwargs -- dict, keys are method arguments, values are objects
                             that will run the method when passed to it.
            var_conv_func -- this function is applied to each value in the
                             variable argument.
            Raises:
            -------
            ValueError -- init_kwargs is empty,
                          init_kwargs doesn't match class init arguments,
                          method_kwargs doesn't match method arguments,
                          var_key not in init_kwargs.
            TypeError -- init_kwargs is not of type dict,
                         method_kwargs is not of type dict,
            """
            self._check_var_kwargs_and_key(init_kwargs, var_key)
            if not isinstance(method_kwargs, dict):
                raise TypeError("methods kwargs must be of type dict.")
            self._init_kwargs = self._validate_func_in(class_init, init_kwargs)
            self._method_kwargs = self._validate_func_in(method, method_kwargs)
            self._class_init = class_init
            self._var_key = var_key
            self._method = method
            self._var_conv_func = var_conv_func

        def _get_profilefunc(self):
            return self._method

        def profile(self):
            """Run the function with the given inputs, return lists of points.

            Return:
            -------
            - lists of points [x1, x2...] [y1, y2...]. The x values are either
              the variable input to the function or the results of applying the
              conversion function to them. y values are function runtimes.
            """
            x = []
            runtimes = []
            var_values = self._init_kwargs[self._var_key]
            for var_val in var_values:
                self._init_kwargs[self._var_key] = var_val
                self._method_kwargs["self"] = self._class_init(**self._init_kwargs)
                runtime = self._run_and_time(self._method_kwargs)
                x_val = (var_val if self._var_conv_func is None
                         else self._var_conv_func(var_val))
                x.append(x_val)
                runtimes.append(runtime)
            self._init_kwargs[self._var_key] = var_values     # restore kwargs
            return x, runtimes

    class _ProfileContainer:
        """Store profilers and associated information."""
        def __init__(self):
            self.profilers = {}

        def get_profiler(self, label):
            """Return profiler stored under given label."""
            return self.profilers[label]

        def add_profile(self, label, profile):
            self.profilers[label] = profile

        def __len__(self):
            return len(self.profilers)

        def __iter__(self):
            """Give label and profiler for each profiler present."""
            for k, v in self.profilers.items():
                yield k, v

    # ProfilePlotter
    def __init__(self, x_axis_label, y_axis_label):
        """ProfilePlotter Init.

        Input:
        ------
        - x_axis_label: str, label for plot x axis
        - y_axis_label: str, label for plot y axis

        Raises:
        -------
        - TypeError: if x_axis_label or y_axis_label are not strings
        """
        if (not isinstance(x_axis_label, str)
                or not isinstance(y_axis_label, str)):
            raise TypeError("axis label parameters must be strings")
        self.profilers = self._ProfileContainer()
        self.x_label = x_axis_label
        self.y_label = y_axis_label

    def set_func_profile(self, label, func, kwargs, var_key, var_conv_func=None):
        """Profile given function. Label the resutls with label in the plot.

        This funtion is suitable for functions or class methods that don't
        require any change to instance/class variables.

        Input:
        -----
        label -- str, name of the dataset for the plot
        func -- function pointer, funtion to be tested.
        kwargs -- dict,
        var_key -- the name of the variable argument key

        Keyword Arguments:
        var_conv_func -- function to convert variable argument obejects to x
                         axis values
        """
        if not isinstance(label, str):
            raise TypeError("argument label must be of type string. got type"
                            f" {type(label)}")
        profiler = self._Profiler(func, kwargs, var_key,
                                  var_conv_func=var_conv_func)
        self.profilers.add_profile(label, profiler)

    def set_var_init_profile(self, label, class_init, init_kwargs, var_key,
                             method, method_kwargs, var_conv_func=None):
        """Set a variable init profiler to the given label.

        This profiler will measure the runtime of a method that is dependant
        on the values given at the object's construction.

        Input:
        ------
        label -- str, name of the dataset for the plot
        class_init -- obj, class constructor
        init_kwargs -- dict, dict with keys matching constructor and values to
                        give to it. Note: one of the keys must have an iterable
                        of values.
        var_key -- str, the key in the init_kwargs that is to be varied. The
                   value stored under this key should be an iterable of values.
        method -- method to profile
        method_kwargs -- dict, parameters and values to run the method.
        var_conv_func -- function, function to apply to each element in the
                         variable parameter iterable (see var_key).
        """
        if not isinstance(label, str):
            raise TypeError("argument label must be of type string. got type"
                            f" {type(label)}")
        profiler = self._VariableInitMethodProfiler(
            class_init, init_kwargs, var_key,
            method, method_kwargs, var_conv_func)
        self.profilers.add_profile(label, profiler)

    def plot(self):
        """Plot the results of all profilers and return fig, ax objs."""
        if (len(self.profilers) == 0):
            raise ValueError("No function profiles to be plotted.")
        fig, ax = plt.subplots(figsize=(19.2, 10.8))
        for label, profiler in self.profilers:
            ax.plot(*profiler.profile(), label=label)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.legend(loc="upper left")
        return fig, ax
