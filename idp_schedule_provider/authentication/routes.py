from fastapi import APIRouter, Depends, HTTPException, status

from idp_schedule_provider.authentication import auth, schemas

router = APIRouter()


@router.post("/token", response_model=schemas.TokenResponseModal, tags=["spec-optional"])
async def get_access_token(
    form_data: auth.OAuth2ClientCredentialsRequestForm = Depends(),
) -> schemas.TokenResponseModal:
    """
    Provides an access token to the client providing credentials.

    ## Use Case
    This is part of the external schedule provider specification but is optional. If you do not
    need to secure your endpoint for public use (eg. on prem deployments), this is not necessary.

    ## WARNING
    The implementation included in this reference implementation is NOT recomended.
    It exists for testing and reference purposes only. We recommend an external
    JWT provider like Keycloak, short lived tokens and token validation for a
    secure implementation.
    """
    is_valid_client = auth.authenticate_client(form_data.client_id, form_data.client_secret)
    if not is_valid_client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client_id or client_secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth.create_token()
