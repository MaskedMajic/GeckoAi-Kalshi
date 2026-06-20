import os
import time
import base64
import requests

from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding


load_dotenv()

HOST = "https://external-api.kalshi.com"

KEY_ID = os.getenv(
    "KALSHI_KEY_ID"
)

PRIVATE_KEY_PATH = os.getenv(
    "KALSHI_PRIVATE_KEY_PATH"
)


def load_key():

    with open(
        PRIVATE_KEY_PATH,
        "rb"
    ) as f:

        return load_pem_private_key(
            f.read(),
            password=None
        )


def sign(
    private_key,
    timestamp,
    method,
    path
):

    message = (
        f"{timestamp}"
        f"{method}"
        f"{path}"
    ).encode()

    signature = (
        private_key.sign(

            message,

            padding.PSS(

                mgf=padding.MGF1(
                    hashes.SHA256()
                ),

                salt_length=padding.PSS.DIGEST_LENGTH
            ),

            hashes.SHA256()

        )
    )

    return (
        base64
        .b64encode(
            signature
        )
        .decode()
    )


def get_headers(
    method,
    path
):

    timestamp = str(
        int(
            time.time()
            *
            1000
        )
    )

    key = (
        load_key()
    )

    signature = (
        sign(
            key,
            timestamp,
            method,
            path
        )
    )

    return {

        "KALSHI-ACCESS-KEY":
            KEY_ID,

        "KALSHI-ACCESS-TIMESTAMP":
            timestamp,

        "KALSHI-ACCESS-SIGNATURE":
            signature
    }


def test():

    method = "GET"

    path = (
        "/trade-api/v2/"
        "portfolio/balance"
    )

    url = (
        HOST
        +
        path
    )

    response = requests.get(
        url,
        headers=get_headers(
            method,
            path
        ),
        timeout=10
    )

    print()

    print(
        "STATUS:",
        response.status_code
    )

    print()

    try:

        print(
            response.json()
        )

    except:

        print(
            response.text
        )


if __name__ == "__main__":

    test()