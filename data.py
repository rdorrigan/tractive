import pandas as pd
from datetime import datetime
import folium
def clean_tracker_history(tracker_id,history):
    '''
    clean the tracker history from the TractiveClient.get_tracker_history method
    '''
    df = pd.concat([pd.DataFrame(x) for x in history],sort=False)
    ll = df['latlong'].tolist()
    df[['latitude','longitude']] = pd.DataFrame(ll,index=df.index)#.drop(columns=['latlong'])
    df['tracker'] = tracker_id
    df['datetime'] = [datetime.fromtimestamp(t) for t in df['time']]
    cols = ['tracker','time','datetime','alt','speed','course','sensor_used','latitude','longitude']
    return df[cols]

def plot_tracker_history(pet_history,custom_icon=False):
    '''
    clean_history should be a list of tuples: pet, url image for the CustomIcon, DataFrame
    url is only needed if custom_icon is True and must be png
    '''
    icon_colors = 'red, blue, green, purple, orange, darkred, lightred, beige, darkblue, darkgreen, cadetblue, darkpurple, white, pink, lightblue, lightgreen, gray, black, lightgray'.split(', ')

    # Add points to the map
    marker_locations = []
    i = 0
    for pet,url,df in pet_history:
        if not marker_locations:
            fm = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=5)
        icon = folium.Icon(color=icon_colors[i])
        for lat,lon in df[['latitude','longitude']].itertuples(index=None,name=None):
            location = [lat,lon]
            marker_locations.append(location)
            if custom_icon:
                # Not recommended with more than a few dozen markers
                icon = folium.CustomIcon(url)
            folium.Marker(location, popup=f"({lat}, {lon})",icon=icon).add_to(fm)
        i += 1

    # Auto-zoom to fit all markers
    fm.fit_bounds(marker_locations)
    return fm
def save_tracker_history(history):
    import json
    with open('tracker_history.json','w') as f:
        json.dump(history,f)