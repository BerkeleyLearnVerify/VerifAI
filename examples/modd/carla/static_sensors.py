import os
from time import sleep

import carla
import cv2
import numpy as np

from scenic.core.sensors import ActiveSensor

class CarlaOtherFeaturesSensor(ActiveSensor):
    def __init__(
        self,
        attributes=None,
    ):
        super().__init__()
            if isinstance(attributes, str):
                raise NotImplementedError(
                    "String parsing for attributes is not yet implemented. Feel free to do so."
                )
            elif isinstance(attributes, dict):
                self.attributes = attributes
            else:
                self.attributes = {}

            self.convert = None
            if convert is not None:
                if isinstance(convert, int):
                    self.convert = convert
                elif isinstance(convert, str):
                    self.convert = carla.ColorConverter.names[convert]
                else:
                    AttributeError("'convert' has to be int or string.")

            self.record_npy = record_npy

    def processing(self, data):
        array = np.frombuffer(data.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (data.height, data.width, 4))  # BGRA format
        array = array[:, :, :3]  # Take only RGB
        array = array[:, :, ::-1]  # Revert order

        return array, data.frame

    def save_last_observation(self, save_path, frame_number=None):
        if frame_number is None:
            frame_number = self.frame
        save_as = os.path.join(save_path, f"{frame_number}")
        if self.record_npy:
            np.save(save_as, self.observation)
        else:
            cv2.imwrite(f"{save_as}.png", self.observation[..., ::-1])
