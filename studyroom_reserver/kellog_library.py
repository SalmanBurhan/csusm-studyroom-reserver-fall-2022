from .browser import Browser
from .room_details import RoomDetails
from .room_amenities import RoomAmenities
from .room_reservation import RoomReservation
from duo import duo_gen

from selenium.webdriver.remote.webelement import WebElement
from urllib.parse import urlparse, urlencode, parse_qs
from datetime import datetime, timedelta

import logging
import re
import requests
import bs4


class KellogLibrary:
    BASE_URL = "https://libapps.csusm.edu/groupstudy"
    MAX_DAILY_HOURS = 3
    MAX_WEEKLY_HOURS = 12
    VALID_ROOM_FLOORS = [2, 4, 5]

    def __init__(self, email: str, password: str):

        # Initiate Loggers
        self.logger = logging.getLogger('Kellog Library')
        self.logger.setLevel(level=logging.INFO)

        self.auth_flow_logger = logging.getLogger('Auth Flow')
        self.auth_flow_logger.setLevel(level=logging.INFO)

        self.browser = None
        self.email = email
        self.password = password

    # Safely Quit Browser
    def exit(self):
        if isinstance(self.browser, Browser):
            self.browser.quit()

    @property
    def logged_in(self) -> bool:

        if self.browser is None:
            return False

        a_tag = self.browser.element('#app-topnav > li:nth-child(1) > a')
        assert (isinstance(a_tag, WebElement))

        state = True if 'Signed in' in a_tag.text else False
        self.auth_flow_logger.info(f'Is Logged In ==> {state}')

        return state

    def login(self) -> bool:

        self.auth_flow_logger.info('Beginning Auth Flow')

        # Ensure Browser is Initiated
        if self.browser is None:
            self.browser = Browser()

        # Build Base Page URL
        url = f'{self.BASE_URL}/reservation_calendar_ada.php'

        try:
            # Navigate To URL
            self.browser.get(url)

            # Click Login Button
            self.browser.element('#app-topnav > li:nth-child(1) > a').click()

            # Begin CSUSM Portion of Auth Flow
            self.auth_flow_logger.info('Beginning CSUSM Portion of Auth Flow')
            self.browser.element('input[type="email"]').send_keys(self.email)
            self.browser.element('input[type="submit"]').click()
            self.browser.element(
                'input[type="password"]').send_keys(self.password)
            self.browser.element('input[type="submit"]').click()

            # Begin DUO 2FA Portion of Auth Flow
            self.auth_flow_logger.info(
                'Beginning DUO 2FA Portion of Auth Flow')
            self.browser.element('button[id="passcode"]').click()
            self.auth_flow_logger.info('Generating 2FA Code')
            code = duo_gen.generate_code()
            self.auth_flow_logger.info(f'2FA Code ==> {code}')
            self.browser.element('input[name="passcode"]').send_keys(code)
            self.browser.element('button[id="passcode"]').click()

            # Begin CSUSM Redirection Portion of Auth Flow
            self.auth_flow_logger.info('Awaiting Redirect To CSUSM')
            if (stay_signed_in_bttn := self.browser.element(
                    'input[type="submit"][value="Yes"]')) is not None:
                stay_signed_in_bttn.click()

            if success := self.logged_in:
                self.auth_flow_logger.info('Auth Flow Successful')
            else:
                self.auth_flow_logger.error('Auth Flow Failed')

            return success

        except Exception as e:
            self.auth_flow_logger.error(
                f'Auth Flow Failed With Exception: {e}')
            return False

    def rooms_available(self,
                        start: datetime = datetime.now(),
                        duration_hours: int = MAX_DAILY_HOURS,
                        floor_preference: int = -1,
                        attendees: int = 1,
                        amenities: [RoomAmenities] = []) -> [RoomReservation]:
        """Parses availability and filters results for given conditions.

        Args:
            start (datetime, optional): Defaults to datetime.now().
            duration_hours (int, optional): Defaults to MAX_DAILY_HOURS = 3.
            floor_preference (int, optional): Valid values between [3, 5]. \
                Defaults to -1.
            attendees (int, optional): Defaults to 1.
            amenities (RoomAmenities], optional): Defaults to [].

        Returns:
            [RoomReservation]: List of potential reservations.
        """

        assert isinstance(start, datetime)
        assert isinstance(duration_hours, int) and duration_hours >= 1
        assert isinstance(attendees, int) and attendees >= 1
        assert isinstance(floor_preference, int)
        if floor_preference > -1:
            assert floor_preference in self.VALID_ROOM_FLOORS

        # Build URL Parameters
        date = start.strftime('%Y-%m-%d')
        start_time = start.strftime('%Y-%m-%d %H:%M:%S')
        end_time = (start + timedelta(hours=duration_hours)) \
            .strftime('%Y-%m-%d %H:%M:%S')

        # Build URL
        params = {'selected_date': date, 'start_time': start_time,
                  'end_time': end_time, 'minimum_capacity': attendees,
                  'amenity_filter[]': [a.value for a in amenities]}

        url = f'{self.BASE_URL}' \
            f'/reservation_calendar_ada.php?{urlencode(params, True)}'

        self.logger.info(
            f'Searching For Rooms From {start_time} '
            f'To {end_time} On Floor: '
            f'{"Any" if floor_preference == -1 else floor_preference}')

        # Load and Parse Page
        response = requests.get(url)
        assert response.status_code == 200
        self.logger.info("Parsing Web Page")
        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        # Get Table Containing List of Available Rooms
        table = soup.select_one('table[width="100%"] > tr[valign="top"] > td')
        assert isinstance(table, bs4.element.Tag)

        # Regex Matcher
        matcher = re.compile((
            r'Room\W+(?P<room_number>\d{1,}),\W+(?P<capacity>\d{1,2}) seats,'
            r'\W+(?:(?P<month>\d{1,2})\/(?P<day>\d{1,2})\/(?P<year>\d{4})),\W+'
            r'(?:(?P<start_hour>\d{1,2})\:(?P<start_minute>\d{2})'
            r'(?P<start_am_pm>am|pm))\W+to\W+(?:(?P<end_hour>\d{1,2})'
            r'\:(?P<end_minute>\d{2})(?P<end_am_pm>am|pm))'))

        # Iterate Through Table Data, Validating Data Against Our Parameters
        self.logger.info("Validating and Mapping Search Results")
        availability: [RoomReservation] = []
        for a_tag in table.find_all('a'):
            result = matcher.match(a_tag.text)
            assert isinstance(result, re.Match)

            query_string = parse_qs(urlparse(a_tag.get('href')).query)
            assert query_string['room_id'] is not None and len(
                query_string['room_id']) > 0

            room_id = query_string['room_id'][0].split("_")[0]
            room_number = result.group('room_number')

            # If Floor Preference Set and Room Does
            # Not Match It, Exclude From Results.
            if floor_preference != -1 \
                    and room_number[:1] != str(floor_preference):
                continue
            # room_capacity = result.group('capacity')

            _start = datetime(year=int(result.group('year')),
                              month=int(result.group('month')),
                              day=int(result.group('day')),
                              hour=int(result.group('start_hour')),
                              minute=int(result.group('start_minute')))

            if result.group('start_am_pm') == 'pm':
                _start = _start.replace(hour=_start.hour+12)

            _end = datetime(year=int(result.group('year')),
                            month=int(result.group('month')),
                            day=int(result.group('day')),
                            hour=int(result.group('end_hour')),
                            minute=int(result.group('end_minute')))

            if result.group('end_am_pm') == 'pm':
                _end = _end.replace(hour=_end.hour+12)

            assert start == _start
            assert (_end - _start) == timedelta(hours=duration_hours)

            availability.append(
                RoomReservation(
                    start=_start, end=_end, attendees=attendees,
                    room_details=RoomDetails(
                        room_id=room_id, room_number=room_number)
                )
            )

        self.logger.info(f'Search Returned {len(availability)} Results')
        return availability

    def reserve(self, reservation: RoomReservation) -> bool:
        """Attempts to reserve a given RoomReservation returned from the \
        rooms_available method.

        Args:
            reservation (RoomReservation): a reservation containing the \
                parameters required to attempt a booking.

        Returns:
            bool: the success state of the booking.
        """
        try:
            assert self.logged_in
        except AssertionError:
            self.logger.error('You Must Be Logged In To Make A Reservation')
            return False

        self.logger.info(f'Reserving Room {reservation.room_details.number} '
                         f'on {reservation.human_readable_date} '
                         f'from {reservation.human_readable_start_time} '
                         f'to {reservation.human_readable_end_time} '
                         f'for {reservation.attendees} attendee(s)')

        # Build Reservation URL
        url = self.__build_reservation_request_url(reservation=reservation)

        # Navigate To Built URL
        self.browser.get(url)

        # Get Response Message
        self.logger.info("Parsing and Validating Server Response")
        is_successful = False
        response_elem = self.browser.element('#maincontent > h3')

        try:
            assert isinstance(response_elem, WebElement) \
                and 'confirmed' in response_elem.text.lower()
            self.logger.info(
                f'Room {reservation.room_details.number} '
                'Successfully Reserved')
            is_successful = False

        # If Element Was Not Found, Check For An Error Message Instead
        except AssertionError:
            response_elem = self.browser.element(
                '#maincontent > div[class="error"]')
            try:
                assert isinstance(response_elem, WebElement)
                self.logger.error(
                    f'Unable To Reserve Room {reservation.room_details.number}'
                    f' With Response ==> {response_elem.text}')
                is_successful = False

            # An Error Element Was Also Not Found, Something Else Is Wrong
            except AssertionError:
                self.logger.error(
                    f'Unable To Reserve Room {reservation.room_details.number}'
                    f' With Unknown Error')
                is_successful = False

        reservation.confirmed = is_successful

        return is_successful

    def __build_reservation_request_url(self, reservation: RoomReservation):
        """An internal method which creates a confirmation url with the \
        relevant query parameters which would have been created had the \
        user manually selected the date and time slots via the browser.

        Args:
            reservation (RoomReservation)

        Returns:
            str: a confirmation url.
        """
        self.logger.info("Building Reservation Request")

        # Create Patron from Email Address
        assert self.email is not None
        patron = self.email.split('@')[0]
        assert isinstance(patron, str)

        # Assert Expected Types
        assert isinstance(reservation.room_details.id, int)
        assert isinstance(reservation.start, datetime)
        assert isinstance(reservation.end, datetime)

        selected_date = reservation.start.strftime('%Y-%m-%d')
        start = reservation.start.strftime('%Y%m%d%H%M%S')
        end = reservation.end.strftime('%Y%m%d%H%M%S')

        return (f'{self.BASE_URL}/confirm_reservation.php'
                f'?requesting_patron={patron}'
                f'&room_id={reservation.room_details.id}_1'
                f'&selected_date={selected_date}'
                f'&start_time={start}'
                f'&end_time={end}'
                f'&attendees={reservation.attendees}'
                '&terms=&otf=&terms=1'
                '&submitted=Confirm%20Reservation')

    @classmethod
    def load_full_room_details(cls, room: RoomDetails):
        """Extends a RoomDetails object to include rich details including \
        the ammenities in the room and a map of the floor on which the \
        room is located.

        Args:
            room (RoomDetails): the original RoomDetails object, with newly \
                populated properties.
        """
        # Build URL
        url = f'{KellogLibrary.BASE_URL}/room_details.php?room_id={room.id}'

        # Load and Parse Page
        response = requests.get(url)
        assert response.status_code == 200
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        assert isinstance(soup, bs4.BeautifulSoup)

        # Get Room Name
        room_name = soup.select_one('h2[id="PageTitle"]')
        assert isinstance(room_name, bs4.element.Tag)
        room.name = room_name.text

        # Get Room Capacity
        room_capacity = soup.select_one('div[class="room-capacity"] > p')
        assert isinstance(room_capacity, bs4.element.Tag) \
            and not room_capacity.is_empty_element
        room.capacity = int(room_capacity.text)

        # Get Room Images
        room_images = soup.select('a[class="thumbnail"]')
        assert all(isinstance(o, bs4.element.Tag) for o in room_images)

        room.images = {'room': [], 'floor_map': None}
        for room_image in room_images:
            rel_attr = room_image['rel'][0]
            assert rel_attr == 'map' or rel_attr == 'room'
            floor_map = True if rel_attr == 'map' else False
            img_url = f'{KellogLibrary.BASE_URL}/{room_image.get("href")}'

            if floor_map:
                room.images['floor_map'] = img_url
            else:
                room.images['room'].append(img_url)

        # Get Room Amenities
        room_amenities = soup.select('div[class="room-amenities"] > ul > li')
        assert all(isinstance(o, bs4.element.Tag) for o in room_amenities)
        room.amenities = [o.text for o in room_amenities]
