class RoomDetails:

    def __init__(self, room_id: int, room_number: int):
        self.id = int(room_id)
        self.number = int(room_number)
        self.name = None
        self.capacity = None
        self.images = None
        self.amenities = None

    def load_details(self):
        KellogLibrary.load_full_room_details(self)

    def __repr__(self):
        return f'{self.__class__.__name__}'\
            '(id: {self.id}, room_number: {self.number})'
