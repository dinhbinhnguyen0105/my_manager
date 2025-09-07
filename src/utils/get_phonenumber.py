import threading, time, sys
from queue import Queue
from typing import Optional, Dict, List
import io, pycurl, json
from urllib.parse import urljoin, urlencode


class RequestViotp:
    """
    Client for interacting with the Viotp API.

    This class provides methods to retrieve account balance,
    list available services, get service IDs, request phone numbers for services,
    and poll for OTP codes. It handles API requests using pycurl for efficient
    HTTP communication.
    """

    def __init__(self, token: str = None):
        """
        Initializes the RequestViotp client.

        Args:
            token (str, optional): The authentication token for the Viotp API.
                                   Raises ValueError if None or empty.
        """
        self._params = {"token": token}
        self._base_url = "https://api.viotp.com"
        if not token:
            raise ValueError(f"Invalid token: {self._params.get('token')}")

    def get_account_balance(self) -> Optional[int]:
        """
        Retrieves the current account balance from the Viotp API.

        Returns:
            Optional[int]: The current balance as an integer if successful,
                           None otherwise.

        Raises:
            RequestViotpError: If the API call fails or returns an error status.
        """
        try:
            params = self._params.copy()
            url_api = self._RequestViotp__build_api_url("users/balance", params)
            response_data = self._RequestViotp__request(url_api)
            # Basic HTTP status code check
            if response_data.get("status_code") != 200:
                raise RequestViotpError(
                    response_data.get("message"),
                    response_data.get("status_code"),
                    response_data,
                )
            # Assuming API response structure includes 'data' key with 'balance'
            data = response_data.get("data", None)
            if data:
                return data.get("balance", None)
            return None
        except RequestViotpError as e:
            # Re-raise the custom exception for higher-level handling
            raise e

    def list_services(self) -> Optional[Dict]:
        """
        Lists all available services from the Viotp API.

        Returns:
            Optional[Dict]: A dictionary containing service data if successful,
                            None otherwise.
        Raises:
            RequestViotpError: If the API call fails or returns an error status.
        """
        try:
            params = self._params.copy()
            params.setdefault("country", "vn")  # Default to Vietnam services
            url_api = self._RequestViotp__build_api_url("service/getv2", params)
            response_data = self._RequestViotp__request(url_api)
            # Basic HTTP status code check
            if response_data.get("status_code") != 200:
                raise RequestViotpError(
                    response_data.get("message"),
                    response_data.get("status_code"),
                    response_data,
                )
            # Assuming API response structure includes 'data' key
            data = response_data.get("data", None)
            return data
        except RequestViotpError as e:
            # Re-raise the custom exception for higher-level handling
            raise e

    def get_service_id(self, service_name: str) -> int:
        """
        Retrieves the numerical ID for a given service name from the list of available services.

        Args:
            service_name (str): The human-readable name of the service (e.g., "facebook").

        Returns:
            int: The integer ID of the service if found, -1 otherwise.
        """
        list_service = self.list_services()
        if not list_service:
            return -1  # No services found at all
        target_service = next(
            (
                item
                for item in list_service
                if item.get("name", "").lower() == service_name.lower()
            ),
            None,
        )
        if target_service:
            return target_service.get("id")
        return -1  # Service name not found in the list

    def get_service(self, service_name: str) -> Optional[Dict]:
        """
        Requests a new phone number for a specified service to receive an OTP.

        This involves first getting the service ID, then requesting a number
        from the API.

        Args:
            service_name (str): The name of the service (e.g., "facebook").

        Returns:
            Optional[Dict]: A dictionary containing 'phone_number' and 'request_id'
                            if the request is successful, None otherwise.

        Raises:
            RequestViotpError: If the service ID cannot be retrieved or
                               if the API returns an error during the phone number request.
        """
        try:
            params = self._params.copy()
            service_id = self.get_service_id(service_name=service_name)
            if service_id == -1:  # Using -1 as sentinel for "not found"
                raise RequestViotpError(
                    message=f"Could not retrieve service ID for {service_name}"
                )
            params.setdefault("serviceId", service_id)
            url_api = self._RequestViotp__build_api_url("request/getv2", params)
            response_data = self._RequestViotp__request(url_api)

            # Check for HTTP status code errors as well as API-specific logical errors
            status_code = response_data.get("status_code")
            message = response_data.get("message")
            if status_code != 200:
                raise RequestViotpError(
                    message=message, error_code=status_code, error_data=response_data
                )
            # Assuming the API might return {"status": "error", "message": "..."} even with 200 OK
            if response_data.get("status") == "error":
                raise RequestViotpError(
                    message=response_data.get("message", "Unknown API logic error"),
                    error_code=response_data.get(
                        "code"
                    ),  # Assuming 'code' for API-specific error code
                    error_data=response_data,
                )

            data = response_data.get("data")
            if data:
                return {
                    "phone_number": f"+{data.get('countryCode')}{data.get('phone_number')}",
                    "request_id": data.get("request_id"),
                }
            return None
        except RequestViotpError as e:
            # Print the error for debugging/logging, then return None as per original flow
            print(e)
            return None

    def get_code(self, request_id: int) -> Optional[Dict]:
        """
        Retrieves the OTP code for a given request ID.
        This method typically needs to be called repeatedly until the OTP arrives.

        Args:
            request_id (int): The ID of the request for which to retrieve the OTP.

        Returns:
            Optional[Dict]: A dictionary containing 'status' (e.g., 1 for success, 2 for expired),
                            'phone_number', and 'code' (if status is 1). Returns None on error.

        Raises:
            RequestViotpError: If the API returns an error status or message.
        """
        try:
            params = self._params.copy()
            params.setdefault("requestId", request_id)
            url_api = self._RequestViotp__build_api_url("session/getv2", params)
            response_data = self._RequestViotp__request(url_api)

            # Check for HTTP status code errors
            if response_data.get("status_code") != 200:
                raise RequestViotpError(
                    response_data.get("message"),
                    response_data.get("status_code"),
                    response_data,
                )
            # Further check for API-specific logical errors
            if response_data.get("status") == "error":
                raise RequestViotpError(
                    message=response_data.get("message", "Unknown API logic error"),
                    error_code=response_data.get("code"),
                    error_data=response_data,
                )

            data = response_data.get("data", None)
            status = (
                data.get("Status") if data else None
            )  # Ensure data exists before accessing
            return (
                {
                    "status": status,
                    "phone_number": f"+{data.get('CountryCode')}{data.get('Phone')}",
                    "code": data.get("Code"),
                }
                if data
                else None
            )  # Return None if 'data' is missing
        except RequestViotpError as e:
            # Print the error for debugging/logging, then return None as per original flow
            print(e)
            return None

    def _RequestViotp__build_api_url(
        self, endpoint: str, params: Optional[Dict]
    ) -> str:
        """
        Constructs the full API URL, combining the base URL, endpoint, and URL-encoded query parameters.

        Args:
            endpoint (str): The specific API endpoint path (e.g., "users/balance").
            params (Optional[Dict]): A dictionary of key-value pairs for URL query parameters.
                                     These will be URL-encoded.

        Returns:
            str: The complete, URL-encoded API URL.
        """
        full_url = urljoin(self._base_url, endpoint)
        if params:
            # The token is part of _params and should be included in the URL for these calls.
            # Ensure it's passed with the specific calls if not global in __request headers.
            return f"{full_url}?{urlencode(params)}"
        return full_url

    def _RequestViotp__request(self, url: str) -> Dict:
        """
        Executes an HTTP GET request to the given URL using pycurl.

        This internal method handles the HTTP communication, raw response retrieval,
        JSON parsing, and basic error handling for network/JSON issues.

        Args:
            url (str): The full URL to send the request to.

        Returns:
            Dict: The parsed JSON response from the server.

        Raises:
            Exception: For pycurl network errors, invalid JSON responses,
                       or unhandled HTTP status codes (non-200).
                       Specific API logic errors (e.g., "status": "error" in JSON body)
                       should ideally be handled by higher-level methods calling this one,
                       or further refined error types can be raised here.
        """
        buffer = io.BytesIO()
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 60)  # Set connection timeout
        curl.setopt(pycurl.TIMEOUT, 60)  # Set total operation timeout
        headers = [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept: application/json, text/plain, */*",
            "Accept-Language: en-US,en;q=0.9",
            "Connection: keep-alive",
            f"Authorization: Bearer {self._params.get('token')}",  # IMPORTANT: Ensure token is sent here
        ]
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEFUNCTION, buffer.write)

        try:
            curl.perform()
            code = curl.getinfo(pycurl.RESPONSE_CODE)
            body = buffer.getvalue().decode("utf-8")

            # Attempt to parse JSON regardless of status code, as errors might be JSON too
            try:
                res = json.loads(body)
            except json.JSONDecodeError:
                # If it's not JSON, but not 200, raise a generic HTTP error
                if code != 200:
                    raise Exception(
                        f"HTTP Error {code}: Non-JSON response from {url}. Body: {body}"
                    )
                else:  # If 200 but not JSON, this is unexpected and likely an issue
                    raise Exception(
                        f"Unexpected non-JSON 200 OK response from {url}. Body: {body}"
                    )

            # If HTTP status code indicates an error (4xx or 5xx)
            if code >= 400:
                # Assuming 'message' is a common field for error details in JSON responses
                error_message = res.get(
                    "message", f"Unknown API error with status code {code}"
                )
                # This could be further refined to raise specific ViotpAPIError subclasses
                raise Exception(f"API Error {code}: {error_message} (URL: {url})")

            return res  # Return the parsed JSON response
        except pycurl.error as e:
            # Handles network-related errors originating from pycurl
            raise Exception(f"PycURL Error accessing {url}: {e}")
        except Exception as e:
            # Re-raise any other unexpected exceptions not caught specifically above
            raise Exception(f"An unexpected error occurred while requesting {url}: {e}")
        finally:
            curl.close()  # Always ensure the curl object is closed to release resources


class RequestViotpError(Exception):
    """
    Custom exception for Viotp API-specific errors.

    This exception is raised when the Viotp API returns an error response,
    allowing for structured error handling that includes the API's message,
    status code, and the raw error data. It inherits from Python's base Exception class.
    """

    def __init__(
        self, message: str, error_code: Optional[int], error_data: Optional[Dict]
    ):
        """
        Initializes a RequestViotpError instance.

        Args:
            message (str): A human-readable error message, typically derived from the API response.
            error_code (Optional[int]): An optional numerical error code (e.g., HTTP status code or API-specific code).
            error_data (Optional[Dict]): An optional dictionary containing the raw error data
                                         from the API response for detailed debugging.
        """
        super().__init__(message)
        self.error_code = error_code
        self.error_data = error_data

    def __str__(self):
        """
        Returns a human-readable string representation of the RequestViotpError.
        This method is called when the exception is converted to a string (e.g., by print()).
        """
        if self.error_code:
            return f"{self.__class__.__name__} [{self.error_code}]: {self.args[0]}"
        return f"{self.__class__.__name__}: {self.args[0]}"


def get_service_task(api_client: RequestViotp, service_name: str, result_queue: Queue):
    """
    Worker task to request a phone number for a specific service.
    The result (success status, request_id, phone_number) is put into a queue.

    Args:
        api_client (RequestViotp): An instance of the Viotp API client.
        service_name (str): The name of the service to request (e.g., "facebook").
        result_queue (Queue): A thread-safe queue to put the task results into.
                              Each item put into the queue is a dictionary indicating
                              success/failure and relevant data.
    """
    print(
        f"[{threading.current_thread().name}] Starting service info task for {service_name}..."
    )
    service = api_client.get_service(service_name=service_name)
    if service and service.get("request_id"):
        request_id = service.get("request_id")
        phone_number = service.get("phone_number")
        result = {
            "success": True,
            "service_name": service_name,
            "request_id": request_id,
            "phone_number": phone_number,
        }
        result_queue.put(result)
    else:
        # If service request failed or didn't return request_id
        print(
            f"[{threading.current_thread().name}] Failed to get service info or request ID for {service_name}."
        )
        result_queue.put(
            {
                "success": False,
                "service_name": service_name,
                "request_id": None,
                "phone_number": None,
            }
        )


def get_otp_task(
    api_client: RequestViotp,
    service_name: str,
    request_id: int,
    otp_queue: Queue,
):
    """
    Worker task to continuously poll for the OTP code for a given request ID.

    This task will repeatedly call the API's get_code endpoint until an OTP
    is received (status 1), the request expires (status 2), or an error occurs.
    Results are placed in the otp_queue.

    Args:
        api_client (RequestViotp): An instance of the Viotp API client.
        service_name (str): The name of the service (for logging purposes).
        request_id (int): The unique ID of the request for which to retrieve the OTP.
        otp_queue (Queue): A thread-safe queue to store the final OTP information.
    """
    print(
        f"[{threading.current_thread().name}] Starting OTP retrieval for {service_name} (Request ID: {request_id})..."
    )
    if not request_id:
        print(
            f"[{threading.current_thread().name}] Invalid Request ID for {service_name}. Cannot get OTP."
        )
        return  # Exit if no valid request_id provided

    while True:
        code_info = api_client.get_code(request_id)
        status = code_info.get("status") if code_info else None  # Safely get status

        if status == 1:  # OTP received successfully
            otp_queue.put(
                {
                    "code": code_info.get("code"),
                    "phone_number": code_info.get("phone_number"),
                    "service_name": service_name,  # Add service_name for context in final output
                    "request_id": request_id,
                    "status": "received",
                }
            )
            sys.stdout.write("\a")
            print(
                f"[{threading.current_thread().name}] OTP for {service_name}: {code_info.get('phone_number')} - {code_info.get('code')}"
            )
            break  # Exit loop once OTP is received
        elif status == 2:  # Phone number expired
            print(
                f"[{threading.current_thread().name}] Phone number {code_info.get('phone_number')} for {service_name} has expired."
            )
            # Optionally put an expired status into queue for main thread to handle
            otp_queue.put(
                {
                    "code": None,
                    "phone_number": code_info.get("phone_number"),
                    "service_name": service_name,
                    "request_id": request_id,
                    "status": "expired",
                }
            )
            break  # Exit loop as phone number expired
        else:  # OTP not yet available, waiting
            # print(
            #     f"[{threading.current_thread().name}] Waiting for OTP for {service_name}..."
            # )
            time.sleep(5)  # Wait before polling again


if __name__ == "__main__":
    # Check if the correct number of command-line arguments are provided
    if len(sys.argv) == 2:
        start_time = time.time()

        # Initialize the API client instance
        # IMPORTANT: Replace "d655ba7073214b0f95740a511864f1e7" with your actual Viotp API token
        api_client = RequestViotp("d655ba7073214b0f95740a511864f1e7")

        # Queues for inter-thread communication:
        # service_request_queue: Stores results from get_service_task (request_id, phone_number)
        # otp_queue: Stores final OTP results from get_otp_task
        service_request_queue = Queue()
        otp_queue = Queue()

        # List to hold references to service request threads
        service_threads: List[threading.Thread] = []

        # Get the number of service request threads from command-line arguments
        num_requests = int(sys.argv[1])
        print(
            f"[MainThread] Starting {num_requests} service request threads for Facebook..."
        )

        # Create and start threads to request phone numbers for the specified service
        for i in range(num_requests):
            service_thread = threading.Thread(
                target=get_service_task,
                args=(
                    api_client,
                    "facebook",
                    service_request_queue,
                ),  # Using "facebook" as example service
                name=f"FacebookServiceThread_{i}",  # Unique name for each service thread
            )
            service_threads.append(service_thread)
            service_thread.start()

        # Wait for all service request threads to complete their initial task
        print(f"[MainThread] Waiting for all service request threads to finish...")
        for service_thread in service_threads:
            service_thread.join()
        print(
            f"[MainThread] All service request threads completed. Processing results and starting OTP threads..."
        )

        # List to hold references to OTP retrieval threads
        otp_threads: List[threading.Thread] = []

        # Process results from service_request_queue and start OTP retrieval threads
        while not service_request_queue.empty():
            item = service_request_queue.get()
            service_name = item.get("service_name")

            if item.get("success"):
                request_id = item.get("request_id")
                phone_number = item.get("phone_number")
                print(
                    f"[MainThread] Obtained phone number: {phone_number} for {service_name} (Request ID: {request_id})"
                )

                # Create and start a new thread for each OTP retrieval
                otp_thread = threading.Thread(
                    target=get_otp_task,
                    args=(api_client, service_name, request_id, otp_queue),
                    # Using request_id in thread name for uniqueness and traceability
                    name=f"{service_name.capitalize()}OTPThread_ReqID_{request_id}",
                )
                otp_threads.append(otp_thread)
                otp_thread.start()
            else:
                print(
                    f"[MainThread] Skipping OTP task for {service_name} due to missing Request ID (Service request failed)."
                )

        # Wait for all OTP retrieval threads to complete
        print("[MainThread] Waiting for all OTP retrieval threads to finish...")
        for otp_thread in otp_threads:
            otp_thread.join()
        print(
            "[MainThread] All OTP retrieval threads completed. Collecting final results..."
        )

        # Print all collected OTPs from the otp_queue
        while not otp_queue.empty():
            item = otp_queue.get()
            print(f"[MainThread] Final Collected OTP result: {item}")

        end_time = time.time()
        print(f"\nAll tasks completed in {end_time - start_time:.2f} seconds.")

    else:
        # Provide usage instructions if command-line arguments are incorrect
        print("Usage: python get_phonenumber.py <number_of_threads>")
