"""Protocol and threaded interface for data acquisition."""

import time
import numpy
from PyQt5 import QtCore
from axopy.messaging import Transmitter
from axopy.gui.main import get_qtapp, qt_key_map
from axopy.pipeline import Filter


class DaqStream(QtCore.QThread):
    """Asynchronous interface to an input device.

    Runs a persistent while loop wherein the device is repeatedly polled for
    data. When the data becomes available, it is emitted and the loop
    continues.

    There are effectively two methods of this class: start and stop. These
    methods do as their names suggest -- they start and stop the underlying
    device from sampling new data.

    The device used to create the DaqStream is also accessible via the
    ``device`` attribute so you can change settings on the underlying device
    any time (e.g. sampling rate, number of samples per update, etc.).

    Parameters
    ----------
    device : daq
        Any object implementing the AxoPy data acquisition interface. See
        :class:`NoiseGenerator` for an example.

    Attributes
    ----------
    updated : Transmitter
        Transmitted when the latest chunk of data is available. The data type
        depends on the underlying input device, but it is often a numpy
        ndarray.
    disconnected : Transmitter
        Transmitted if the device cannot be read from (it has disconnected
        somehow).
    finished : Transmitter
        Transmitted when the device has stopped and samping is finished.
    """

    updated = Transmitter(object)
    disconnected = Transmitter()
    finished = Transmitter()

    def __init__(self, device):
        super(DaqStream, self).__init__()
        self.device = device

        self._running = False

    @property
    def running(self):
        """Boolean value indicating whether or not the stream is running."""
        return self._running
    
    def get_device_details(self):
        """Attempts to retrieve data about the connected Neuranics device, returns default device properties if """
        # this was made into its own function rather than something the task 
        #   can access through self.device to add error handling if the attribute 
        #   does not exist in specific DAQ implementaions
        try:
            deviceDetails = self.device.DEVICE_DETAILS
        except:
            deviceDetails = NeuranicsDevice() #ensures that there is no error if the attribute is missing from DAQ implementation
            
        return deviceDetails

    def get_sample_properties(self):
        """ Allow the task structure access to device specific properties"""
        return self.device.get_sample_properties()
    
    def get_channels(self):
        return self.device.CHANNELS

    def start(self):
        """Start the device and begin reading from it."""
        super(DaqStream, self).start()

    def run(self):
        """Implementation for the underlying QThread.

        Don't call this method directly -- use :meth:`start` instead.
        """
        self._running = True

        self.device.start()

        while True:
            if not self._running:
                break

            try:
                d = self.device.read()
            except IOError:
                self.disconnected.emit()
                return

            if self._running:
                self.updated.emit(d)

        self.device.stop()
        self.finished.emit()

    def stop(self, wait=True):
        """Stop the stream.

        Parameters
        ----------
        wait : bool, optional
            Whether or not to wait for the underlying device to stop before
            returning.
        """
        self._running = False
        if wait:
            self.wait()


class NoiseGenerator(object):
    """An emulated data acquisition device which generates random data.

    Each sample of the generated data is sampled from a zero-mean Gaussian
    distribution with variance determined by the amplitude specified, which
    corresponds to three standard deviations. That is, approximately 99.7% of
    the samples should be within the desired peak amplitude.

    :class:`NoiseGenerator` is meant to emulate data acquisition devices that
    block on each request for data until the data is available. See
    :meth:`read` for details.

    Parameters
    ----------
    rate : int, optional
        Sample rate in Hz. Default is 1000.
    num_channels : int, optional
        Number of "channels" to generate. Default is 1.
    amplitude : float, optional
        Approximate peak amplitude of the signal to generate. Specifically, the
        amplitude represents three standard deviations for generating the
        Gaussian distributed data. Default is 1.
    read_size : int, optional
        Number of samples to generate per :meth:`read()` call. Default is 100.
    """

    def __init__(self, rate=1000, num_channels=1, amplitude=1.0,
                 read_size=100):
        self.rate = rate
        self.num_channels = num_channels
        self.amplitude = amplitude
        self.read_size = read_size

        self._sigma = amplitude / 3

        self.sleeper = _Sleeper(float(self.read_size/self.rate))

    def start(self):
        """Does nothing for this device. Implemented to follow device API."""
        pass

    def read(self):
        """
        Generates zero-mean Gaussian data.

        This method blocks (calls ``time.sleep()``) to emulate other data
        acquisition units which wait for the requested number of samples to be
        read. The amount of time to block is calculated such that consecutive
        calls will always return with constant frequency, assuming the calls
        occur faster than required (i.e. processing doesn't fall behind).

        Returns
        -------
        data : ndarray, shape (num_channels, read_size)
            The generated data.
        """
        self.sleeper.sleep()
        data = self._sigma * numpy.random.randn(self.num_channels,
                                                self.read_size)
        return data

    def stop(self):
        """Does nothing for this device. Implemented to follow device API."""
        pass

    def reset(self):
        """Reset the device back to its initialized state."""
        self.sleeper.reset()


