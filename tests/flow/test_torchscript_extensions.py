import math
import redis

from includes import *
from RLTest import Env

'''
python -m RLTest --test tests_torchscript_extensions.py --module path/to/redisai.so
'''


class test_torch_script_extesions:

    def __init__(self):
        self.env = Env()
        if not TEST_PT:
            self.env.debugPrint("skipping {} since TEST_PT=0".format(
                sys._getframe().f_code.co_name), force=True)
            self.env.skip()

        self.con = self.env.getConnection()
        script = load_file_content('redis_scripts.py')
        ret = self.con.execute_command(
            'AI.SCRIPTSET', 'redis_scripts{1}', DEVICE, 'SOURCE', script)
        self.env.assertEqual(ret, b'OK')
        model_tf = load_file_content('graph.pb')
        ret = self.con.execute_command('AI.MODELSTORE', 'model_tf{1}', 'TF', DEVICE, 'INPUTS', 2, 'a', 'b', 'OUTPUTS', 1,
                                       'mul', 'BLOB', model_tf)
        self.env.assertEqual(ret, b'OK')
        model_torch = load_file_content('pt-minimal.pt')
        ret = self.con.execute_command('AI.MODELSTORE', 'model_torch{1}', 'TORCH', DEVICE, 'BLOB', model_torch)
        self.env.assertEqual(ret, b'OK')
        # self.env.ensureSlaveSynced(self.con, self.env)

    def test_redis_error(self):
        try:
            self.con.execute_command(
            'AI.SCRIPTEXECUTE', 'redis_scripts', 'test_redis_error',  'KEYS', 1, "x{1}", "INPUTS", 1, "x{1}")
            self.env.assertTrue(False)
        except:
            pass
        
    def test_simple_test_set(self):
        self.con.execute_command(
            'AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_set_key', 'KEYS', 1, "x{1}", "INPUTS", 2, "x{1}", 1)
        self.env.assertEqual(b"1", self.con.get("x{1}"))

    def test_int_set_get(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_int_set_get', 'KEYS', 1, "x{1}", "INPUTS", 2, "x{1}", 1, 'OUTPUTS', 1, 'y{1}')
        y = self.con.execute_command('AI.TENSORGET', 'y{1}', 'meta' ,'VALUES')
        self.env.assertEqual(y, [b"dtype", b"INT64", b"shape", [], b"values", [1]] )

    def test_int_set_incr(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_int_set_incr', 'KEYS', 1, "x{1}", "INPUTS", 2, "x{1}", 1, 'OUTPUTS', 1, 'y{1}')
        y = self.con.execute_command('AI.TENSORGET', 'y{1}', 'meta' ,'VALUES')
        self.env.assertEqual(y, [b"dtype", b"INT64", b"shape", [], b"values", [2]] )

    def test_float_get_set(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_float_set_get', 'KEYS', 1, "x{1}", "INPUTS", 2, "x{1}", 1.1, 'OUTPUTS', 1, 'y{1}')
        y = self.con.execute_command('AI.TENSORGET', 'y{1}', 'meta' ,'VALUES')
        self.env.assertEqual(y[0], b"dtype")
        self.env.assertEqual(y[1], b"FLOAT")
        self.env.assertEqual(y[2], b"shape")
        self.env.assertEqual(y[3], [])
        self.env.assertEqual(y[4], b"values")
        self.env.assertAlmostEqual(float(y[5][0]), 1.1, 0.1)

    def test_int_list(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_int_list', 'KEYS', 1, "int_list{1}", 'INPUTS', 1, "int_list{1}", "LIST_INPUTS", 2, "1", "2", 'OUTPUTS', 1, 'y{1}')
        y = self.con.execute_command('AI.TENSORGET', 'y{1}', 'meta' ,'VALUES')
        self.env.assertEqual(y, [b"dtype", b"INT64", b"shape", [2, 1], b"values", [1, 2]] )

    def test_str_list(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_str_list', 'KEYS', 1, "str_list{1}", 'INPUTS', 1, "str_list{1}", "LIST_INPUTS", 2, "1", "2")
        res = self.con.execute_command("LRANGE", "str_list{1}", "0", "2")
        self.env.assertEqual(res, [b"1", b"2"] )

    def test_hash(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_hash', 'KEYS', 1, "hash{1}", 'INPUTS', 1, "hash{1}", "LIST_INPUTS", 4, "field1", 1, "field2", 2, 'OUTPUTS', 1, 'y{1}')
        y = self.con.execute_command('AI.TENSORGET', 'y{1}', 'meta' ,'VALUES')
        self.env.assertEqual(y, [b"dtype", b"INT64", b"shape", [2, 1], b"values", [1, 2]])

    def test_execute_model_via_script(self):
        self.con.execute_command('AI.SCRIPTEXECUTE', 'redis_scripts{1}', 'test_model_execute', 'KEYS', 1, "model_torch{1}",
                                 'LIST_INPUTS', 1, 'model_torch{1}', 'OUTPUTS', 1, 'y{1}')
        y = self.con.execute_command('AI.TENSORGET', 'y{1}', 'meta', 'VALUES')
        self.env.assertEqual(y, [b"dtype", b"FLOAT", b"shape", [2, 2], b"values", [b'4', b'6', b'4', b'6']])
