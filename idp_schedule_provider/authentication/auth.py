import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from fastapi import Depends, Form, HTTPException, Request, status
from fastapi.security.oauth2 import (
    OAuth2,
    OAuthFlowsModel,
    get_authorization_scheme_param,
)

from idp_schedule_provider import config
from idp_schedule_provider.authentication import schemas

settings: config.Settings = config.get_settings()


class Oauth2ClientCredentials(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(clientCredentials={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=False)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            return None
        return param


oauth2_scheme = Oauth2ClientCredentials(tokenUrl="token")


class OAuth2ClientCredentialsRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="client_credentials"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


def authenticate_client(client_id: Optional[str], client_secret: Optional[str]) -> bool:
    return client_id in settings.jwt_clients and settings.jwt_clients[client_id] == client_secret


def validate_token(token: Optional[str] = Depends(oauth2_scheme)) -> bool:
    if os.environ.get("AUTH") == "TRUE":
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            try:
                jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from e

    return True


def create_token() -> schemas.TokenResponseModal:
    expiry = datetime.utcnow() + timedelta(days=1)
    token = jwt.encode({"exp": expiry}, settings.jwt_secret_key, settings.jwt_algorithm)
    return schemas.TokenResponseModal(
        access_token=token,
        token_type="Bearer",
    )
