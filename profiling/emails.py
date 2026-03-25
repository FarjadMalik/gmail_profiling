import base64

from bs4 import BeautifulSoup
from typing import List, Optional, Callable, Dict, Any, Union, Tuple
from email.utils import getaddresses
from googleapiclient.http import BatchHttpRequest

from .utils import _decode_base64url



class Emails:
    """
    Gmail analysis by Label using Gmail API.

    Requires an authenticated Gmail API service passed in constructor.
    """

    def __init__(self, service):
        """
        Initialize with an authenticated Gmail API service instance.

        Args:
            service: Google Gmail API service instance.
        """
        self.service = service

    def get_all_labels(self):
        """
        List all labels in the user's Gmail account.

        Returns:
            list of dict: Each dict contains label 'id' and 'name'.
        """
        response = self.service.users().labels().list(userId='me').execute()
        return response.get('labels', [])

    def get_label_id(self, label_name):
        """
        Get the Gmail label ID for a given label name.

        Args:
            label_name (str): The display name of the label to find.

        Returns:
            str or None: Label ID if found, else None.
        """
        labels = self.get_all_labels()
        for label in labels:
            if label.get('name') == label_name:
                return label.get('id')
        return None
    
    def get_email_metadata(self, message_id, metadata_headers=['From', 'Subject', 'Date']):
        """
        Fetch sender, subject, and date metadata of an email message.

        Args:
            message_id (str): Email message ID.
            metadata_headers (list of str): List of headers to fetch, e.g. ['From', 'Subject', 'Date'].
                                            If None, defaults to ['From', 'Subject', 'Date'].

        Returns:
            dict: Metadata dict with keys 'from', 'subject', 'date'.
        """
        message = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='metadata',
            metadataHeaders=metadata_headers # ['From', 'Subject', 'Date']
        ).execute()

        metadata_dict = {}
        headers = message.get('payload', {}).get('headers', [])
        if not headers:
            # For some rare cases, headers could be inside parts (multipart message)
            parts = message.get('payload', {}).get('parts', [])
            for part in parts:
                part_headers = part.get('headers', [])
                for header in part_headers:
                    name = header.get('name', '').lower()
                    value = header.get('value', '')
                    metadata_dict.setdefault(name, []).append(value)
        

        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            metadata_dict.setdefault(name, []).append(value)

        return metadata_dict

    def batch_get_metadata(
        self,
        message_ids: List[str],
        metadata_headers: List[str] = ['From', 'Subject', 'Date'],
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Fetch metadata for multiple messages in batch *and return* a dictionary of results.

        Args:
            message_ids: List of Gmail message IDs.
            metadata_headers: List of headers to fetch.

        Returns:
            Dict mapping message ID to its metadata dict.
            Example:
            {
                'message_id_1': {'from': ['example@example.com'], 'subject': ['Hello'], ... },
                'message_id_2': {...},
                ...
            }
        """
        print(f"Fetching metadata for {len(message_ids)} messages with headers: {metadata_headers}")
        results: Dict[str, Dict[str, List[str]]] = {}
        errors: Dict[str, Exception] = {}

        def handle_metadata_callback(request_id: str, response: Any, exception: Optional[Exception]) -> None:
            metadata_dict: Dict[str, List[str]] = {}
            print(f"Processing response for message ID: {request_id}")
            if exception:
                errors[request_id] = exception
                results[request_id] = metadata_dict
                print(f"Error fetching metadata for {request_id}: {metadata_dict} : {exception}")
                return

            headers = response.get('payload', {}).get('headers', [])
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                if name in [h.lower() for h in metadata_headers]:
                    metadata_dict.setdefault(name, []).append(value)

            results[request_id] = metadata_dict

        batch = self.service.new_batch_http_request(callback=handle_metadata_callback)

        for msg_id in message_ids:
            batch.add(
                self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='metadata',
                    metadataHeaders=metadata_headers
                ),
                request_id=msg_id
            )
        batch.execute()

        # Optionally handle or raise errors here:
        if errors:
            print(f"Errors occurred for message IDs: {list(errors.keys())}")

        return results


    def _extract_parts(self, parts: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """
        Recursively walk MIME parts to extract plain text and HTML parts.

        Args:
            parts: List of MIME parts.

        Returns:
            Tuple of two lists: (plain_text_parts, html_parts)
        """
        text_parts = []
        html_parts = []

        for part in parts:
            mime_type = part.get('mimeType', '')
            body = part.get('body', {})
            data = body.get('data')
            if 'parts' in part:
                sub_text, sub_html = self._extract_parts(part['parts'])
                text_parts.extend(sub_text)
                html_parts.extend(sub_html)

            if data:
                decoded = _decode_base64url(data)
                if mime_type == 'text/plain':
                    text_parts.append(decoded)
                elif mime_type == 'text/html':
                    html_parts.append(decoded)

        return text_parts, html_parts
    
    def get_email_body(self, message_id=None) -> str:
        """
        Extract the best available email body from a message.

        Args:
            message_id (str): ID of the email message.

        Returns:
            str: Email body as plain text (empty string if none found).
        """
        if not message_id:
            return ''
        # Fetch the full message with all parts
        message = self.service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()

        payload = message.get('payload', {})

        text_parts = []
        html_parts = []

        if 'parts' in payload:
            text_parts, html_parts = self._extract_parts(payload['parts'])
        else:
            body = payload.get('body', {})
            data = body.get('data')
            mime_type = payload.get('mimeType', '')
            if data:
                decoded = _decode_base64url(data)
                if mime_type == 'text/plain':
                    text_parts.append(decoded)
                elif mime_type == 'text/html':
                    html_parts.append(decoded)

        if text_parts:
            return '\n'.join(text_parts).strip()

        if html_parts:
            combined_html = '\n'.join(html_parts)
            soup = BeautifulSoup(combined_html, 'html.parser')
            return soup.get_text(separator='\n').strip()

        return ''  # No readable content found


    def batch_get_email_bodies(
        self,
        message_ids: List[str],
        callback: Optional[Callable[[str, str, Optional[Exception]], None]] = None,
    ) -> Dict[str, Union[str, Exception]]:
        """
        Batch fetch and extract email bodies from multiple message IDs.

        Args:
            message_ids: List of Gmail message IDs.
            callback: Optional function called for each message with signature
                    (message_id, email_body, exception).
                    If no callback is provided, results are still collected and returned.

        Returns:
            Dict mapping message ID to extracted body string or Exception if error occurred.
        """
        results: Dict[str, Union[str, Exception]] = {}

        def batch_callback(request_id: str, response: Dict[str, Any], exception: Optional[Exception]) -> None:
            if exception:
                results[request_id] = exception
                if callback:
                    callback(request_id, '', exception)
                return

            try:
                body_text = self._extract_email_body_from_response(response)
                results[request_id] = body_text
            except Exception as e:
                results[request_id] = e
                if callback:
                    callback(request_id, '', e)
                return

            if callback:
                body = results[request_id]
                if isinstance(body, str):
                    callback(request_id, body, None)
                else:
                    callback(request_id, '', None)

        batch = self.service.new_batch_http_request(callback=batch_callback)

        for msg_id in message_ids:
            batch.add(
                self.service.users().messages().get(userId='me', id=msg_id, format='full'),
                request_id=msg_id,
            )

        batch.execute()

        return results
    
    def _extract_email_body_from_response(self, message: Dict[str, Any]) -> str:
        """
        Internal helper to extract body text from a message resource.

        Args:
            message: Gmail message resource.

        Returns:
            Extracted plain text body.
        """
        payload = message.get('payload', {})
        text_parts, html_parts = [], []

        if 'parts' in payload:
            text_parts, html_parts = self._extract_parts(payload['parts'])
        else:
            body = payload.get('body', {})
            data = body.get('data')
            mime_type = payload.get('mimeType', '')
            if data:
                decoded = _decode_base64url(data)
                if mime_type == 'text/plain':
                    text_parts.append(decoded)
                elif mime_type == 'text/html':
                    html_parts.append(decoded)

        if text_parts:
            return '\n'.join(text_parts).strip()

        if html_parts:
            combined_html = '\n'.join(html_parts)
            soup = BeautifulSoup(combined_html, 'html.parser')
            return soup.get_text(separator='\n').strip()

        return ''
        
    @staticmethod
    def extract_email_addresses(header_value):
        """
        Parse a header containing one or multiple email addresses.

        Args:
            header_value (str): Raw header string, e.g. From, To, Cc.

        Returns:
            list of str: List of email addresses in lowercase.
        """
        if not header_value:
            return []
        # If header_value is a list of strings, join it into a single string
        if isinstance(header_value, list):
            header_value = ', '.join(header_value)
        pairs = getaddresses([header_value])
        # getaddresses returns list of (name, email)
        emails = [email.lower() for _, email in pairs if email]
        return emails
    
