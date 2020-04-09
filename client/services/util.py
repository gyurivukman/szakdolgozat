import time
from datetime import timezone, timedelta


class TimeConverter:

    def convertTimestampToLocalDateTime(self, stamp):

        offsetHours = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        offsetHours = offsetHours / (3600 * -1)

        delta = timedelta(hours=offsetHours)
        zone = timezone(delta)

        return datetime.fromtimestamp(stamp, zone)

    def convertDateTimeToTouchCompatibleString(self, dt):
        return dt.strftime("%Y%m%d%H%M.%S")
