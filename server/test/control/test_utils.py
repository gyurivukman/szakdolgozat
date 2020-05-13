import unittest

from control.util import httpRangeHeaderIntervalGenerator, chunkSizeGenerator


class TestHTTPRangeHeaderIntervalGenerator(unittest.TestCase):

    def test_starts_at_16_bytes_for_the_init_vector(self):
        total = 32
        intervalSize = 16
        intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], [16, total - 1])

    def test_generates_every_interval_with_the_interval_size(self):
        total = 48
        intervalSize = 16
        intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]
        expectedIntervals = [[16, 31], [32, total - 1]]

        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals, expectedIntervals)
        for interval in intervals:
            self.assertEqual(interval[1] - interval[0], intervalSize - 1)

    def test_generates_a_single_interval_if_interval_size_is_greater_than_total(self):
        total = 32
        intervalSize = 64
        intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], [16, total - 1])

    def test_throws_exception_if_interval_size_is_zero(self):
        total = 32
        intervalSize = 0
        try:
            intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]
            self.fail(f"Interval generator should throw ValueError with intervalSize: 0. Result: {intervals}")
        except ValueError:
            pass

    def test_generates_no_intervals_if_total_is_zero(self):
        total = 0
        intervalSize = 16
        intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]

        self.assertEqual(intervals, [])

    def test_throws_exception_if_interval_size_is_negative(self):
        total = 32
        intervalSize = -5
        try:
            intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]
            self.fail(f"Interval generator should throw ValueError with intervalSize: -5. Result: {intervals}")
        except ValueError:
            pass

    def test_throws_exception_if_total_is_negative(self):
        total = -32
        intervalSize = 5
        try:
            intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]
            self.fail(f"Interval generator should throw ValueError with total: -32. Result: {intervals}")
        except ValueError:
            pass

    def test_single_interval_is_generated_if_total_is_equal_to_intervalSize(self):
        total = 32
        intervalSize = 32

        intervals = [interval for interval in httpRangeHeaderIntervalGenerator(total, intervalSize)]

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], [16, 31])


class TestChunkSizeGenerator(unittest.TestCase):

    def test_generates_multiple_chunks_and_remainders_correctly(self):
        total = 30
        chunkSize = 16

        intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]

        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals[0], (16, 14))
        self.assertEqual(intervals[1], (14, 0))

    def test_error_on_chunkSize_zero(self):
        total = 30
        chunkSize = 0
        try:
            intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]
            self.fail(f"Chunksize generator should throw ValueError with chunkSize: 0. Result: {intervals}")
        except ValueError:
            pass

    def test_error_on_negative_total(self):
        total = -30
        chunkSize = 0
        try:
            intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]
            self.fail(f"Chunksize generator should throw ValueError with total: -30. Result: {intervals}")
        except ValueError:
            pass

    def test_error_on_negative_chunkSize(self):
        total = 30
        chunkSize = -5
        try:
            intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]
            self.fail(f"Chunksize generator should throw ValueError with chunkSize: -5. Result: {intervals}")
        except ValueError:
            pass

    def test_doublezero_interval_is_generated_on_zero_total(self):
        total = 0
        chunkSize = 10
        intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], (0, 0))

    def test_single_interval_is_generated_if_chunksize_is_greater_than_total(self):
        total = 10
        chunkSize = 15
        intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], (10, 0))

    def test_single_interval_is_generated_if_chunksize_is_equal_to_total(self):
        total = 10
        chunkSize = 10
        intervals = [interval for interval in chunkSizeGenerator(total, chunkSize)]

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], (10, 0))
