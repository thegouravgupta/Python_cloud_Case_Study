# python-project

Title: Color the “Validation Result” column in HTML report for email notifications

Description:
In our Data Quality Framework, we generate a report in HTML format which is emailed to users after validations. Currently, the “Validation Result” column simply displays “Pass” or “Fail” as plain text.

Requirement:

Modify the HTML report so that:

The text “Pass” appears in green color (text only, no background fill).

The text “Fail” appears in red color (text only, no background fill).

The colors should render correctly inside email clients (e.g. Gmail, Outlook).

Avoid using external stylesheets or CSS classes, because many email clients strip them.

Inline CSS styling should be used directly inside HTML tags for best compatibility.

Ensure the report still retains table borders and formatting for readability.

Acceptance Criteria:

HTML table in the email should display:

Green text for Pass

Red text for Fail

No cell background color

The email renders correctly in popular email clients.

No errors in report generation or email sending process.

