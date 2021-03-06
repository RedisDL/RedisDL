from includes import *

'''
python -m RLTest --test tests_dag_basic.py --module path/to/redisai.so
'''


def test_dag_load(env):
    con = get_connection(env, '{1}')
    ret = con.execute_command(
        "AI.TENSORSET persisted_tensor_1{1} FLOAT 1 2 VALUES 5 10")
    env.assertEqual(ret, b'OK')
    command = "AI.DAGEXECUTE LOAD 1 persisted_tensor_1{1}" \
              " |> AI.TENSORGET persisted_tensor_1{1} VALUES"
    ret = con.execute_command(command)
    env.assertEqual(ret[0], [b'5', b'10'])


def test_dag_local_tensorset(env):
    con = get_connection(env, '{1}')

    command = "AI.DAGEXECUTE ROUTING {1} |> " \
              "AI.TENSORSET volatile_tensor1 FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORSET volatile_tensor2 FLOAT 1 2 VALUES 5 10 "

    ret = con.execute_command(command)
    env.assertEqual(ret, [b'OK',b'OK'])

    # assert that transaction tensor does not exist
    ret = con.execute_command("EXISTS volatile_tensor")
    env.assertEqual(ret, 0)


def test_dagro_local_tensorset(env):
    con = get_connection(env, '{1}')

    command = "AI.DAGEXECUTE_RO ROUTING {1} |> " \
              "AI.TENSORSET volatile_tensor1 FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORSET volatile_tensor2 FLOAT 1 2 VALUES 5 10 "

    ret = con.execute_command(command)
    env.assertEqual(ret, [b'OK',b'OK'])

    # assert that volatile_tensor does not exist
    ret = con.execute_command("EXISTS volatile_tensor")
    env.assertEqual(ret, 0 )


def test_dag_local_tensorset_persist(env):
    con = get_connection(env, '{1}')

    command = "AI.DAGEXECUTE " \
              "PERSIST 1 tensor1{1} |> " \
              "AI.TENSORSET tensor1{1} FLOAT 1 2 VALUES 5 10"

    ret = con.execute_command(command)
    env.assertEqual(ret, [b'OK'])

    # assert that PERSIST succeeded.
    ret = con.execute_command("EXISTS tensor1{1}")
    env.assertEqual(ret, 1 )

    ret = con.execute_command("AI.TENSORGET tensor1{1} META VALUES")
    env.assertEqual(ret, [b'dtype', b'FLOAT', b'shape', [1, 2], b'values', [b'5', b'10']])


def test_dag_multilocal_tensorset_persist(env):
    con = get_connection(env, '{1}')

    command = "AI.DAGEXECUTE " \
              "PERSIST 1 tensor3:{1} |> " \
              "AI.TENSORSET tensor1{1} FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORSET tensor2 FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORSET tensor3:{1} FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORSET tensor4:{1} FLOAT 1 2 VALUES 5 10 "

    ret = con.execute_command(command)
    env.assertEqual([b'OK',b'OK',b'OK',b'OK'],ret)

    # assert that PERSIST succeeded.
    ret = con.execute_command("EXISTS tensor1{1}")
    env.assertEqual(ret, 0 )

    # assert that PERSIST succeeded.
    ret = con.execute_command("EXISTS tensor2")
    env.assertEqual(ret, 0 )

    # assert that PERSIST succeeded.
    ret = con.execute_command("EXISTS tensor3:{1}")
    env.assertEqual(ret, 1 )

    # assert that PERSIST succeeded.
    ret = con.execute_command("EXISTS tensor4:{1}")
    env.assertEqual(ret, 0 )

    ret = con.execute_command("AI.TENSORGET tensor3:{1} META VALUES")
    env.assertEqual(ret, [b'dtype', b'FLOAT', b'shape', [1, 2], b'values', [b'5', b'10']])


