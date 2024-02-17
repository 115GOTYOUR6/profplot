"""Testing for func_decorators module."""

import unittest
import time
import profplot
from profplot import ProfilePlotter as pp


class TestFuncDecorators(unittest.TestCase):
    def test_ret_rime_decorator(self):
        @ profplot.ret_time_decorator
        def wait_0_1():
            time.sleep(0.1)
        @ profplot.ret_time_decorator
        def wait_1():
            time.sleep(0.01)

        dec_place_accuracy = 1
        self.assertAlmostEqual(wait_0_1(), 0.1, dec_place_accuracy)
        self.assertAlmostEqual(wait_1(), 0.01, dec_place_accuracy)

class TestFunctions(unittest.TestCase):
    def test__dup_kwargs_without_keys(self):
        def dummy(n):
            pass
        # straight copy
        kwargs = {'n':43}
        kwargs_cop = dict(kwargs)
        exp = {'n':43}
        dup = profplot._dup_dict_without_keys(kwargs)
        self.assertEqual(exp, dup)
        self.assertEqual(kwargs_cop, kwargs)   # check no mutation
        # check it removes key
        kwargs = {'n':43}
        kwargs_cop = dict(kwargs)
        exp = {}
        dup = profplot._dup_dict_without_keys(kwargs, 'n')
        self.assertEqual(exp, dup)
        self.assertEqual(kwargs_cop, kwargs)   # check no mutation
        # check we can supply keys not in dict
        kwargs = {'n':43}
        kwargs_cop = dict(kwargs)
        exp = {'n':43}
        dup = profplot._dup_dict_without_keys(kwargs, 'sdlkfj', 343, "daf")
        self.assertEqual(exp, dup)
        self.assertEqual(kwargs_cop, kwargs)   # check no mutation
        # remove multiple keys
        kwargs = {'n':43, 'f': 0, "y": []}
        kwargs_cop = dict(kwargs)
        exp = {'y':[]}
        dup = profplot._dup_dict_without_keys(kwargs, 'n', 'f')
        self.assertEqual(exp, dup)
        self.assertEqual(kwargs_cop, kwargs)   # check no mutation


class TestProfilerClass(unittest.TestCase):
    def test__init__(self):
        # bad input
        def bad_in_test_helper(func, kwargs, var_key, ex):
            with self.assertRaises(ex):
                pp._Profiler(func, kwargs, var_key)
        # no func args
        def func1():
            pass
        bad_in_test_helper(func1, {}, None, ValueError)
        # kwargs doesn't match func args
        def func2(a):
            pass
        bad_in_test_helper(func2, {'a':34, 'f':4}, 'a', ValueError)
        # var_key not in kwargs
        bad_in_test_helper(func2, {'a':34}, None, ValueError)
        bad_in_test_helper(func2, {'a':34}, 43, ValueError)
        # kwargs is not a dict
        bad_in_test_helper(func2, [('a', 34)], 'a', TypeError)
        # ok input
        def func(x):
            return x
        kwargs = {'x': [1, 2, 3]}
        var_key = 'x'
        var_conv_func = lambda x: x**2
        profiler = pp._Profiler(func, kwargs, var_key, var_conv_func)
        self.assertEqual(profiler._func, func)
        self.assertEqual(profiler._kwargs, kwargs)
        self.assertEqual(profiler._var_key, var_key)
        self.assertEqual(profiler._var_conv_func, var_conv_func)

    def test__run_and_time(self):
        def run_and_time_test_helper(sleep_time, kwargs, var_key):
            def func(x):
                time.sleep(sleep_time)
                return x
            profiler = pp._Profiler(func, kwargs, var_key)
            exp_sleep_time = len(kwargs[var_key])*sleep_time
            self.assertGreaterEqual(profiler._run_and_time(kwargs), exp_sleep_time)

            var_key = 'x'
            kwargs = {'x': []}
            run_and_time_test_helper(0.1, kwargs, var_key)
            var_key = 'x'
            kwargs = {'x': [1]}
            run_and_time_test_helper(0.1, kwargs, var_key)
            var_key = 'x'
            kwargs = {'x': [43, 52, 51, 9]}
            run_and_time_test_helper(0.1, kwargs, var_key)

    def test_profile(self):
        def profiler_test_helper(func, kwargs, var_key, exp_x_vals, exp_stime,
                                 conv_func=None):
            profiler = pp._Profiler(func, kwargs, var_key, conv_func)
            x_vals, run_times = profiler.profile()
            t_stime = 0
            for ind, val in enumerate(x_vals):
                t_stime += run_times[ind]
                self.assertEqual(val, exp_x_vals[ind])
            self.assertGreaterEqual(t_stime, exp_stime)
        def func(a):
            time.sleep(a)
        kwargs = {'a': []}
        var_key = 'a'
        exp_x_vals = []
        exp_stime = 0
        profiler_test_helper(func, kwargs, var_key, exp_x_vals, exp_stime)
        kwargs = {'a': [0.03]}
        var_key = 'a'
        exp_x_vals = [0.03]
        exp_stime = sum(kwargs[var_key])
        profiler_test_helper(func, kwargs, var_key, exp_x_vals, exp_stime)
        kwargs = {'a': [0.03, 0.01, 0.003]}
        var_key = 'a'
        exp_x_vals = [0.03, 0.01, 0.003]
        exp_stime = sum(kwargs[var_key])
        profiler_test_helper(func, kwargs, var_key, exp_x_vals, exp_stime)
        # two arg function
        def func2(a, b):
            time.sleep(a)
        kwargs = {'a': [0.044, 0.08, 0.001], 'b': 10}
        var_key = 'a'
        exp_x_vals = [0.044, 0.08, 0.001]
        exp_stime = sum(kwargs[var_key])
        profiler_test_helper(func2, kwargs, var_key, exp_x_vals, exp_stime)
        kwargs = {'a': [0.04, 0.08, 0.001], 'b': 10}
        var_key = 'a'
        conv_func = lambda x: x**2
        exp_x_vals = [0.0016, 0.0064, 0.000001]
        exp_stime = sum(kwargs[var_key])
        profiler_test_helper(func2, kwargs, var_key, exp_x_vals, exp_stime, conv_func)
        def func3(a, b):
            time.sleep(sum(a))
        kwargs = {'a': [[], [0.32], [0.034, 0.087]], 'b': 10}
        var_key = 'a'
        conv_func = lambda x:len(x)
        exp_x_vals = [0, 1, 2]
        exp_stime = sum((sum(i) for i in kwargs[var_key]))
        profiler_test_helper(func3, kwargs, var_key, exp_x_vals, exp_stime, conv_func)


