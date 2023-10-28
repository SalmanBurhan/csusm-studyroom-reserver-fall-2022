from studyroom_reserver.kellog_library import KellogLibrary
from datetime import datetime, timedelta
import constants
import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s :: %(name)s :: %(levelname)-s :: %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p')


if __name__ == '__main__':

    library = KellogLibrary(
        email=constants.CSUSM_EMAIL,
        password=constants.CSUSM_PASSWORD)
    today = datetime.today()

    # Target Times To Schedule Based On Day Of Week
    if not (target_time := constants.TARGET_TIMES.get(
            today.weekday() + 1 % 7)):
        logging.getLogger('Main').error(
            'No Target Time Defined For Tomorrow.')
        exit()

    hour, minute = constants.TARGET_TIMES[(today.weekday() + 1) % 7]
    desired_slot = today.replace(day=today.day+1,
                                 hour=hour,
                                 minute=minute,
                                 second=0,
                                 microsecond=0)
    selected_room = None

    # Search For Rooms Floor Of Preferred Room.
    open_rooms = library.rooms_available(
        desired_slot,
        attendees=constants.ATTENDEES_COUNT,
        floor_preference=int(str(constants.PREFERRED_ROOM)[0]))

    # Select Preferred Room, If It Is Available.
    for room in open_rooms:
        if room.room_details.number == constants.PREFERRED_ROOM:
            selected_room = room
            break

    # If The Preferred Room Was Found.
    if selected_room:
        library.reserve(selected_room)

    # If The Preferred Room Is Not Available, Book Next Available.
    else:
        open_rooms = library.rooms_available(
            desired_slot, attendees=constants.ATTENDEES_COUNT)
        if len(open_rooms) > 0:
            selected_room = open_rooms[0]
            library.reserve(selected_room)
        else:
            # If There Were No Options At All, Keep Looking In 30 Minute
            # Increments With Maximum Of 3 Attempts, Sleeping 10 Seconds
            # Between Each Attempt.
            from time import sleep
            attempts = 0
            while (selected_room is None and attempts < 3):
                desired_slot += timedelta(minutes=30)
                open_rooms = library.rooms_available(
                    desired_slot, attendees=constants.ATTENDEES_COUNT)
                if len(open_rooms) > 0:
                    selected_room = open_rooms[0]  # First Available
                    library.reserve(selected_room)
                else:
                    attempts += 1
                    sleep(10)

    # Exit Safely
    library.exit()