def test_dag_local_tensorset_tensorget_persist(env):
    con = get_connection(env, '{1}')

    command = "AI.DAGEXECUTE PERSIST 1 tensor1{1} |> " \
              "AI.TENSORSET tensor1{1} FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORGET tensor1{1} VALUES"

    ret = con.execute_command(command)
    env.assertEqual(ret, [b'OK', [b'5', b'10']])

    ret = con.execute_command("AI.TENSORGET tensor1{1} VALUES")
    env.assertEqual(ret, [b'5', b'10'])


def test_dag_local_multiple_tensorset_on_same_tensor(env):
    con = get_connection(env, '{1}')

    command = "AI.DAGEXECUTE PERSIST 1 tensor1{1} |> " \
              "AI.TENSORSET tensor1{1} FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORGET tensor1{1} META VALUES |> " \
              "AI.TENSORSET tensor1{1} FLOAT 1 4 VALUES 20 40 60 80 |> " \
              "AI.TENSORGET tensor1{1} META VALUES"

    ret = con.execute_command(command)
    env.assertEqual([
        b'OK',
        [b'dtype', b'FLOAT', b'shape', [1, 2], b'values', [b'5', b'10']],
        b'OK',
        [b'dtype', b'FLOAT', b'shape', [1, 4], b'values', [b'20', b'40', b'60', b'80']]
    ], ret)

    ret = con.execute_command("AI.TENSORGET tensor1{1} META VALUES")
    env.assertEqual([b'dtype', b'FLOAT', b'shape', [1, 4], b'values', [b'20', b'40',b'60',b'80']],ret)


def test_dag_load_persist_tensorset_tensorget(env):
    con = get_connection(env, '{1}')

    ret = con.execute_command(
        "AI.TENSORSET persisted_tensor_1{1} FLOAT 1 2 VALUES 5 10")
    env.assertEqual(ret, b'OK')

    ret = con.execute_command(
        "AI.TENSORSET persisted_tensor_2:{1} FLOAT 1 3 VALUES 0 0 0")
    env.assertEqual(ret, b'OK')

    command = "AI.DAGEXECUTE LOAD 2 persisted_tensor_1{1} persisted_tensor_2:{1}" \
              " PERSIST 1 volatile_tensor_persisted{1} |> " \
              "AI.TENSORSET volatile_tensor_persisted{1} FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORGET persisted_tensor_1{1} META VALUES |> " \
              "AI.TENSORGET persisted_tensor_2:{1} META VALUES "

    ret = con.execute_command(command)
    env.assertEqual(ret, [b'OK', [b'dtype', b'FLOAT', b'shape', [1, 2], b'values', [b'5', b'10']], [
        b'dtype', b'FLOAT', b'shape', [1, 3], b'values', [b'0', b'0', b'0']]])

    ret = con.execute_command("AI.TENSORGET volatile_tensor_persisted{1} META VALUES")
    env.assertEqual(ret, [b'dtype', b'FLOAT', b'shape', [1, 2], b'values', [b'5', b'10']])


def test_dag_keyspace_tensorget(env):
    con = get_connection(env, '{1}')

    ret = con.execute_command(
        "AI.TENSORSET persisted_tensor{1} FLOAT 1 2 VALUES 5 10")
    env.assertEqual(ret, b'OK')

    command = "AI.DAGEXECUTE LOAD 1 persisted_tensor{1} " \
              "|> AI.TENSORGET persisted_tensor{1} VALUES"

    ret = con.execute_command(command)
    env.assertEqual(ret, [[b'5', b'10']])


def test_dag_ro_keyspace_tensorget(env):
    con = get_connection(env, '{1}')

    ret = con.execute_command(
        "AI.TENSORSET persisted_tensor{1} FLOAT 1 2 VALUES 5 10")
    env.assertEqual(ret, b'OK')

    command = "AI.DAGEXECUTE_RO LOAD 1 persisted_tensor{1} |> " \
              "AI.TENSORGET persisted_tensor{1} VALUES"

    ret = con.execute_command(command)
    env.assertEqual(ret, [[b'5', b'10']])


