A Python API wrapper of the Tractive Pet GPS tracker influenced by  
https://github.com/FAXES/tractive  
https://github.com/dominique-boerner/unofficial-tractive-rest-api  
https://github.com/zhulik/aiotractive  

## Getting Started Example  

```python
from tractive import account_details,TractiveClient as TC
client = TC(account_details)
trackers = client.get_trackers()
pet_ids = client.get_pets()
pets = [client.get_pet(p['_id']) for p in pet_ids]
from datetime import datetime, timedelta
start = datetime.now() - timedelta(days=1)
end = datetime.now()
pet_history = {}
for p in pets:
    pet_history[p['details']['name']] = client.get_tracker_history(p['device_id'],start,end)
```
