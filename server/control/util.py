
def httpRangeHeaderIntervalGenerator(total, intervalSize):
    if intervalSize < 0:
        raise ValueError("argument 'intervalSize' must be greater than 0!")
    elif total < 0:
        raise ValueError("argument 'total' must not be a negative number!")

    for start in range(16, total, intervalSize):
        end = min(total - 1, start + intervalSize - 1)
        yield [start, end]


def chunkSizeGenerator(total, chunkSize):
    if chunkSize <= 0:
        raise ValueError("argument: 'chunkSize' must be greater than 0!")
    elif total < 0:
        raise ValueError("argument 'total' must not be a negative number!")

    remainder = total
    while remainder > chunkSize:
        remainder = remainder - chunkSize
        yield chunkSize, remainder
    yield remainder, 0
