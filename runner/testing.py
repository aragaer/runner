import os

from .channel import PipeChannel


class TestChannel(PipeChannel):

    def __init__(self):
        self._in_r, self._out_w = os.pipe()
        self._out_r, self._in_w = os.pipe()
        super().__init__(self._out_r, self._out_w)
        self._inner = PipeChannel(self._in_r, self._in_w)

    def get(self):
        return self._inner.read()

    def put(self, data):
        self._inner.write(data)
