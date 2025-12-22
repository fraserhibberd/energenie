"""Should be run after midnight and before sunset"""
import argparse
import logging
from datetime import datetime, time as time_cls, timedelta, timezone
import time

from gpio_controller import EnergenieGPIO
from sun_times import Sun
from logging_config import configure_logging


LOGGER = logging.getLogger('energenie.main')

LATITUDE = 52.01355000660077
LONGITUDE = -2.5974807343283923


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


def main(argv=None):
    args = _parse_args(argv)
    configure_logging()
    reference = _local_reference_datetime()
    sun = Sun(reference, LATITUDE, LONGITUDE)

    sunset_time = sun.sunset()

    turn_on_dt = _apply_offset(reference.date(), sunset_time, args.turn_on_offset_minutes, reference.tzinfo)
    turn_on_time = turn_on_dt.timetz()
    turn_off_dt = datetime.combine(reference.date(), time_cls(*args.lights_off_time))
    if reference.tzinfo is not None:
        turn_off_dt = turn_off_dt.replace(tzinfo=reference.tzinfo)
    turn_off_time = turn_off_dt.timetz()

    LOGGER.info('Sunset: %s, turn_on: %s, turn_off: %s', sunset_time, turn_on_time, turn_off_time)

    controller = EnergenieGPIO(args.receiver_socket)

    if turn_on_dt >= turn_off_dt:
        LOGGER.warning('Turn-on time %s is at/after cutoff %s; ensuring light is off and exiting', turn_on_time, turn_off_time)
        controller.turn_off()
        return

    if reference >= turn_off_dt:
        LOGGER.error('Cron ran at/after cutoff; ensuring light is off')
        controller.turn_off()
        return

    if reference >= turn_on_dt:
        LOGGER.warning('Cron ran after the scheduled turn-on; ensuring light is on')
        controller.turn_on()
    else:
        LOGGER.info('Waiting until turn-on time...')
        sleep_until_datetime(turn_on_dt)
        controller.turn_on()

    LOGGER.info('Waiting until cutoff time...')
    sleep_until_datetime(turn_off_dt)
    controller.turn_off()


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Energenie sunset scheduler')
    parser.add_argument('--turn-on-offset-minutes', type=int, help='Minutes relative to sunset to switch on (negative = before)', required=True)
    parser.add_argument('--lights-off-time', type=_hhmm, help='Daily cutoff in HH:MM (24h)', required=True)
    parser.add_argument('--receiver-socket', type=_receiver, help='Energenie receiver socket (1-4)', required=True)
    return parser.parse_args(argv)


def _hhmm(value):
    try:
        hour_str, minute_str = value.split(':', 1)
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError('time must be HH:MM')
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise argparse.ArgumentTypeError('time must be within 00:00-23:59')
    return hour, minute


def _receiver(value):
    try:
        receiver = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError('receiver must be an integer 1-4')
    if receiver not in (1, 2, 3, 4):
        raise argparse.ArgumentTypeError('receiver must be between 1 and 4')
    return receiver


if __name__ == '__main__':
    main()
