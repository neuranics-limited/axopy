"""
Step timing example
=============

Example of using a step timing counter.
"""
import time
from axopy.experiment import Experiment
from axopy.task import Task
from axopy.timing import StepCounter
from axopy.gui.canvas import Canvas, Text


class DebugPrinter(object):
    def __init__(self):
        self.last_read_time = None
        self.start_time = None

    def print(self, stage):
        t = time.time()
        if self.last_read_time is None:
            pass
        else:
            now = (t - self.start_time)
            ms = (t - self.last_read_time)
            pstr = 'time: {:.4f} inc: {:.4f} @ {}'.format(now, ms, stage)
            print(pstr)
        self.last_read_time = t

    def start(self):
        t = time.time()
        self.last_read_time = t
        self.start_time = t

    def reset(self):
        self.last_read_time = None
        self.start_time = None


class TimingTask(Task):

    def __init__(self):
        super(TimingTask, self).__init__()
        self.prepare_timer()
        self.debug = DebugPrinter()

    def prepare_daq(self, daq):
        self.daq = daq
        self.daq.start()

    def prepare_design(self, design):
        block = design.add_block()
        for i in range(10):
            block.add_trial()

    def prepare_timer(self):
        trial_length = int(TRIAL_LENGTH / READ_LENGTH)
        start_stage1 = int(TRIAL_STAGE1 / READ_LENGTH)
        start_stage2 = int(TRIAL_STAGE2 / READ_LENGTH)
        start_stage3 = int(TRIAL_STAGE3 / READ_LENGTH)

        self.timer = StepCounter(trial_length, reset_on_timeout=True)
        self.timer.timeout.connect(self.trial_end)

        """ Add calls to different trial stages. """
        self.timer.add_step(start_stage1, self.trial_stage1)
        self.timer.add_step(start_stage2, self.trial_stage2)
        self.timer.add_step(start_stage3, self.trial_stage3)

    def prepare_graphics(self, container):
        canvas = Canvas()
        container.set_widget(canvas)

        self.text0 = Text('')
        self.text0.pos = -0.15, 0
        canvas.add_item(self.text0)

    def update(self, data):
        self.timer.increment()

        """ Default updates for each step go here.
            Main change is trial stage specific
            updates are then called from here, rather than
            connecting the daq to a different update function."""
        if (self.trial_stage == 1):
            pass
        elif (self.trial_stage == 2):
            pass
        elif (self.trial_stage == 3):
            pass

    def run_trial(self, trial):
        self.text0.qitem.setText('Stage 0')

        self.trial_stage = 0
        self.connect(self.daq.updated, self.update)

        self.debug.start()
        self.debug.print('Trial start')

    def trial_stage1(self):
        self.text0.qitem.setText('Stage 1')

        self.trial_stage += 1
        self.debug.print('Trial stage 1')

    def trial_stage2(self):
        self.text0.qitem.setText('Stage 2')

        self.trial_stage += 1
        self.debug.print('Trial stage 2')

    def trial_stage3(self):
        self.text0.qitem.setText('Stage 3')

        self.trial_stage += 1
        self.debug.print('Trial stage 3')

    def trial_end(self):
        self.debug.print('Trial end')

        self.disconnect(self.daq.updated, self.update)
        self.next_trial()

    def finish(self):
        self.daq.stop()
        self.finished.emit()


if __name__ == '__main__':
    from axopy.daq import NoiseGenerator

    S_RATE = 100
    READ_LENGTH = 0.1

    TRIAL_LENGTH = 5.
    TRIAL_STAGE1 = 1.
    TRIAL_STAGE2 = 1.5
    TRIAL_STAGE3 = 4.

    dev = NoiseGenerator(rate=S_RATE, num_channels=1, amplitude=1.0,
                         read_size=int(S_RATE * READ_LENGTH))

    exp = Experiment(daq=dev, subject='test', allow_overwrite=True)
    exp.run(TimingTask())
