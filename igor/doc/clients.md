# Clients

## Flow

Client process could be anything that can handle websockets, likely a browser based app. The flow of using Igor backend is following:

#### 1. Connecting to server via ws://127.0.0.1:5678

> When connectoin is established server will automaticly give your client and id (numeric). If you want to change it see step 2


#### 2. Setting custom client id (Optional)

  If you would like to set your client your own id you cant dispach action: `introduce_self` with data:
```json
    {
      "client_id": "myClientId"
    }
```