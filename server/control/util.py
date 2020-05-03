
def httpRangeHeaderIntervalGenerator(total, intervalSize):
    for start in range(16, total, intervalSize):
        end = min(total - 1, start + intervalSize - 1)
        yield [start, end]


def chunkSizeGenerator(total, chunkSize):
    remainder = total
    while remainder > chunkSize:
        remainder = remainder - chunkSize
        yield chunkSize, remainder
    yield remainder, 0
