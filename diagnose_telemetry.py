import os
import sys
import psutil
from src.f1_data import load_session, get_race_telemetry

proc = psutil.Process(os.getpid())

def mem(label):
    mi = proc.memory_info()
    print(f"{label}: rss={mi.rss/1024**2:.1f}MB vms={mi.vms/1024**2:.1f}MB")

print('start')
mem('start')

session = load_session(2023, 12, 'R')
mem('after load_session')

try:
    data = get_race_telemetry(session, session_type='R')
    mem('after get_race_telemetry')
    print('frames', len(data['frames']))
except Exception as e:
    print('EXCEPTION', type(e).__name__, e)
    raise
