import random
import string
from datetime import timedelta

def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return "".join(randlst)

def convertHHmmssfff(time:timedelta):
    totsec = time.total_seconds()
    hh = int(totsec // 3600)
    mm = int((totsec % 3600) // 60)
    ss = int(totsec % 60)
    mi = int((totsec % 1) * 1000)
    return f'{hh:02}:{mm:02}:{ss:02},{mi:03}'
