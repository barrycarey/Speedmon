import json
import logging
import os
import subprocess
from typing import Dict, List, NoReturn

from speedmon.common.exceptions import SpeedtestRunError
from speedmon.common.speed_test_results import SpeedTestResult
from speedmon.storage.storage_handler_base import StorageHandlerBase

log = logging.getLogger(__name__)


def convert_results(results: Dict):
    return SpeedTestResult(
        results['ping']['jitter'] if 'jitter' in results['ping'] else None,
        results['ping']['latency'],
        results['download']['bandwidth'],
        results['upload']['bandwidth'],
        results['server']['id'],
        results['server']['name'],
        results['server']['country'],
        results['server']['location'])


def accept_speedtest_license() -> NoReturn:
    if os_name() == 'nt':
        executable = os.path.join(os.getcwd(), 'bin', 'speedtest.exe')
    else:
        executable = 'speedtest'
    subprocess.run([executable, '--accept-license'],  stdout=subprocess.PIPE, encoding='UTF-8')


def build_speedtest_command_line(server: str = None) -> List:
    if os_name() == 'nt':
        command = os.path.join(os.getcwd(), 'bin', 'speedtest.exe')
    else:
        command = 'speedtest'
    proc_args = [command, '-f', 'json']
    if server:
        proc_args += ['-s', server]
    return proc_args


def run_speedtest_with_default_server(storage_handlers: List[StorageHandlerBase]) -> NoReturn:
    try:
        results = run_speed_test()
    except SpeedtestRunError as e:
        log.error('Problem running speed test: %s', e)
        return
    save_results(storage_handlers, results)
    return


def run_speedtest_with_servers(storage_handlers: List[StorageHandlerBase], servers: List[str]) -> NoReturn:
    for server in servers:
        try:
            results = run_speed_test(server=server)
        except SpeedtestRunError as e:
            log.error('Problem running speed test: %s', e)
            return
        save_results(storage_handlers, results)
    return


def run_speed_test(server: str = None) -> SpeedTestResult:
    """
    Performs the speed test with the provided server
    :param server: Server to test against
    """

    proc_args = build_speedtest_command_line(server)
    log.debug('Running with args: %s', ' '.join(proc_args))
    process_result = subprocess.run(proc_args, stdout=subprocess.PIPE, encoding='UTF-8')
    if process_result.stderr:
        error_data = json.loads(process_result.stderr)
        log.error('Failed to run speedtest: %s', error_data['message'])
        raise SpeedtestRunError(f'Failed to run speed test.  Message: {error_data["message"]}')

    results = json.loads(process_result.stdout)

    if 'error' in results:
        log.error('Problem running test: %s', results['error'])
        raise SpeedtestRunError(f'Failed to run speed test.  Message: {results["error"]}')

    return convert_results(results)


def os_name() -> str:
    """
    Wrapper around os.name to facilitate easier testing
    :rtype: str
    """
    return os.name


def save_results(storage_handlers: List[StorageHandlerBase], result: SpeedTestResult) -> None:
    for handler in storage_handlers:
        if handler.active:
            handler.save_results(result)


def format_influxdb_results(data: SpeedTestResult) -> List[Dict]:
    return [
        {
            'measurement': 'speed_test_results',
            'fields': {
                'download': data.download,
                'upload': data.upload,
                'ping': data.latency,
                'jitter': data.jitter,
                'packetloss': data.packetloss,
            },
            'tags': {
                'server_id': data.server_id,
                'server_name': data.server_name,
                'server_country': data.server_country,
                'server_location': data.server_location
            }
        }
    ]
