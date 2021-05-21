from fastapi import APIRouter, Depends, HTTPException, status

from idp_schedule_provider.authentication import auth, schemas

router = APIRouter()


@router.post("/token", response_model=schemas.TokenResponseModal)
async def get_access_token(
    form_data: auth.OAuth2ClientCredentialsRequestForm = Depends(),
):
    """
    Provides an access token to the client providing credentials
    """

    # this is *not* a production ready implemention of JWT. It exists for testing purposes only
    # secure your application properly. We recommend tooling like Keycloak
    is_valid_client = auth.authenticate_client(form_data.client_id, form_data.client_secret)
    if not is_valid_client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client_id or client_secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth.create_token()
