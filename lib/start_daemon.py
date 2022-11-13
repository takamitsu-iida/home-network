#!/usr/bin/env python

import logging
import os
import signal
import sys
import time

import daemon
import daemon.pidfile
import schedule

logger = logging.getLogger(__name__)

app_dir = os.path.dirname(__file__)
pid_path = os.path.join(app_dir, __file__ + '.pid')

def dummy():
    print('done')

def stop_daemon():
    print('stop_daemon')

    pidfile = daemon.pidfile.PIDLockFile(pid_path)

    pid = pidfile.read_pid()

    print(pid)

    if pid:
        os.kill(pid, signal.SIGTERM)


def clear():
    if os.path.exists(pid_path):
        os.remove(pid_path)


def start_daemon():

    # 毎時update_db()を実行する
    schedule.every(1).minute.do(dummy)

    pidfile = daemon.pidfile.PIDLockFile(pid_path)
    if pidfile.is_locked():
        logger.info('already running')
        return


    # デーモンコンテキストを作成
    context = daemon.DaemonContext(
        stdout=sys.stdout,
        stderr=sys.stderr,
        umask=0o002,
        working_directory=app_dir,  # 注意：pidファイルの作成場所に移動必要
        pidfile=pidfile
    )

    context.signal_map = {
        signal.SIGTERM: 'terminate', # kill -TERM で停止
        signal.SIGHUP: 'terminate',  # kill -HUP で停止
    }

    with context:
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except SystemExit:
                break
            except Exception as e:
                logger.info(e)


if __name__ == '__main__':

    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='test script to run daemon')
    parser.add_argument('-d', '--daemon', action='store_true', default=False, help='Daemon')
    parser.add_argument('-k', '--kill', action='store_true', default=False, help='Kill')
    parser.add_argument('-c', '--clear', action='store_true', default=False, help='Clear junk pid file')


    args = parser.parse_args()

    def main():

        if args.clear:
            clear()
            return 0

        if args.daemon:
            start_daemon()
            return 0

        if args.kill:
            stop_daemon()
            return 0

        return 0

    sys.exit(main())
