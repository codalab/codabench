# Django Admin Interface

Once you log in to an account with superuser privileges, you have access to the "Django Admin" interface:

![interface access](../_attachments/214587579-53b8f79c-dc51-4323-b48d-360dd7b5774f_1753436642870153.png)

From this interface, you can change a user's quota, change their staff and superuser status, change the featured competitions displayed on the homepage, manage user accounts and more.

## Edit announcements

In the Django admin interface, click on `Announcements`:

![](../../_attachments/announcements.png)

Every announcement marked **Is active** is shown on the front page, inside the "Announcement" box. Each announcement has:

- **Title** (optional): shown in bold above the text.
- **Level**: controls the style.
    - `Critical`: red with an exclamation icon
    - `Warning`: yellow with a warning icon
    - `Info`: blue with an info icon
    - `Plain`: plain text with no background or icon
- **Text**: the body, written in HTML. Links are shown bold and underlined in the announcement's color.
- **Is active**: untick to hide an announcement without deleting it.
- **Priority**: controls the order. Lower numbers are shown first; announcements with the same priority are shown newest first.

You can create and edit announcements using the interface. Write the text using HTML to format it, add links, and more.

## Edit news

In the Django admin interface, click on `News posts`:

![](../../_attachments/news.png)

All news objects are read by the front page as separate news.
You can create and edit news using the interface. Write the news using HTML to format it, add links, and more.

## Delete a user

Go to `Users`:

![](../_attachments/47b45c3e-13ed-4870-a83d-a25338aeaa39_17534366434936385.jpg)

Select it, select the `Delete selected users` action and click on `Go`:

![](../_attachments/c0fdd7ff-0c46-4bae-b9e2-7d4e0b774ec2_17534366434447145.jpg)

## Ban/Unban a user

Go to `Users` in the `django admin`:

![Django Admin Users](../_attachments/users-django-admin.png)

Search for user using the search bar, or use the filter on the right side. Click on the username of the user to open user details, scroll down to find `Is Banned`. Check/uncheck this option to toggle the banned status.
