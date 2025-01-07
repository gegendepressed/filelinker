from .consts import (
    PASSWORD_REQUIRED,
    ERROR_NOT_FOUND,
    WRONG_PASSWORD,
    WRONG_FOLDER,
    ERROR_EXPIRE,
    WRONG_OWNER,
)
from requests import RequestException, delete, post, put, get
from typing import Iterable, NoReturn, Literal
from hashlib import sha256
from random import choices
from .exceptions import (
    InvalidExpirationError,
    PasswordRequiredError,
    RequiresPremiumError,
    ContentNotFoundError,
    WrongPasswordError,
    WrongFolderError,
    WrongOwnerError,
)
from .exceptions import (
    UnknownResponseException,
    CannotReachAPIException,
    InvalidTokenException,
    ContentExpiredError,
    RateLimitException,
)


class GoFileSession:
    """Class for communicating with the GoFile API."""

    def __init__(
        self, max_retries: int = 5, raw_output: bool = False, token: str | None = None
    ) -> None:
        self.__max_retries = max_retries
        self.__retry_count = 0
        self.__raw = raw_output
        self.__token = token
        if token == None:
            self.__token = self.create_account()
        self.refresh_account_info()

    def get_server(self, raw: bool | None = None) -> str | dict:
        """raw: Return raw json."""
        if raw == None:
            raw = self.__raw
        try:
            response = get("https://api.gofile.io/getServer")
        except RequestException:
            self.__next_retry("while getting available server")
            return self.get_server(raw)
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return response_json["data"]["server"]
                elif status == "noServer":
                    self.__next_retry(
                        "no server was available, the gofile api is probably down, or under heavy load"
                    )
                    return self.get_server(raw=raw)
                else:
                    raise UnknownResponseException(
                        f"error while getting server, status: {status}"
                    )
            case _:
                raise UnknownResponseException(
                    f"error while getting server, status: {status}\nresponse code: {response.status_code}"
                )

    def upload_file(
        self,
        file_path: str,
        raw: bool | None = None,
        parent_folder_id: str | None = None,
        parent_folder_name: str | None = None,
        parent_folder_public: bool = True,
        parent_folder_password: str | None = None,
        expiration_timestamp: float | int | None = None,
        parent_folder_description: str | None = None,
        parent_folder_tags: Iterable[str] | None = None,
    ) -> dict:
        """file_path: The path to the file that will be uploaded.\n
        parent_folder_id: The parent folder ID. If None is given, a new folder is created to recieve the file.\n
        raw: Return raw json.\n
        parent_folder_name: The parent folder name. If None is given, a random name is generated.\n
        parent_folder_public: Should the parent folder be public for all users to see. Default is True.\n
        parent_folder_password: The password for the parent folder.\n
        expiration_timestamp: When the parent folder should expire, in unix-time.\n
        description: Description of the parent folder.\n
        tags: The tags for the parent folder.\n
        """
        if raw == None:
            raw = self.__raw
        if parent_folder_id == None:
            created_new_folder = True
            parent_folder_id = self.create_folder(
                folder_name=parent_folder_name,
                parent_folder_id=self.__root_folder,
                public=parent_folder_public,
                folder_password=parent_folder_password,
                expiration_timestamp=expiration_timestamp,
                description=parent_folder_description,
                tags=parent_folder_tags,
            )
        else:
            parent_folder_id = self.__root_folder
        payload = {"token": self.__token}
        payload["folderId"] = parent_folder_id
        with open(file_path, "rb") as file_opened:
            try:
                response = post(
                    f"https://{self.get_server()}.gofile.io/uploadFile",
                    data=payload,
                    files={"file": file_opened},
                )
            except RequestException:
                self.__next_retry(
                    f"while uploading file ({file_path}) to {parent_folder_id}"
                )
                return self.upload_file(
                    file_path=file_path,
                    raw=raw,
                    parent_folder_id=parent_folder_id,
                    parent_folder_name=parent_folder_name,
                    parent_folder_public=parent_folder_public,
                    parent_folder_password=parent_folder_password,
                    expiration_timestamp=expiration_timestamp,
                    parent_folder_description=parent_folder_description,
                    parent_folder_tags=parent_folder_tags,
                )
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    self.set_option(parent_folder_id, "public", parent_folder_public)
                    if parent_folder_password != None:
                        self.set_option(
                            parent_folder_id, "password", parent_folder_password
                        )
                    if expiration_timestamp != None:
                        self.set_option(
                            parent_folder_id, "expire", float(expiration_timestamp)
                        )
                    if parent_folder_tags != None:
                        self.set_option(parent_folder_id, "tags", parent_folder_tags)
                    if parent_folder_description != None:
                        self.set_option(
                            parent_folder_id, "description", parent_folder_description
                        )
                    if raw:
                        return response_json
                    return response_json["data"]
                elif status == WRONG_OWNER and not created_new_folder:
                    raise WrongOwnerError(f"you do not own {parent_folder_id}")
                else:
                    raise UnknownResponseException(
                        f"error while uploading file, status: {status}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while uploading file, status: {status}\nresponse code: {response.status_code}"
                )

    def get_content(
        self,
        content_id: str,
        folder_password: str | None = None,
        raw: bool | None = None,
    ) -> dict:
        """content_id: Content ID to get the contents of.\n
        folder_password: Password is only needed if you don't own the folder.\n
        raw: Return raw json."""
        if raw == None:
            raw = self.__raw
        params = {
            "token": self.__token,
            "contentId": content_id,
            "websiteToken": "7fd94ds12fds4",  # websiteToken up my ass bruhh
        }
        if folder_password != None:
            params["password"] = sha256(
                folder_password.encode()
            ).hexdigest()  # gofile uses client side hashing lol
        headers = {"Content-Type": "application/json"}
        try:
            response = get(
                "https://api.gofile.io/getContent", params=params, headers=headers
            )
        except RequestException:
            self.__next_retry(f"while getting contents of: {content_id}")
            return self.get_content(content_id=content_id, raw=raw)
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return response_json["data"]["contents"]
                elif status == PASSWORD_REQUIRED:
                    raise PasswordRequiredError(f"password required for {content_id}")
                elif status == WRONG_PASSWORD:
                    raise WrongPasswordError(
                        f"the password {folder_password} ({params['password']}) for {content_id} is wrong!"
                    )
                elif status == WRONG_OWNER:
                    raise WrongOwnerError(f"you do not own {content_id}")
                elif status == ERROR_EXPIRE:
                    raise ContentExpiredError(f"content id {content_id} has expired")
                else:
                    raise UnknownResponseException(
                        f"error while getting content(s) of {content_id}\nstatus: {status}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while getting content(s) of {content_id}\nresponse code: {response.status_code}"
                )

    def create_account(self, raw: bool | None = None) -> str:
        """raw: Return raw json."""
        if raw == None:
            raw = self.__raw
        try:
            response = get("https://api.gofile.io/createAccount")
        except RequestException:
            self.__next_retry("while creating account")
            return self.create_account(raw)
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return response_json["data"]["token"]
                else:
                    raise UnknownResponseException(
                        f"error while creating account, status: {status}"
                    )
            case 429:
                raise RateLimitException(
                    "rate limited (too many requests in a short period of time)"
                )
            case _:
                raise UnknownResponseException(
                    f"error while creating account, response code: {response.status_code}\nstatus: {status}"
                )

    def create_folder(
        self,
        raw: bool | None = None,
        folder_name: str | None = None,
        parent_folder_id: str | None = None,
        public: bool = True,
        folder_password: str | None = None,
        expiration_timestamp: float | int | None = None,
        description: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> str | dict:
        """folder_name: The folder name. If None is given, a random name is generated.\n
        parent_folder_id: The parent folder ID. If None is given, the root folder will be used.\n
        public: Should the folder be public for all users to see. Default is True.\n
        folder_password: The password for the folder.\n
        expiration_timestamp: When the folder should expire, in unix-time.\n
        description: Description of the folder.\n
        tags: The tags for the folder."""
        if raw == None:
            raw = self.__raw
        if parent_folder_id == None:
            parent_folder_id = self.__root_folder
        if folder_name == None:
            folder_name = "".join(choices("abcdefghijklmnopqrstuvwxyz1234567890", k=5))
        payload = {
            "token": self.__token,
            "folderName": folder_name,
            "parentFolderId": parent_folder_id,
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = put(
                "https://api.gofile.io/createFolder", json=payload, headers=headers
            )
        except RequestException:
            self.__next_retry(
                f"creating folder {folder_name}\nparent folder id: {parent_folder_id}"
            )
            return self.create_folder(
                raw=raw,
                folder_name=folder_name,
                parent_folder_id=parent_folder_id,
                public=public,
                folder_password=folder_password,
                expiration_timestamp=expiration_timestamp,
                description=description,
                tags=tags,
            )
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                content_id = response_json["data"]["id"]
                if status == "ok":
                    self.set_option(content_id, "public", public)
                    if folder_password != None:
                        self.set_option(content_id, "password", folder_password)
                    if expiration_timestamp != None:
                        self.set_option(
                            content_id, "expire", float(expiration_timestamp)
                        )
                    if tags != None:
                        self.set_option(content_id, "tags", tags)
                    if description != None:
                        self.set_option(content_id, "description", description)
                    if raw:
                        return response_json
                    return content_id
                elif status == WRONG_FOLDER:
                    raise WrongFolderError(f"invalid parent folder: {parent_folder_id}")
                else:
                    raise UnknownResponseException(
                        f"error while creating folder {folder_name}\nparent folder id: {parent_folder_id}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while creating folder {folder_name}\nparent folder id: {parent_folder_id}\nresponse code: {response.status_code}"
                )

    def get_account_details(self, raw: bool | None = None) -> dict:
        """raw: return raw json"""
        if raw == None:
            raw = self.__raw
        params = {"token": self.__token}
        headers = {"Content-Type": "application/json"}
        try:
            response = get(
                "https://api.gofile.io/getAccountDetails",
                params=params,
                headers=headers,
            )
        except RequestException:
            self.__next_retry(
                f"while getting account details for token: {params['token']}"
            )
            return self.get_account_details(raw=raw)
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return response_json["data"]
                else:
                    raise UnknownResponseException(
                        f"error while getting account details for token: {params['token']}\nstatus: {status}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while getting account details for token: {params['token']}\nstatus: {status}\nresponse code: {response.status_code}"
                )

    def copy_content(
        self, sources: Iterable[str], destination: str, raw: bool | None = None
    ) -> None | dict:
        """sources: Iterable of source content IDs\n
        destination: Content ID of destination folder\n
        raw: Return raw json"""
        if not self.is_premium:
            raise RequiresPremiumError(
                "this api endpoint requires the premium gofile api"
            )
        if raw == None:
            raw = self.__raw
        sources_string = ",".join(sources)
        payload = {
            "token": self.__token,
            "contentsId": sources_string,
            "folderIdDest": destination,
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = put(
                "https://api.gofile.io/copyContent", json=payload, headers=headers
            )
        except RequestException:
            self.__next_retry(
                f"while copying content from {sources_string} to {destination}"
            )
            return self.copy_content(sources=sources, destination=destination, raw=raw)
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return
                elif status == WRONG_FOLDER:
                    raise WrongFolderError(
                        f"invalid folder, the api does not say which one"
                    )
                elif status == WRONG_OWNER:
                    raise WrongOwnerError(f"you do not own {destination}")
                else:
                    raise UnknownResponseException(
                        f"error while copying content from {sources_string} to {destination}\nstatus: {status}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while copying content from {sources_string} to {destination}\nstatus: {status}\nresponse code: {response.status_code}"
                )

    def delete_content(
        self, targets: Iterable[str], raw: bool | None = None
    ) -> None | dict:
        """sources: Iterable of source content IDs\n
        raw: Return raw json"""
        if raw == None:
            raw = self.__raw
        targets_string = ",".join(targets)
        payload = {
            "token": self.__token,
            "contentsId": targets_string,
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = delete(
                "https://api.gofile.io/deleteContent", json=payload, headers=headers
            )
        except RequestException:
            self.__next_retry(f"while deleting content from {targets_string}")
            return self.delete_content(targets=targets, raw=raw)
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return
                elif status == WRONG_FOLDER:
                    raise WrongFolderError(
                        f"invalid folder, the api does not say which one"
                    )
                elif status == WRONG_OWNER:
                    raise WrongOwnerError(f"you do not own {targets_string}")
                elif status == ERROR_NOT_FOUND:
                    raise ContentNotFoundError(
                        f"content ids {', '.join(list(response_json['data'].keys()))} not found"
                    )
                else:
                    raise UnknownResponseException(
                        f"error while deleting content {targets_string}\nstatus: {status}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while deleting content {targets_string}\nstatus: {status}\nresponse code: {response.status_code}"
                )

    def set_option(
        self,
        content_id: str,
        option_type: Literal[
            "public", "password", "description", "expire", "tags", "directLink"
        ],
        value: bool | str | int | Iterable[str],
        raw: bool | None = None,
    ) -> None:
        """If option_type is "public", value must be a `bool`, and the content_id must be a folder.\n
        If option_type is "password", value must be a `str`, and the content_id must be a folder.\n
        If option_type is "description", value must be a `str`, and the content_id must be a folder.\n
        If option_type is "expire", value must be an `int`, and the content_id must be a folder.\n
        If option_type is "tags", value must be an `Iterable[str]`, and the content_id must be a folder.\n
        If option_type is "directLink", value must be a `bool`, and the content_id must be a file.\n

        raw: Return raw json
        """
        original_value = value
        if raw == None:
            raw = self.__raw
        if option_type in ("public", "directLink"):
            if value:
                value = "true"
            else:
                value = "false"
        if option_type == "tags":
            value = ",".join(original_value)
        payload = {
            "token": self.__token,
            "contentId": content_id,
            "option": option_type,
            "value": value,
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = put(
                "https://api.gofile.io/setOption", json=payload, headers=headers
            )
        except RequestException:
            self.__next_retry(
                f"setting option for content id/response status: {content_id}"
            )
            return self.set_option(
                content_id=content_id,
                option_type=option_type,
                value=original_value,
                raw=raw,
            )
        self.__reset_retry_count()
        response_json: dict = response.json()
        status = response_json.get("status")
        match response.status_code:
            case 200:
                if status == "ok":
                    if raw:
                        return response_json
                    return
                elif status == WRONG_OWNER:
                    raise WrongOwnerError(f"you do not own {content_id}")
                elif status == ERROR_EXPIRE:
                    raise InvalidExpirationError(
                        f"the expiration time {original_value} is not valid"
                    )
                else:
                    raise UnknownResponseException(
                        f"error while setting option for content id: {content_id}\nstatus: {status}"
                    )
            case 401 | 403:
                raise InvalidTokenException("invalid token")
            case _:
                raise UnknownResponseException(
                    f"error while setting option for content id: {content_id}\nstatus: {status}\nstatus code: {response.status_code}"
                )

    def set_token(self, new_token: str) -> None:
        self.__token = new_token
        self.refresh_account_info()

    def reset_account(self) -> None:
        self.__token = self.create_account()
        self.refresh_account_info()

    def refresh_account_info(self) -> None:
        account_details = self.get_account_details()
        self.__root_folder: str = account_details["rootFolder"]
        self.__tier: str = account_details["tier"]

    def set_default_raw(self, new_raw: bool) -> None:
        self.__raw = new_raw

    def __reset_retry_count(self) -> None:
        self.__retry_count = 0

    def __increase_retry_count(self, amount: int = 1) -> None:
        self.__retry_count += amount

    def __next_retry(self, while_doing: str | None = None) -> None:
        if self.__retry_count == self.__max_retries:
            self.__reset_retry_count()
            self.__raise_max_retries(while_doing)
        self.__increase_retry_count()

    @staticmethod
    def __raise_max_retries(while_doing: str | None = None) -> NoReturn:
        if while_doing == None:
            raise CannotReachAPIException("max retries hit")
        raise CannotReachAPIException("max retries hit while " + while_doing)

    @property
    def max_retries(self) -> int:
        return self.__max_retries

    @property
    def token(self) -> str:
        return self.__token

    @property
    def root_folder(self) -> str:
        return self.__root_folder

    @property
    def raw(self) -> bool:
        return self.__raw

    @property
    def tier(self) -> str:
        return self.__tier

    @property
    def is_guest(self) -> bool:
        return self.__tier == "guest"

    @property
    def is_standard(self) -> bool:
        return self.__tier == "standard"

    @property
    def is_premium(self) -> bool:
        return self.__tier == "premium"
