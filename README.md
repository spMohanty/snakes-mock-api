# Snakes Mock API


# Installation

```
git clone git@github.com:spMohanty/snakes-mock-api.git
cd snakes-mock-api
pip install -r requirements.txt
cp config.py.example config.py

# In a separate tab
# Start Redis Server
redis-server

#In a separate tab
python worker.py

# In a separate tab
python app.py

```

# Usage
## Enqueue Image for Prediction
```
curl -X GET http://localhost:3001/enqueue/<image_url>
```
for example : 
```
curl -X GET http://localhost:3001/enqueue/https://cms.qz.com/wp-content/uploads/2019/02/RTXLA3F-e1551362816993.jpg
```

### response
```
{
  "api_version": 0.1,
  "image_id": "e2fafa4c692058b2da04b3d84988fa70",
  "response_channel": "aicrowd-snakes-api::RESPONSE",
  "status": "AICROWD_SNAKES_API.IMAGE_ENQUEUED"
}
```

## Check status of processing using GET
```
curl -X GET http://localhost:3001/status/<image_id>
```
for example : 
```
curl -X GET http://localhost:3001/status/e2fafa4c692058b2da04b3d84988fa70
```

### response
```
{
  "api_version": 0.1,
  "image_id": "e2fafa4c692058b2da04b3d84988fa70",
  "result": {
    "confidence": [
      0.9996096525547743,
      0.9982541591681338,
      0.9981244171578539,
      0.9966792734893344,
      0.9953320812024775
    ],
    "predictions": [
      "thamnophis-validus",
      "philodryas-chamissonis",
      "leptophis-ahaetulla",
      "crotalus-ravus",
      "bothriechis-marchi"
    ]
  },
  "status": "AICROWD_SNAKES_API.IMAGE_PROCESSED"
}
```

Ensure that you have a `redis-server` running in the background at the appropriate location (as specified in `config.py`)

# Author
Sharada Mohanty 
