from __future__ import print_function

import os
import signal
import time

from alligator.constants import ALL


class Worker(object):
    def __init__(self, gator, max_tasks=0, to_consume=ALL, nap_time=0.1):
        """
        An object for consuming the queue & running the tasks.

        Ex::

            from alligator import Gator, Worker

            gator = Gator('locmem://')
            worker = Worker(gator)
            worker.run_forever()

        :param gator: A configured ``Gator`` object
        :type gator: ``Gator`` instance

        :param max_tasks: (Optional) The maximum number of tasks to consume.
            Useful if you're concerned about memory leaks or want short-lived
            workers. Defaults to ``0`` (unlimited tasks).
        :type max_tasks: integer

        :param to_consume: (Optional) The queue name the worker should consume
            from. Defaults to ``ALL``.
        :type to_consume: string

        :param nap_time: (Optional) To prevent high CPU usage in the busy loop,
            you can specify a time delay (in seconds) between tasks. Set to
            ``0`` to disable sleep & consume as fast as possible. Defaults to
            ``0.1``
        :type nap_time: float
        """
        self.gator = gator
        self.max_tasks = int(max_tasks)
        self.to_consume = to_consume
        self.nap_time = nap_time
        self.tasks_complete = 0

    def ident(self):
        """
        Returns a string identifier for the worker.

        Used in the printed messages & includes the process ID.
        """
        return 'Alligator Worker (#{})'.format(os.getpid())

    def starting(self):
        """
        Prints a startup message to stdout.
        """
        ident = self.ident()
        print('{} starting & consuming "{}".'.format(ident, self.to_consume))

        if self.max_tasks:
            print('{} will die after {} tasks.'.format(ident, self.max_tasks))
        else:
            print('{} will never die.'.format(ident))

    def interrupt(self):
        """
        Prints an interrupt message to stdout.
        """
        ident = self.ident()
        print('{} for "{}" saw interrupt. Finishing in-progress task.'.format(
            ident,
            self.to_consume
        ))

    def stopping(self):
        """
        Prints a shutdown message to stdout.
        """
        ident = self.ident()
        print('{} for "{}" shutting down. Consumed {} tasks.'.format(
            ident,
            self.to_consume,
            self.tasks_complete
        ))

    def result(self, result):
        """
        Prints the received result from a task to stdout.

        :param result: The result of the task
        """
        print(result)

    def run_forever(self):
        """
        Causes the worker to run either forever or until the
        ``Worker.max_tasks`` are reached.
        """
        self.starting()
        self.keep_running = True

        def handle(signum, frame):
            self.interrupt()
            self.keep_running = False

        signal.signal(signal.SIGINT, handle)

        while self.keep_running:
            if self.max_tasks and self.tasks_complete >= self.max_tasks:
                self.stopping()

            if self.gator.len():
                result = self.gator.pop()
                self.tasks_complete += 1
                self.result(result)

            if self.nap_time >= 0:
                time.sleep(self.nap_time)

        return 0
