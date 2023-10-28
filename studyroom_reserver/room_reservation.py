from datetime import datetime
from .room_details import RoomDetails


class RoomReservation:

    def __init__(self,
                 start: datetime,
                 end: datetime,
                 attendees: int,
                 room_details: RoomDetails):

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert isinstance(attendees, int)
        assert isinstance(room_details, RoomDetails)

        self.start = start
        self.end = end
        self.attendees = attendees
        self.room_details = room_details
        self.confirmed = False

    @property
    def human_readable_date(self):
        return self.start.strftime('%Y-%m-%d')

    @property
    def human_readable_start_time(self):
        return self.start.strftime('%I:%M:%S %p')

    @property
    def human_readable_end_time(self):
        return self.end.strftime('%I:%M:%S %p')

    def __repr__(self):
        return f'{self.__class__.__name__}' + \
            ', '.join([f'(date: {self.start.strftime("%Y-%m-%d")}',
                       f'confirmed: {self.confirmed}',
                       f'start: {self.start.strftime("%I:%M:%S %p")}',
                       f'attendees: {self.attendees}',
                       f'end: {self.end.strftime("%I:%M:%S %p")}',
                       f'room: {self.room_details})'])
