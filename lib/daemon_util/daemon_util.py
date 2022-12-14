#!/usr/bin/env python

import logging
import os
import signal
import sys
import time

import daemon
import daemon.pidfile

logger = logging.getLogger(__name__)


class SingleDaemon:

    def __init__(self, pid_dir: str, pid_file: str) -> None:
        self.pid_dir = pid_dir
        self.pid_file = pid_file
        self.pid_path = os.path.join(pid_dir, pid_file)
        self.preserved_handlers = []


    def add_presereved_handlers(self, handler):
        """
        with contextを抜けたときにloggingのハンドラが閉じられてしまうのを防止する

        file_handler = logging.FileHandler(log_path, 'a+')
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

        このようにして作成したハンドラが閉じられないようにする
        d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
        d.add_presereved_handlers(file_handler)  # ファイルハンドラを閉じないように指定
        d.start_daemon(run_schedule, run_func())

        Args:
            handler (_type_): _description_
        """
        self.preserved_handlers.append(handler.stream.fileno())


    def start_daemon(self, func: callable, *args, **kwargs):

        pidfile = daemon.pidfile.PIDLockFile(self.pid_path)
        if pidfile.is_locked():
            logger.info('already running')
            return

        # デーモンコンテキストを作成
        context = daemon.DaemonContext(
            # stdout=sys.stdout,
            # stderr=sys.stderr,
            files_preserve = self.preserved_handlers,
            umask=0o002,
            working_directory=self.pid_dir,  # 注意：pidファイルの作成場所に移動必要
            pidfile=pidfile)

        context.signal_map = {
            signal.SIGTERM: 'terminate',  # kill -TERM で停止
            signal.SIGHUP: 'terminate',  # kill -HUP で停止
        }

        with context:
            func(*args, **kwargs)

    def stop_daemon(self):
        print('stop_daemon')

        pidfile = daemon.pidfile.PIDLockFile(self.pid_path)

        pid = pidfile.read_pid()

        print(pid)

        if pid:
            os.kill(pid, signal.SIGTERM)

    def clear(self):
        if os.path.exists(self.pid_path):
            os.remove(self.pid_path)


if __name__ == '__main__':

    import argparse

    import schedule

    logging.basicConfig(level=logging.INFO)

    def dummy(*args, **kwargs):
        print(args)
        print(kwargs)
        print('done')

    def run_schedule(*args, **kwargs):
        # schedule.every(1).minutes.do(dummy, args, kwargs)  # 毎分実行
        # schedule.every(1).hours.do(dummy)                  # 毎時実行
        # schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
        # schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
        # schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except SystemExit:
                break
            except Exception as e:
                logger.info(e)

    def main():
        parser = argparse.ArgumentParser(
            description='test script to run daemon')
        parser.add_argument('-d',
                            '--daemon',
                            action='store_true',
                            default=False,
                            help='Daemon')
        parser.add_argument('-k',
                            '--kill',
                            action='store_true',
                            default=False,
                            help='Kill')
        parser.add_argument('-c',
                            '--clear',
                            action='store_true',
                            default=False,
                            help='Clear junk pid file')

        args = parser.parse_args()

        pid_dir = os.path.dirname(__file__)
        pid_file = __file__ + '.pid'

        d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)

        if args.clear:
            d.clear()
            return 0

        if args.daemon:
            d.start_daemon(run_schedule,
                           'arg1',
                           'arg2',
                           kwarg1='kwarg1',
                           kwarg2='kwarg2')
            return 0

        if args.kill:
            d.stop_daemon()
            return 0

        return 0

    sys.exit(main())