class RandomWalkGenerator(object):
    """An emulated data acquisition device which generates data using a random
    walk.

    Each sample of the generated data is sampled from a zero-mean Gaussian
    distribution with variance determined by the amplitude specified, which
    corresponds to three standard deviations. That is, approximately 99.7% of
    the samples should be within the desired peak amplitude.

    :class:`RandomWalkGenerator` is meant to emulate data acquisition devices
    that block on each request for data until the data is available. See
    :meth:`read` for details.

    Parameters
    ----------
    rate : int, optional
        Sample rate in Hz. Default is 1000.
    num_channels : int, optional
        Number of "channels" to generate. Default is 1.
    amplitude : float or array-like, optional
        Standard deviation of random step. Default is 1.
    start : float or array-like, optional
        Starting point. Default is 0.
    read_size : int, optional
        Number of samples to generate per :meth:`read()` call. Default is 100.
    """

    def __init__(self, rate=1000, num_channels=1, amplitude=1.0, start_pos=0.,
                 read_size=100):
        self.rate = rate
        self.num_channels = num_channels
        self.amplitude = amplitude
        self.start_pos = start_pos
        self.read_size = read_size

        self.previous_ = self.start_pos

        self.sleeper = _Sleeper(float(self.read_size/self.rate))

    def start(self):
        """Does nothing for this device. Implemented to follow device API."""
        pass

    def read(self):
        """
        Generates zero-mean Gaussian data.

        This method blocks (calls ``time.sleep()``) to emulate other data
        acquisition units which wait for the requested number of samples to be
        read. The amount of time to block is calculated such that consecutive
        calls will always return with constant frequency, assuming the calls
        occur faster than required (i.e. processing doesn't fall behind).

        Returns
        -------
        data : ndarray, shape (num_channels, read_size)
            The generated data.
        """
        self.sleeper.sleep()
        steps = numpy.random.normal(
            loc=0.0,
            scale=self.amplitude,
            size=(self.num_channels,self.read_size))
        data = self.previous_ + numpy.cumsum(steps, axis=1)
        self.previous_ = data
        return data

    def stop(self):
        """Does nothing for this device. Implemented to follow device API."""
        pass

    def reset(self):
        """Reset the device back to its initialized state."""
        self.sleeper.reset()
        self.previous_ = self.start_pos


class DumbDaq(object):
    """An emulated data acquisition device that doesn't generate any data.

    :class:`DumbGenerator` is meant to emulate data acquisition devices that
    block on each request for data until the data is available. See
    :meth:`read` for details.

    Parameters
    ----------
    rate : int, optional
        Sample rate in Hz. Default is 1000.
    read_size : int, optional
        Number of samples to generate per :meth:`read()` call. Default is 100.
    """

    def __init__(self, rate=1000, read_size=100):
        self.rate = rate
        self.read_size = read_size

        self.sleeper = _Sleeper(float(self.read_size/self.rate))

    def start(self):
        """Does nothing for this device. Implemented to follow device API."""
        pass

    def read(self):
        """
        Blocks execution.

        This method blocks (calls ``time.sleep()``) to emulate other data
        acquisition units which wait for the requested number of samples to be
        read. The amount of time to block is calculated such that consecutive
        calls will always return with constant frequency, assuming the calls
        occur faster than required (i.e. processing doesn't fall behind).
        """
        self.sleeper.sleep()
        return None

    def stop(self):
        """Does nothing for this device. Implemented to follow device API."""
        pass

    def reset(self):
        """Reset the device back to its initialized state."""
        self.sleeper.reset()


