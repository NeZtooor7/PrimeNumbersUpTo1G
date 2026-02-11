import time

class Chronometer:
    __current_time: float

    def __init__(self):
        self.__current_time = time.time()

    def __str__(self):
        elapsed = time.time() - self.__current_time
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        str_hours = str(int(hours))
        str_minutes = str(int(minutes))
        str_seconds = "%.2f"%seconds
        if hours < 10:
            str_hours = "0" + str_hours
        if minutes < 10:
            str_minutes = "0" + str_minutes
        if seconds < 10:
            str_seconds = "0" + str_seconds
        str_time = ""

        if hours > 0:
            str_time = "%s:%s:%s"%(str_hours, str_minutes, str_seconds)
        elif minutes > 0:
            str_time = "%s:%s"%(str_minutes, str_seconds)
        else:
            str_time = "%.2f"%seconds

        return str_time