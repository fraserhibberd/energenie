"""Should be run after midnight and before sunset"""
import logging
from datetime import datetime, time as time_cls, timedelta, timezone
import time

from gpio_controller import EnergenieGPIO
from sun_times import Sun

LATITUDE = 52.01355000660077
LONGITUDE = -2.5974807343283923
TURN_ON_OFFSET_MINUTES = -30  # negative=before sunset, positive=after sunset
FIXED_LIGHTS_OFF_TIME = (23, 0)  # (hour, minute) daily cutoff
RECEIVER_SOCKET = 2


LOG_PATH = 'scheduler.log'


def _configure_logging():
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )


def _local_reference_datetime():
    """Build a timezone-aware datetime for the current locale."""
    local_now = datetime.now()
    utc_now = datetime.utcnow()
    offset_minutes = int(round((local_now - utc_now).total_seconds() / 60.0))
    tz = timezone(timedelta(minutes=offset_minutes))
    return local_now.replace(tzinfo=tz)


def _apply_offset(base_date, base_time, offset_minutes, tzinfo):
    combined = datetime.combine(base_date, base_time).replace(tzinfo=tzinfo)
    adjusted = combined + timedelta(minutes=offset_minutes)
    return adjusted


def sleep_until_datetime(target_dt):
    """Sleep until target_dt; raise if the deadline already passed."""
    if not isinstance(target_dt, datetime):
        raise TypeError('target_dt must be a datetime.datetime instance')
    now = datetime.now(target_dt.tzinfo)
    if target_dt <= now:
        raise RuntimeError('Target datetime %s has already passed' % target_dt)
    delta = target_dt - now
    time.sleep(delta.total_seconds())


def main():
    _configure_logging()
    reference = _local_reference_datetime()
    sun = Sun(reference, LATITUDE, LONGITUDE)

    sunset_time = sun.sunset()

    turn_on_dt = _apply_offset(reference.date(), sunset_time,
                               TURN_ON_OFFSET_MINUTES, reference.tzinfo)
    turn_on_time = turn_on_dt.timetz()
    turn_off_dt = datetime.combine(reference.date(),
                                   time_cls(*FIXED_LIGHTS_OFF_TIME))
    if reference.tzinfo is not None:
        turn_off_dt = turn_off_dt.replace(tzinfo=reference.tzinfo)
    turn_off_time = turn_off_dt.timetz()

    logging.info('Sunset: %s, turn_on: %s, turn_off: %s',
                 sunset_time, turn_on_time, turn_off_time)

    controller = EnergenieGPIO()

    if reference >= turn_off_dt:
        logging.error('Cron ran at/after cutoff; ensuring socket %d is OFF immediately', RECEIVER_SOCKET)
        controller.turn_off(RECEIVER_SOCKET)
        return

    if reference >= turn_on_dt:
        logging.warning('Cron ran after the scheduled turn-on; switching socket %d ON now', RECEIVER_SOCKET)
        controller.turn_on(RECEIVER_SOCKET)
    else:
        logging.info('Waiting until turn-on time...')
        sleep_until_datetime(turn_on_dt)
        controller.turn_on(RECEIVER_SOCKET)

    logging.info('Waiting until cutoff time...')
    sleep_until_datetime(turn_off_dt)
    controller.turn_off(RECEIVER_SOCKET)


if __name__ == '__main__':
    main()