class Keyboard(QtCore.QObject):
    """Keyboard input device.

    The keyboard device works by periodically sampling (with the rate
    specified) whether or not the watched keys have been pressed since the last
    sampling event. The output is a numpy array of shape ``(n_keys, 1)``, where
    the numerical values are booleans indicating whether or not the
    corresponding keys have been pressed.

    Parameters
    ----------
    rate : int, optional
        Sampling rate, in Hz.
    keys : container of str, optional
        Keys to watch and use as input signals. The keys used here should not
        conflict with the key used by the ``Experiment`` to start the next
        task.

    Notes
    -----
    There are a couple reasonable alternatives to the way the keyboard device
    is currently implemented. One way to do it might be sampling the key states
    at a given rate and producing segments of sampled key state data, much like
    a regular data acquisition device. One issue is that actual key state
    (whether the key is being physically pressed or not) doesn't seem to be
    feasible to find out with Qt. You can hook into key press and key release
    events, but these are subject to repeat delay and repeat rate.

    Another possible keyboard device would be responsive to key press events
    themselves rather than an input sampling event. While Qt enables
    event-based keyboard handling, the method used here fits the input device
    model, making it easily swappable with other input devices.
    """

    def __init__(self, rate=10, keys=None):
        super(Keyboard, self).__init__()
        self.rate = rate

        if keys is None:
            keys = list('wasd')
        self.keys = keys

        self._qkeys = [qt_key_map[k] for k in keys]

        self._sleeper = _Sleeper(1.0/rate)
        self._data = numpy.zeros((len(self.keys), 1))

    def start(self):
        """Start the keyboard input device."""
        # install event filter to capture keyboard input events
        get_qtapp().installEventFilter(self)

    def read(self):
        """Read which keys have just been pressed.

        Returns
        -------
        data : ndarray, shape (n_keys, 1)
            A boolean array with a 1 indicating the corresponding key has been
            pressed and a 0 indicating it has not.
        """
        self._sleeper.sleep()
        out = self._data.copy()
        self._data *= 0
        return out

    def stop(self):
        """Stop the keyboard input device.

        You may need to stop the device in case you want to be able to use the
        keys watched by the device for another purpose.
        """
        # remove event filter so captured keys propagate when daq isn't used
        get_qtapp().removeEventFilter(self)

    def reset(self):
        """Reset the input device."""
        self._sleeper.reset()

    def eventFilter(self, obj, event):
        evtype = event.type()
        if evtype == QtCore.QEvent.KeyPress and event.key() in self._qkeys:
            self._data[self._qkeys.index(event.key())] = 1
            return True

        return False


class Mouse(QtCore.QObject):
    """Mouse input device.

    The mouse device works by periodically sampling (with the rate specified)
    the mouse position within the AxoPy experiment window. The output is in the
    form of a numpy array of shape ``(2, 1)``, representing either the change
    in position (default) or the absolute position in the window.

    Parameters
    ----------
    rate : int, optional
        Sampling rate, in Hz.
    position : bool, optional
        Whether or not to return the mouse's position (instead of the position
        difference from the prevoius sample).

    Notes
    -----
    In Qt's coordinate system, the positive y direction is *downward*. Here,
    this is inverted as a convenience (upward movement of the mouse produces a
    positive "velocity").

    Mouse events are intercepted here but they are not *consumed*, meaning you
    can still use the mouse to manipulate widgets in the experiment window.
    """

    def __init__(self, rate=10, position=False):
        super(Mouse, self).__init__()
        self.rate = rate
        self._sleeper = _Sleeper(1.0/rate)

        if position:
            b = 1
        else:
            b = (1, -1)
        self._filter = Filter(b)

        self.reset()

    def start(self):
        """Start sampling mouse movements."""
        get_qtapp().installEventFilter(self)

    def read(self):
        """Read the last-updated mouse position.

        Returns
        -------
        data : ndarray, shape (2, 1)
            The mouse "velocity" or position (x, y).
        """
        self._sleeper.sleep()
        return self._filter.process(self._data.copy())

    def stop(self):
        """Stop sampling mouse movements."""
        get_qtapp().removeEventFilter(self)

    def reset(self):
        """Clear the input device."""
        self._data = numpy.zeros((2, 1), dtype=float)
        self._filter.clear()
        self._sleeper.reset()

    def eventFilter(self, obj, event):
        evtype = event.type()
        if evtype == QtCore.QEvent.MouseMove:
            self._data[0] = event.x()
            self._data[1] = -event.y()
        return False


