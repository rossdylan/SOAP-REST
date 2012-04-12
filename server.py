from bottle import route, run, request
from threading import Thread, Lock
import os
import json
class SoapServer(object):

    def __new__(self, *args, **kwargs):
        """
        We use __new__ to use route in order to connect our http endpoints to functions
        """

        obj = super(SoapServer, self).__new__(self, *args, **kwargs)
        route("/status", method="GET")(obj.status)
        route("play", method="POST")(obj.playStream)
        return obj

    def __init__(self, port, bathrooms, timeout=20):
        """
        Create a new SOAP REST Server

        :type port: int
        :param port: port to listen for requests on

        :type bathrooms: dict
        :param bathrooms: A dict mapping bathroom names to sound devices

        :type timeout: int
        :param timeout: time in minutes to wait before killing a stream
        """

        self.soap_port = port
        self.timeout = timeout * 60
        self.command_string = "timeout -s SIGKILL {} mplayer -cache 1024 -lavdopts threads=5 -noconsolecontrols -ao alsa;device=hw={}.0 {}"
        self.bathrooms = bathrooms
        self.locks = {}
        self.currently_playing = {}
        for device in self.bathrooms.items():
            self.locks[device] = Lock()

    def playStream(self):
        """
        Play a stream recieved via REST
        """

        bathroom = request.forms.get("bathroom")
        stream = request.forms.get("stream")
        play_thread = Thread(target=self.playSong,args=(self.bathrooms[bathroom],stream))
        play_thread.start()

    def status(self):
        """
        Get the song playing in each Bathroom and return it as json
        """

        status_dict = {}
        for bathroom in self.bathrooms:
            status_dict[bathroom] = self.currently_playing[self.bathrooms[bathroom]]
        return json.dumps(status_dict)

    def playSong(self,device, stream):
        """
        Acquire a lock on a sound device and play a stream through it

        :type device: int
        :param device: the device number to play the stream through

        :type stream: str
        :param stream: string containing the stream to stream to a bathroom
        """

        self.locks[device].acquire()
        self.currently_playing[device] = stream
        os.system(self.command_string.format(self.timeout,device,stream))
        self.currently_playing[device] = ""
        self.locks[device].release()

    def start(self):
        """
        Start the bottle http server
        """

        run(host="0.0.0.0",port=self.port)

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "north":
        bathrooms = {"The L": 2, "The Stairs": 1, "The Vator": 0}
    if sys.argv[1] == "south":
        bathrooms = {"The Stairs": 1, "The Vator": 0}
    else:
        exit()
    server = SoapServer(1234, bathrooms)
    server.start()