def test_dag_keyspace_and_localcontext_tensorget(env):
    con = get_connection(env, '{1}')

    ret = con.execute_command(
        "AI.TENSORSET persisted_tensor{1} FLOAT 1 2 VALUES 5 10")
    env.assertEqual(ret, b'OK')

    command = "AI.DAGEXECUTE LOAD 1 persisted_tensor{1} |> " \
              "AI.TENSORSET volatile_tensor FLOAT 1 2 VALUES 5 10 |> " \
              "AI.TENSORGET persisted_tensor{1} VALUES |> " \
              "AI.TENSORGET volatile_tensor VALUES"

    ret = con.execute_command(command)
    env.assertEqual(ret, [b'OK', [b'5', b'10'], [b'5', b'10']])


def test_dag_with_timeout(env):
    if not TEST_TF:
        return
    con = get_connection(env, '{1}')
    batch_size = 2
    minbatch_size = 2
    timeout = 1
    model_name = 'model{1}'
    model_pb, input_var, output_var, labels, img = load_mobilenet_v2_test_data()

    con.execute_command('AI.MODELSTORE', model_name, 'TF', DEVICE,
                        'BATCHSIZE', batch_size, 'MINBATCHSIZE', minbatch_size,
                        'INPUTS', 1, input_var,
                        'OUTPUTS', 1, output_var,
                        'BLOB', model_pb)
    con.execute_command('AI.TENSORSET', 'input{1}',
                        'FLOAT', 1, img.shape[1], img.shape[0], img.shape[2],
                        'BLOB', img.tobytes())

    res = con.execute_command('AI.DAGEXECUTE',
                              'LOAD', '1', 'input{1}',
                              'TIMEOUT', timeout, '|>',
                              'AI.MODELEXECUTE', model_name,
                              'INPUTS', 1, 'input{1}', 'OUTPUTS', 1, 'output{1}',
                              '|>', 'AI.MODELEXECUTE', model_name,
                              'INPUTS', 1, 'input{1}', 'OUTPUTS', 1, 'output{1}')

    env.assertEqual(b'TIMEDOUT', res)


def test_dag_with_error(env):
    if not TEST_TF:
        return

    con = get_connection(env, '{1}')
    tf_model = load_file_content('graph.pb')
    ret = con.execute_command('AI.MODELSTORE', 'tf_model{1}', 'TF', DEVICE,
                        'INPUTS', 2, 'a', 'b',
                        'OUTPUTS', 1, 'mul',
                        'BLOB', tf_model)
    env.assertEqual(b'OK', ret)

    # Run the model from DAG context, where MODELEXECUTE op fails due to dim mismatch in one of the tensors inputs:
    # the input tensor 'b' is considered as tensor with dim 2X2X3 initialized with zeros, while the model expects that
    # both inputs to node 'mul' will be with dim 2.
    ret = con.execute_command('AI.DAGEXECUTE_RO', 'ROUTING', '{1}',
                              '|>', 'AI.TENSORSET', 'a', 'FLOAT', 2, 'VALUES', 2, 3,
                              '|>', 'AI.TENSORSET', 'b', 'FLOAT', 2, 2, 3,
                              '|>', 'AI.MODELEXECUTE', 'tf_model{1}', 'INPUTS', 2, 'a', 'b', 'OUTPUTS', 1, 'tD',
                              '|>', 'AI.TENSORGET', 'tD', 'VALUES')

    # Expect that the MODELEXECUTE op will raise an error, and the last TENSORGET op will not be executed
    env.assertEqual(ret[0], b'OK')
    env.assertEqual(ret[1], b'OK')
    env.assertEqual(ret[3], b'NA')
    env.assertEqual(type(ret[2]), redis.exceptions.ResponseError)
    env.assertTrue(str(ret[2]).find('Incompatible shapes: [2] vs. [2,2,3] \t [[{{node mul}}]]') >= 0)
