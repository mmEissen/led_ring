import typing as t

import numpy as np
from numpy.fft import rfft as fourier_transform, rfftfreq
import matplotlib
matplotlib.use("agg")
from scipy import ndimage

import a_weighting_table
from audio_tools import AudioInput
from airpixel.client import AbstractClient, Pixel


class ContiniuousVolumeNormalizer:
    def __init__(self, min_threshold=0.001, falloff=32, debug=False) -> None:
        self._min_threshold = min_threshold
        self._falloff = falloff
        self._current_threshold = self._min_threshold
        self._last_call = 0
        self._debug = debug

    def _update_threshold(self, max_sample, timestamp):
        if max_sample >= self._current_threshold:
            self._current_threshold = max_sample
        else:
            target_threshold = max_sample
            factor = 1 / self._falloff ** (timestamp - self._last_call)
            self._current_threshold = self._current_threshold * factor + target_threshold * (
                1 - factor
            )
        self._last_call = timestamp

    def normalize(self, signal, timestamp):
        if self._last_call == 0:
            self._last_call = timestamp
        max_sample = np.max(np.abs(signal))
        self._update_threshold(max_sample, timestamp)
        if self._current_threshold >= self._min_threshold:
            if self._debug:
                print(self._current_threshold)
            return signal / self._current_threshold
        return signal * 0


class FadingCircularEffect:
    def __init__(
        self,
        audio_input: AudioInput,
        ring_client: AbstractClient,
        signal_normalizer: ContiniuousVolumeNormalizer,
        window_size: float=0.1,
        first_octave: int = 4,
        number_octaves: int = 8,
        falloff: float = 64,
        color_rotation_period: float = 180,
    ) -> None:
        self._bins_per_octave = ring_client.num_leds
        self._ring_client = ring_client
        self._audio_input = audio_input
        self._window_size = window_size
        self._fourier_frequencies = rfftfreq(
            self._audio_input.seconds_to_samples(window_size),
            d=self._audio_input.sample_delta,
        )
        self._sample_points = np.exp2(
            (
                np.arange(self._ring_client.num_leds * number_octaves)
                + self._ring_client.num_leds * first_octave
            )
            / self._ring_client.num_leds
        )
        self._a_weighting = np.interp(
            self._sample_points,
            a_weighting_table.frequencies,
            a_weighting_table.weights,
        )
        self._signal_normalizer = signal_normalizer
        self._last_values = np.zeros(self._ring_client.num_leds)
        self._last_time = 0
        self._falloff = falloff
        self._color_rotation_period = color_rotation_period

    def _frequencies(self, audio_data):
        return np.absolute(fourier_transform(audio_data))

    def __call__(self, timestamp):
        audio = np.array(self._audio_input.get_data(length=self._window_size))
        measured_frequencies = self._frequencies(audio)
        sampled_frequencies = np.interp(
            self._sample_points, self._fourier_frequencies, measured_frequencies
        )
        weighted_frequencies = sampled_frequencies ** 2 * self._a_weighting
        normalized = self._signal_normalizer.normalize(weighted_frequencies, timestamp)
        f = self._to_colors(normalized, timestamp)
        return f

    def _combine_values(self, new_values, timestamp):
        diff = timestamp - self._last_time
        self._last_time = timestamp
        factor = 1 / self._falloff ** (diff) if diff < 2 else 0
        self._last_values = self._last_values * factor
        self._last_values = np.maximum(self._last_values, new_values)
        return self._last_values
    
    def _values_to_rgb(self, values, timestamp):
        hue = np.full(
            values.shape, 
            (timestamp % self._color_rotation_period) / self._color_rotation_period,
        )
        saturation = np.clip(values * (-2), -2, -1) + 2
        values_color = np.clip(values * 2, 0, 1)
        hsvs = np.transpose(np.array((hue, saturation, values_color)))
        rgbs = matplotlib.colors.hsv_to_rgb(hsvs)
        return rgbs

    def _to_colors(self, data, timestamp):
        smoothed = ndimage.gaussian_filter(data, sigma=2)
        wrapped = np.reshape(smoothed, (-1, self._ring_client.num_leds))
        color_values = np.maximum.reduce(wrapped)
        new_values = self._combine_values(color_values, timestamp)
        return [
            Pixel(g, r, b)
            for r, g, b in self._values_to_rgb(new_values, timestamp)
        ]    