class _Sleeper(object):

    def __init__(self, read_time):
        self.read_time = read_time
        self.last_read_time = None

    def sleep(self):
        t = time.time()
        if self.last_read_time is None:
            time.sleep(self.read_time)
        else:
            try:
                time.sleep(self.read_time - (t - self.last_read_time))
            except ValueError:
                # if we're not meeting real-time requirement, don't wait
                pass

        self.last_read_time = time.time()

    def reset(self):
        self.last_read_time = None
        
class NeuranicsDevice(object):
    """Keeps track of the hardware details of the devices
   
   - sampleRate (int): DAQ sample rate in samples per second 
   - numberOfChannels (int): channels the harware is equipped with
   - channelNames (list of str): used to label the channels in the view
   - targetChannel (int): the main channel to see, this is the one shown in the Demo Task
   - batteryInfoType (int): how battery is communicated by the device
   - updatableFirmware (bool): if board has ability to update firmware remotely using a bootloader
   - dataPacketLength (int): number of data points sent in each communication 
   """
   
    def __init__(self, 
                 sampleRate: int = 640, #default as it is the current sampleRate (Feb/2024)
                 numberOfChannels: int = 0, 
                 channelNames: list = [], 
                 targetChannel:int = 0, 
                 batteryInfoType: int = 0, 
                 updatableFirmware: bool = False,
                 dataPacketLength: int = 32, #default as it is the current packet length (Feb/2024)
                 ) -> None:
        
        self._sampleRate = sampleRate
        self._numberOfChannels = numberOfChannels
        self._channelNames = channelNames
        self._targetChannel = targetChannel
        self._batteryInfoType = batteryInfoType
        self._batteryStatus = -1 #this is updated manually after initialization
        self._updatableFirmware = updatableFirmware
        self._dataPacketLength = dataPacketLength
       
    #methods: only getters (all values) and setter (batteryStatus only)
    def get_sampleRate(self) -> int:
        """DAQ sample rate, in samples per second"""
        return self._sampleRate
    def get_numberOfChannels(self) -> int:
        """number of channels transmitted by device"""
        return self._numberOfChannels
    def get_channelNames(self) -> list:
        """channel names in the order of occurrance as list of strings"""
        return self._channelNames
    def get_targetChannel(self) -> int:
        """Most important transmitted channel, the one to be displayed by the Demo task"""
        return self._targetChannel
    def get_batteryInfoType(self) -> int:
        """ 
        returns:
        - 0: no battery info given
        - 1: battery info is given as [0, 1, 2] to signify [empty, half-full, full]
        - 2: battery info is given as a percentage
        """
        return self._batteryInfoType
    
    def get_batteryStatus(self) -> int:
        """returns:
            - -1: battery status not supported
            -  0: critically low battery (0-19%)
            -  1: low battery (20-39%)
            -  2: medium battery (40-59%)
            -  3: high battery (60-79%)
            -  4: full battery (80-100%) """ 
        return self._batteryStatus  
    def set_batteryStatus(self, batteryStatus: int) -> None:
        """to set:
            - -1: battery status not supported
            -  0: critically low battery (0-19%)
            -  1: low battery (20-39%)
            -  2: medium battery (40-59%)
            -  3: high battery (60-79%)
            -  4: full battery (80-100%) """ 
        self._batteryStatus = batteryStatus
        
    def get_updatableFirmware(self) -> bool:
        """returns true if firmware contains a bootloader and can be updated remotely"""
        return self._updatableFirmware
    def get_packetLength(self) -> int:
        """ returns number of data points sent in each communication"""
        return self._dataPacketLength

    def __str__(self):
        return f'Neuranics Device, Channels: {self._channelNames}, Sample Rate: {self._sampleRate}'
