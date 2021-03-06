from __future__ import absolute_import

try:
    from six.moves import cPickle as pickle
except:
    import pickle
from tblib import pickling_support
import logging
import botocore
import glob2
import random
import os
pickling_support.install()

from pywren.executor import Executor
import pywren.wrenconfig as wrenconfig
import pywren.invokers as invokers
from pywren.wait import wait
from pywren.wait import *

logger = logging.getLogger(__name__)


def default_executor(**kwargs):
    executor_str = 'lambda'
    if 'PYWREN_EXECUTOR' in os.environ:
        executor_str = os.environ['PYWREN_EXECUTOR']

    if executor_str == 'lambda':
        return lambda_executor(**kwargs)
    elif executor_str == 'remote' or executor_str=='standalone':
        return remote_executor(**kwargs)
    elif executor_str == 'dummy':
        return dummy_executor(**kwargs)
    return lambda_executor(**kwargs)


def lambda_executor(config=None, job_max_runtime=280):
    if config is None:
        config = wrenconfig.default()

    AWS_REGION = config['account']['aws_region']
    FUNCTION_NAME = config['lambda']['function_name']
    S3_BUCKET = config['s3']['bucket']
    S3_PREFIX = config['s3']['pywren_prefix']
    RUNTIME_S3_BUCKET = config['runtime']['s3_bucket']
    RUNTIME_S3_KEY = config['runtime']['s3_key']
    ENDPOINT_URL = config['account']['endpoint_url']

    invoker = invokers.LambdaInvoker(AWS_REGION, FUNCTION_NAME)
    return Executor(AWS_REGION, S3_BUCKET, S3_PREFIX, invoker, 
                    RUNTIME_S3_BUCKET, RUNTIME_S3_KEY, job_max_runtime, ENDPOINT_URL)


def dummy_executor(config=None, job_max_runtime=100):
    if config is None:
        config = wrenconfig.default()

    AWS_REGION = config['account']['aws_region']
    S3_BUCKET = config['s3']['bucket']
    S3_PREFIX = config['s3']['pywren_prefix']
    RUNTIME_S3_BUCKET = config['runtime']['s3_bucket']
    RUNTIME_S3_KEY = config['runtime']['s3_key']
    invoker = invokers.DummyInvoker()
    return Executor(AWS_REGION, S3_BUCKET, S3_PREFIX, invoker,
                    RUNTIME_S3_BUCKET, RUNTIME_S3_KEY, job_max_runtime)


def remote_executor(config=None, job_max_runtime=3600):
    if config is None:
        config = wrenconfig.default()

    AWS_REGION = config['account']['aws_region']
    SQS_QUEUE = config['standalone']['sqs_queue_name']
    S3_BUCKET = config['s3']['bucket']
    S3_PREFIX = config['s3']['pywren_prefix']
    RUNTIME_S3_BUCKET = config['runtime']['s3_bucket']
    RUNTIME_S3_KEY = config['runtime']['s3_key']
    invoker = invokers.SQSInvoker(AWS_REGION, SQS_QUEUE)
    return Executor(AWS_REGION, S3_BUCKET, S3_PREFIX, invoker,
                    RUNTIME_S3_BUCKET, RUNTIME_S3_KEY, job_max_runtime)

standalone_executor = remote_executor


def get_all_results(fs):
    """
    Take in a list of futures and block until they are repeated, 
    call result on each one individually, and return those
    results. 
    
    Will throw an exception if any future threw an exception
    """
    wait(fs, return_when=ALL_COMPLETED)
    return [f.result() for f in fs]
