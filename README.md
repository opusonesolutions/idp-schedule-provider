# IDP Schedule Provider

A service which provides external schedules for consumption in IDP.


## Requirements

* Python 3.7.1 or greater
* Poetry

## Quickstart
```bash
poetry install
poetry run uvicorn idp_schedule_provider.main:app
```

### Using Seed Data
1. Navigate to http://localhost:8000/docs
2. Click on the `seed_data` api route
3. Click on `Try it out`
4. Click `Execute`

It will take 5-10 seconds for the API call to complete and afterwars there will be a
sqlite database created in the project directory (forecast_data.db).
This database is rebuilt everytime the application restarts so you will need to reseed the test
data everytime you restart the service.

At the time of writing this the database is getting seeded with the following test data

| Scenario id | Data Start | Data End | Assets | Notes |
| - | - | - | - | - |
| sce1 | 2000-01-01T00:00:00Z | 2000-12-31T23:59:59Z | asset_1, asset_2, asset_3 | |
| sce2 | N/A | N/A | N/A | sce2 is empty |


### Using JWT Auth
to enable the JWT Auth the environment variable `AUTH` should be set to true.

The 3 forecaster APIs will then require a JWT token to be included in the authorization header.

```bash
AUTH=TRUE poetry run uvicorn idp_schedule_provider.main:app
```

You can get a JWT token by sending a post request to the token endpoint with the 
client_id and client_secret. This is a very insecure implementation of JWT and exists
solely for testing purposes.
```
POST https://localhost:8000/token
Content-Type: application/x-www-form-urlencoded

client_id=gridos
client_secret=gridos_pw
```

and subsequent requests should include the token response in the authorization header
```
GET http://localhost:8000/scenario
Content-Type: application/json
Authorization: Bearer <JWT Token>

```
