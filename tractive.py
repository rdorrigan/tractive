import requests
from urllib.parse import urljoin
from requests.exceptions import JSONDecodeError,ConnectionError,HTTPError
import os
import logging
from threading import Timer
from datetime import datetime, date

TRACTIVE_CLIENT = os.getenv("TRACTIVE_CLIENT",'')

account_details = {
    'email': os.getenv('TRACTIVE_USER',''),
    'password': os.getenv('TRACTIVE_PASSWORD','')
}


default_headers = {
        'X-Tractive-Client': TRACTIVE_CLIENT,
        # 'Authorization': f"Bearer {account_details.get('token', '')}",
        'Content-Type': 'application/json'
    }

logger = logging.getLogger(__name__)
logging.basicConfig(filename=f'{__name__}.log', encoding='utf-8', level=logging.DEBUG)
#Implement

class TractiveClient():
    def __init__(self,account_details,default_headers=default_headers):
        self.base_url = 'https://graph.tractive.com/4/'
        self.account_details = account_details
        self.headers = default_headers
        
    def join_url(self,path):
        '''
        Join base url
        '''
        if path[0] == '/':
            path = path[1:]
        return urljoin(self.base_url, path)
    def request(self,method='GET',url='',data={},headers={},**kwargs):
        '''
        Do all requests
        '''
        try:
            assert url != ''
            if not headers:
                headers = self.headers
            response = requests.request(method,url,data=data,headers=headers,**kwargs)
            response.raise_for_status()
            return response.json()
        except (JSONDecodeError,ConnectionError,HTTPError) as err:
            logger.exception(err)
    def authenticate(self):
        '''
        Authenticate account details storing access_token and user_id
        '''
        url = self.join_url('auth/token')
        payload = dict(grant_type='tractive',platform_email=self.account_details["email"],platform_token=self.account_details["password"])
        data = self.request('POST',url=url,params=payload)
        access_token = data['access_token']
        self.headers.update({'Authorization': f'Bearer {access_token}'})
        self.account_details['access_token'] = access_token
        self.account_details['user_id'] = data['user_id']
        self.account_details['expires_at'] = data['expires_at']
        self.account_details['expiration_timer'] = Timer(int(data['expires_at'])-5,self.authenticate)
    def authenticated(self):
        '''
        is authenticated
        '''
        return 'access_token' in self.account_details
    def create_user_url(self):
        '''
        Join base_url and user account_details for additional endpoints below
        '''
        return self.join_url(f'user/{self.account_details["user_id"]}/')
    def join_user_url(self,path):
        '''
        Join account related endpoints/paths
        '''
        return urljoin(self.create_user_url(),path)
    def get_account_info(self):
        '''
        Get account info using user_id
        '''
        url = self.create_user_url()
        return self.request(url=url)
    def get_account_subscriptions(self):
        '''
        Get all account subscriptions
        '''
        url = self.join_user_url('subscriptions')
        return self.request(url=url)
    def get_account_subscription(self,subscription_id):
        '''
        Get an account subscription by subscription_id
        '''
        url = self.join_user_url(f'subscription/{subscription_id}')
        return self.request(url=url)
    def get_account_shares(self):
        '''
        Get all account shares
        '''
        url = self.join_user_url('shares')
        return self.request(url=url)
    def get_all_trackers(self):
        '''
        Get all trackers by user_id
        '''
        url = self.join_user_url('trackers')
        return self.request(url=url)
    def get_tracker(self, tracker_id):
        '''
        Get a tracker by tracker_id
        '''
        url = self.join_url(f'tracker/{tracker_id}')
        return self.request(url=url)
    def get_tracker_history(self,tracker_id,start,end):
        '''
        Get tracker history for a given date range
        start and end are formatted as POSIX timestamps from date or datetime
        '''
        def to_timestamp(dt):
            if isinstance(dt,(datetime,date)):
                return f'{dt.timestamp():.0f}'
        url = self.join_url(f'tracker/{tracker_id}/positions')
        if not isinstance(start,str):
            start = to_timestamp(start)
        if not isinstance(end,str):
            end = to_timestamp(end)
        data = {'time_from' : start,
                'time_to' : end,
                'format' : 'json_segments'}
        return self.request(url=url,params=data)
    def get_tracker_location(self,tracker_id):
        '''
        Get tracker location including address
        '''
        url = self.join_url(f'device_pos_report/{tracker_id}')
        data = self.request(url=url)
        options = {'latitude' : data['latlong'][0],
                'longitude' : data['latlong'][1]}
        location_url = self.join_url('platform/geo/address/location')
        address = self.request(url=location_url,params=options).get('address')
        data['address'] = address
        return data
    def get_tracker_hardware(self,tracker_id):
        '''
        Get hardware infomation including battery level
        '''
        url = self.join_url(f'device_hw_report/{tracker_id}')
        return self.request(url=url)
    def get_tracker_battery(self,tracker_id):
        '''
        Get tracker battery level
        '''
        return self.get_tracker_hardware(tracker_id)['battery_level']
    def get_tracker_geo_fences(self,tracker_id):
        '''
        Get a trackers geo fences
        '''
        url = self.join_url(f'tracker/{tracker_id}/geofences')
        return self.request(url=url)
    def get_geo_fence(self,fence_id):
        '''
        Get a geo fence by fence_id
        '''
        url = self.join_url(f'geofence/{fence_id}')
        return self.request(url=url)
    def get_pet(self,pet_id):
        '''
        Get pet by pet_id adding profile link
        '''
        url = self.join_url(f'trackable_object/{pet_id}')
        data = self.request(url=url)
        data['details']['profile_picture_link'] = f"https://graph.tractive.com/4/media/resource/{data['details']['profile_picture_id']}.png"
        return data
    def get_pets(self):
        url = self.join_user_url('trackable_objects')
        return self.request(url=url)
    def live_tracking(self,tracker_id,on_off):
        '''
        Turn live tracking on or off 
        on_off = True turns on live tracking
        on_off = False turns off live tracking
        '''
        
        url = self.join_url(f"tracker/{tracker_id}/command/live_tracking/{'on' if on_off else 'off'}")
        return self.request(url=url)
    def led_light(self,tracker_id,on_off):
        '''
        Turn LED light on or off 
        on_off = True turns on the LED light
        on_off = False turns off the LED light
        '''
        
        url = self.join_url(f"tracker/{tracker_id}/command/led_control/{'on' if on_off else 'off'}")
        return self.request(url=url)
    def buzzer(self,tracker_id,on_off):
        '''
        Turn buzzer light on or off 
        on_off = True turns on the buzzer light
        on_off = False turns off the buzzer light
        '''
        
        url = self.join_url(f"tracker/{tracker_id}/command/buzzer_control/{'on' if on_off else 'off'}")
        return self.request(url=url)