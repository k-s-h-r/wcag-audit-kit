"""Guard the bounds of the machine-only media observations."""
import unittest

from benchmarks import residual_media


class ResidualMediaTests(unittest.TestCase):
    def test_unobserved_alternative_is_not_always_a_failure(self):
        plan = dict(target='#media', region='main')
        evidence = dict(media=dict(source='clip.webm'),
                        scope=dict(mediaInside=True, alternatives=[], plainMediaOnly=False))
        row, = residual_media.evaluate('1.2.3', plan, evidence)
        self.assertEqual('cant_tell', row['outcome'])

    def test_activated_autoplay_sample_cannot_be_scored(self):
        plan = dict(target='#media', region='main')
        samples = [dict(at=100, position=0.1, paused=False, muted=False, volume=1, peak=0.3),
                   dict(at=3600, position=3.6, paused=False, muted=False, volume=1, peak=0.4)]
        evidence = dict(before=dict(autoplay=True, activated=True), playback=dict(error=None, controls=False),
                        scope=dict(plainMediaOnly=True), samples=samples, pause=None, after=None)
        row, = residual_media.evaluate('1.4.2', plan, evidence)
        self.assertEqual('cant_tell', row['outcome'])

    def test_description_does_not_pass_on_a_second_url_with_identical_bytes(self):
        plan = dict(target='#video', select='#describe')
        before = dict(source='http://127.0.0.1/base.webm')
        alternate = dict(source='http://127.0.0.1/alternate.webm', ended=True, error=None, visible=True,
                         height=36, audioBytes=100, videoBytes=100, duration=4, played=[[0, 4]])
        evidence = dict(before=before, playback=alternate, initially_pressed='false',
                        pressed='true', resources=['same', 'same'])
        row, = residual_media.evaluate('1.2.5', plan, evidence)
        self.assertEqual('cant_tell', row['outcome'])