class Test_VariableInitMethodProfilerClass(unittest.TestCase):
    def init_raises(self, ex, loc_class, ikwargs, var_key, mkwargs, conv_func=None):
        with self.assertRaises(ex):
            pp._VariableInitMethodProfiler(loc_class, ikwargs, var_key,
                                           loc_class.func, mkwargs, conv_func)

    def bad_init_combo_tests(self, loc_class):
        # mismatch function and init arg names
        self.init_raises(ValueError, loc_class, {'a':40}, 'b', {})
        self.init_raises(ValueError, loc_class, {'a':40}, 'a', {})
        # empty init kwarg
        self.init_raises(ValueError, loc_class, {}, None, {})
        self.init_raises(ValueError, loc_class, {}, None, {'s_time':4})
        self.init_raises(ValueError, loc_class, {}, None, {'self':432})
        self.init_raises(ValueError, loc_class, {}, None, {'self':432,'s_time':4})
        # valid input but wrong kwargs datatype
        self.init_raises(TypeError, loc_class, [('s_time',8)], 's_time', {})
        self.init_raises(TypeError, loc_class, {'s_time':8}, 's_time', [])
        self.init_raises(TypeError, loc_class, [('s_time',8)], 's_time', {'s_time':4})
        self.init_raises(TypeError, loc_class, {'s_time':8}, 's_time', [('s_time',4)])

    def should_fail_on_valid_init_combo(self, loc_class):
        self.init_raises(ValueError, loc_class, {'self':3, 's_time':8}, 's_time', {'self':432,'s_time':4})
        self.init_raises(ValueError, loc_class, {'s_time':8}, 's_time', {'self':432,'s_time':4})
        self.init_raises(ValueError, loc_class, {'self':3, 's_time':8}, 's_time', {'s_time':4})
        self.init_raises(ValueError, loc_class, {'s_time':8}, 's_time', {'s_time':4})

        self.init_raises(ValueError, loc_class, {'self':3, 's_time':8}, 's_time', {'self':432})
        self.init_raises(ValueError, loc_class, {'s_time':8}, 's_time', {'self':432})
        self.init_raises(ValueError, loc_class, {'self':3, 's_time':8}, 's_time', {})
        self.init_raises(ValueError, loc_class, {'s_time':8}, 's_time', {})

    def test__init__(self):
        # this class should fail on all input. It doesn't have init params
        class NoInitParam:
            def __init__(self):
                pass
            def func(self, s_time):
                time.sleep(s_time)
        self.bad_init_combo_tests(NoInitParam)
        self.should_fail_on_valid_init_combo(NoInitParam)
        # this is also a bad class, no init params
        class NoInitParamNoFuncParam:
            def __init__(self):
                self._s_time = 0.5
            def func(self):
                time.sleep(self._s_time)
        self.bad_init_combo_tests(NoInitParamNoFuncParam)
        self.should_fail_on_valid_init_combo(NoInitParamNoFuncParam)
        # these classes should be valid on valid input
        class NoFuncParam:
            def __init__(self, s_time):
                self._s_time = s_time
            def func(self):
                time.sleep(self._s_time)
        self.bad_init_combo_tests(NoFuncParam)
        class InitAndParam:
            def __init__(self, s_time):
                self._s_time = s_time
            def func(self, s_time):
                time.sleep(self._s_time + s_time)
        self.bad_init_combo_tests(InitAndParam)
        # ok, function call can include self in kwargs or exclude it
        pp._VariableInitMethodProfiler(NoFuncParam, {'s_time': 49}, 's_time',
                                       NoFuncParam.func, {})
        pp._VariableInitMethodProfiler(NoFuncParam, {'self':2, 's_time': 49}, 's_time',
                                       NoFuncParam.func, {})
        pp._VariableInitMethodProfiler(NoFuncParam, {'s_time': 49}, 's_time',
                                       NoFuncParam.func, {'self':0})

        pp._VariableInitMethodProfiler(InitAndParam, {'self':43, 's_time': 49}, 's_time',
                                       InitAndParam.func, {'self':3, 's_time':4})
        pp._VariableInitMethodProfiler(InitAndParam, {'s_time': 49}, 's_time',
                                       InitAndParam.func, {'self':3, "s_time":4})
        pp._VariableInitMethodProfiler(InitAndParam, {'self':43, 's_time': 49}, 's_time',
                                       InitAndParam.func, {"s_time":34})
        pp._VariableInitMethodProfiler(InitAndParam, {'s_time': 49}, 's_time',
                                       InitAndParam.func, {"s_time":34})

    def test_profile(self):
        class NoFuncParam:
            def __init__(self, s_time):
                self._s_time = s_time
            def func(self):
                time.sleep(self._s_time)
        class InitAndParam:
            def __init__(self, s_time):
                self._s_time = s_time
            def func(self, s_time):
                time.sleep(self._s_time + s_time)
        def profile_test_helper(exp_xvals, exp_runtimes, loc_class, ikwarg, var_key, mkwarg, conv_func=None):
            var_profiler = pp._VariableInitMethodProfiler(loc_class, ikwarg, var_key,
                                                          loc_class.func, mkwarg, conv_func)
            xvals, runtimes = var_profiler.profile()
            self.assertEqual(xvals, exp_xvals)
            total_stime = sum(runtimes)
            self.assertGreaterEqual(total_stime, sum(ikwarg[var_key]))

        in_list = []
        profile_test_helper(in_list, in_list, NoFuncParam, {"s_time":in_list}, "s_time", {})
        in_list = [0.04]
        profile_test_helper(in_list, in_list, NoFuncParam, {"s_time":in_list}, "s_time", {})
        in_list = [0.04]
        profile_test_helper([0.08], in_list, NoFuncParam, {"s_time":in_list}, "s_time", {}, lambda x:2*x)
        in_list = [0.04, 0.02, 0.001]
        profile_test_helper(in_list, in_list, NoFuncParam, {"s_time":in_list}, "s_time", {})

        in_list = []
        profile_test_helper(in_list, in_list, InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0})
        in_list = []
        profile_test_helper(in_list, in_list, InitAndParam, {"s_time":in_list}, "s_time", {"s_time":10})
        in_list = [0]
        profile_test_helper(in_list, in_list, InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0})
        in_list = [0.02]
        profile_test_helper(in_list, in_list, InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0})
        in_list = [0.02]
        profile_test_helper(in_list, [0.02+0.05], InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0.05})
        in_list = [0.02]
        profile_test_helper([0.02*2], [0.02+0.05], InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0.05}, conv_func=lambda x:2*x)
        in_list = [0.02, 0.001, 0.03]
        profile_test_helper(in_list, in_list, InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0})
        in_list = [0, 0.001, 0.03]
        profile_test_helper(in_list, in_list, InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0})
        in_list = [0.02, 0.001, 0.03]
        profile_test_helper(in_list, [i+0.5 for i in in_list], InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0.5})
        in_list = [0.02, 0.001, 0.03]
        profile_test_helper([i-0.002 for i in in_list], [i+0.5 for i in in_list], InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0.5}, conv_func=lambda x:x-0.002)
        in_list = (i/100 for i in range(5))
        profile_test_helper(list((i/100 for i in range(5))), list((i/100 for i in range(5))), InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0})
        in_list = (i/100 for i in range(5))
        profile_test_helper(list((i for i in range(5))), list((i/100 for i in range(5))), InitAndParam, {"s_time":in_list}, "s_time", {"s_time":0}, conv_func=lambda x:x*100)

class TestProfilePlotterClass(unittest.TestCase):
    def test__init___(self):
        # basic test
        x = profplot.ProfilePlotter("some", "thing")
        self.assertEqual(x.x_label, "some")
        self.assertEqual(x.y_label, "thing")
        # bad input
        with self.assertRaises(TypeError):
            profplot.ProfilePlotter(20, "thing")
        with self.assertRaises(TypeError):
            profplot.ProfilePlotter("thing", 20)
        with self.assertRaises(TypeError):
            profplot.ProfilePlotter(20, 20)
        with self.assertRaises(ValueError):
            x = profplot.ProfilePlotter("", "")
            x.plot()    # trying to plot with no profilers present
