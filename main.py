from auth.authentication import get_gmail_service
from profiling.emails import Emails
from profiling.analysis import get_unique_senders_by_label, list_email_ids, unique_senders_per_date, identify_subscriptions

def main():
    """
    Main workflow:
    - Authenticate
    - List all labels in Gmail account
    - Get label ID for a specific label
    - List emails with that label
    - Get unique senders from that label
    - Fetch emails from a specific sender
    - Fetch emails within a date range
    - Fetch emails metadata
    - Fetch email bodies
    - Count emails per day
    - Identify subscriptions
    - List emails by label and sender
    - List emails by date range
    TODO: Test batch processing of emails
    """
    service = get_gmail_service()
    print(f"Authenticated successfully with Gmail API: \n{service}")
    
    # Initialize Emails service class to serve as a client for Gmail API
    # service_emails = Emails(service)
    # # List all labels in the user's Gmail account
    # labels = service_emails.get_all_labels()
    # print("Labels in your Gmail account:")
    # for label in labels:
    #     print(f"Name: {label['name']}, ID: {label['id']}")

    # # Get the ID for a custom label by name
    # emails_of_interest = []
    # # Get unique senders from a label
    # label_name = 'RED_STAR'
    # label_id = service_emails.get_label_id(label_name)

    # if label_id:
    #     print(f"Label ID for '{label_name}': {label_id}")

    #     # Get unique senders from the specified label
    #     unique_senders = get_unique_senders_by_label(service=service, label_id=label_id, max_results=50)
    #     print(f"Fetched {len(unique_senders)} emails senders with Label {label_id}")

    #     # List emails with that label        
    #     emails_of_interest = list_email_ids(service=service, label_ids=[label_id], max_results=2)
    #     print(f"Found {len(emails_of_interest)} emails with label '{label_name}'.")

    #     # For each email, get metadata and print
    #     for mail in emails_of_interest:
    #         meta = service_emails.get_email_metadata(mail['id'])
    #         print(f"From: {meta['from']}\nSubject: {meta['subject']}\nDate: {meta['date']}\n{'-'*40}")
    # else:
    #     print(f"Label '{label_name}' not found.")

    # # Fetch all emails from a specific sender email address
    # sender_email = ['hello@stratascratch.com', 'sahil@sahilbloom.com']
    # emails_of_interest = list_email_ids(service=service, sender=sender_email, max_results=5)
    # print(f"\nEmails from sender '{sender_email}': {len(emails_of_interest)} found.")

    # # Fetch all emails from a specific date range
    # start_date = '2025-08-04'
    # end_date = '2025-08-05'
    # emails_of_interest = list_email_ids(service=service, label_ids=label_id, sender=sender_email, max_results=5)
    # print(f"\nEmails from {start_date} to {end_date}: {len(emails_of_interest)} found.")

    # for msg in emails_of_interest[-5:]:  # Display up to 10 email metadata samples
    #     print(f"Message ID: {msg['id']}")

    #     meta = service_emails.get_email_metadata(msg['id'])
    #     print(f"From: {meta['from']}\nSubject: {meta['subject']}\nDate: {meta['date']}\n{'-'*20}")

    #     body = service_emails.get_email_body(msg['id'])
    #     print(f"\nMessage ID: {msg['id']}\nBody:\n{'-'*20}\n{body}\n{'-'*40}")
    
    # TODO: fix batch metadata fetching and subscription identification
    # date_of_interest = '2025-08-01'
    # Fetch count of emails received per day
    # daily_counts, senders = unique_senders_per_date(service=service, target_date=date_of_interest)
    # subscriptions = identify_subscriptions(metadata_list)


if __name__ == '__main__':
    main()
