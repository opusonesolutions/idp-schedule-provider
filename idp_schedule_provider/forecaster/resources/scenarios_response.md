Gets all scenarios currently available from the schedule provider.

## Use Case
This operation will be used to allow the user to choose between multiple scenarios available.
It is required that there will always be 1 or more scenarios.

## General Requirements and Guidelines

<details>

### Performance Guidelines
This endpoint is used exclusively for user interface interactions.
If responses are slow, the user interface will be slow so our expectation is the
target response time should be under 1 second for these requests.

</details>
