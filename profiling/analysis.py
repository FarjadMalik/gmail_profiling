import time

from datetime import date, timedelta
from typing import List, Optional, Union, Tuple, Set
from .utils import _decode_base64url, _build_date_range_query, _to_date

from .emails import Emails


def list_email_ids(service, query: Optional[str] = None, label_ids: Optional[List[str]] = None, sender: Optional[Union[str, List[str]]] = None,
                       start_date: Optional[Union[date, str]] = None, end_date: Optional[Union[date, str]] = None, max_results: int = 1000):
        """
        List Gmail messages filtered by labels, sender(s), date, and/or additional query.
        
        Args:
            service: Authenticated Gmail API service instance.
            query: Optional, Gmail API query string.
            label_ids: Optional, List of Gmail label IDs.
            sender: Optional, Single email or list of sender emails.
            start_date: Optional, Inclusive start date (date or parseable string).
            end_date: Optional, Exclusive end date (date or parseable string).
            max_results: Optional, Max number of email messages to return.

        Returns:
            List of message dicts (each with 'id' and 'threadId').
        """
        if service is None:
            raise ValueError("Gmail service must be provided")
        
        # Build query components
        query_parts = []
        
        # Convert dates
        start = _to_date(start_date)
        end = _to_date(end_date)
        if start and end and start >= end:
            raise ValueError("start_date must be before end_date")
        
        # Date range part
        date_query = _build_date_range_query(start, end)
        if date_query:
            query_parts.append(date_query)

        # Sender part
        if sender:
            if isinstance(sender, str):
                sender_emails = [sender]
            else:
                sender_emails = sender

            # Build sender query with OR
            sender_query = " OR ".join(f"from:{email.strip().lower()}" for email in sender_emails if email)
            if sender_query:
                query_parts.append(f"({sender_query})")

        # Additional user query part
        if query:
            query_parts.append(query.strip())

        # Combine all query parts into one query string
        combined_query = " ".join(query_parts) if query_parts else None

        # Paginate and collect messages
        messages = []
        per_request_max = 500  # Gmail API max results per request

        request = service.users().messages().list(
            userId='me',
            labelIds=label_ids,
            q=combined_query,
            maxResults=min(max_results, per_request_max)
        )

        while request and len(messages) < max_results:
            response = request.execute()
            new_msgs = response.get('messages', [])
            messages.extend(new_msgs)
            # Check if there is a next page of results
            # and if we haven't reached the max_results limit  
            if 'nextPageToken' in response and len(messages) < max_results:
                request = service.users().messages().list_next(request, response)
            else:
                request = None

        return messages[:max_results]


def unique_senders_per_date(service, target_date) -> Tuple[int, Set[str]]:
    """
    Counts emails on a specific date and returns unique senders.

    Args:
        service: Authenticated Gmail API service instance.
        target_date: date or str representing the date to count emails for.

    Returns:
        Tuple:
            total count of emails received on that date,
            set of unique sender email addresses.
    """
    # Normalize date and define date range (inclusive start, exclusive end)
    from_date = _to_date(target_date)
    if not from_date:
        raise ValueError("Invalid target_date format. Must be a date or parseable string.")
    to_date = from_date + timedelta(days=1)

    # List message IDs for that date range
    messages = list_email_ids(service=service, start_date=from_date, end_date=to_date, max_results=1000)

    if not messages:
        return 0, set()

    message_ids = [msg['id'] for msg in messages]
    email_service = Emails(service)

    unique_senders = set()
    meta_headers = ['From']

    # Fetch metadata for all messages
    for msg in messages:
        # Fetch metadata for each message
        metadata = email_service.get_email_metadata(msg['id'], metadata_headers=meta_headers)
        # Extract unique senders from metadata
        senders = email_service.extract_email_addresses(metadata.get('from', ''))
        unique_senders.update(senders)
        time.sleep(1)

    # TODO: Batch get metadata, collecting senders via callback
    # email_service.batch_get_metadata(message_ids, metadata_headers=meta_headers)
    # MAX_CONCURRENT_BATCHES = 2  # Adjust this based on testing
    # def process_batches_in_chunks(self, message_ids, metadata_headers=['From', 'Subject', 'Date'], chunk_size=50):
    #     all_results = {}
    #     for i in range(0, len(message_ids), chunk_size):
    #         chunk = message_ids[i:i+chunk_size]
    #         results = self.batch_get_metadata(chunk, metadata_headers=metadata_headers)
    #         all_results.update(results)
    #         time.sleep(1)  # Short delay between batches to reduce concurrency
    #     return all_results

    return len(messages), unique_senders

# TODO: test this function
def identify_subscriptions(self, metadata_list: List[dict]) -> Set[str]:
    """
    Heuristically identify unique subscription senders from metadata list.

    Args:
        metadata_list: List of metadata dicts of emails, each containing headers.

    Returns:
        Set of unique sender emails or List-Id headers likely representing subscriptions.
    """
    subscriptions = set()

    for metadata in metadata_list:
        headers = metadata  # Expected to be dict of header_name -> [values]

        # Check List-Unsubscribe header if present
        list_unsub = headers.get('list-unsubscribe', [])
        if list_unsub:
            # Usually contains mailto or URL - treat as subscription
            subscriptions.update(list_unsub)
            continue

        # Check List-Id header (identifies mailing list)
        list_id = headers.get('list-id', [])
        if list_id:
            subscriptions.update(list_id)
            continue

        # Fallback: check if From or Sender email indicates common mailing list/domain
        from_headers = headers.get('from', []) + headers.get('sender', [])
        for sender in from_headers:
            sender_email = self.extract_email_addresses(sender)
            if sender_email:
                # Simple heuristic: if domain contains keywords like "newsletter", "list", "mail"
                domain = sender_email[0].split('@')[-1].lower()
                if any(kw in domain for kw in ['newsletter', 'list', 'mailer', 'mail', 'subscriptions']):
                    subscriptions.add(sender_email[0])

    return subscriptions


def get_unique_senders_by_label(service, label_id: str = '', max_results=1000):
        """
        Get all unique senders from messages with the specified label.

        Args:
            service: Authenticated Gmail API service instance.
            label_id (str): Gmail label ID to filter messages.
            max_results (int): Maximum number of emails to process.

        Returns:
            set: Unique sender strings extracted from 'From' email headers.
        """
        if service is None:
            raise ValueError("Gmail service must be provided")
        

        # Fetch messages with the specified label
        unique_senders = set()
        messages = list_email_ids(service=service, label_ids=[label_id], max_results=max_results)
        if not messages:
            print(f"No messages found with label ID '{label_id}'.")
            return unique_senders
        print(f"Found {len(messages)} messages with label ID '{label_id}'.")
        
        emails = Emails(service)

        # Iterate through messages and extract unique senders
        for msg in messages:
            metadata = emails.get_email_metadata(msg['id'])
            sender = metadata.get('from')
            if sender:
                unique_senders.add(sender)

        return unique_senders