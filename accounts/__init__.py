"""
Admin Account
username: neoevents
email: neoevents@gmail.com
password: neoevents

Event
{
    "username": "stellar_events",
    "email": "contact@stellarevents.io",
    "phone_number": "+1234567890",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!"
}

{
    "username": "stellar_events",
    "password": "SecurePassword123!"
}


# login
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc4NTg0Nzk0LCJpYXQiOjE3Nzg1ODI5OTQsImp0aSI6Ijc0NTQ0MDA1YzI1NzRiZmZhMWNkYWYyNWVkYzEwZTczIiwidXNlcl9pZCI6IjVmOTdmMGFlLWY4YWYtNDc4NS04MjcxLWQ1MzlmY2ZiNDIyMSJ9.Dv56MWIdd9kioPl4gJl8rezG-MYg-OF29-7OWMwTPUE",
    "user": {
        "id": "5f97f0ae-f8af-4785-8271-d539fcfb4221",
        "username": "stellar_events",
        "email": "contact@stellarevents.io",
        "first_name": "",
        "last_name": "",
        "role": "OWNER",
        "is_email_verified": false,
        "onboarding_status": "ACTIVE",
        "owner_profile": {
            "username": "stellar_events",
            "email": "contact@stellarevents.io",
            "organisation_name": "",
            "organisation_website": "",
            "organisation_logo": null,
            "business_registration_number": "",
            "is_business_verified": false,
            "total_events_created": 0,
            "total_tickets_sold": 0
        },
        "vendor_profile": null,
        "date_joined": "2026-05-12T09:57:02.290940Z"
    }

{
  "title": "Annual Tech Gala",
  "description": "Networking event",
  "venue_name": "Grand Hall",
  "venue_address": "123 Tech Lane",
  "start_date": "2026-08-24T14:15:22Z",
  "end_date": "2026-08-24T18:15:22Z",
  "status": "DRAFT",
  "is_public": true
}


refresh post:

$cookieName = "refresh_token" 
$refreshToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3OTE4Nzc5NCwiaWF0IjoxNzc4NTgyOTk0LCJqdGkiOiJkMWVkODIxNTE2NzA0YWIyOGZiOGFlODU4OTgxYWQ1MCIsInVzZXJfaWQiOiI1Zjk3ZjBhZS1mOGFmLTQ3ODUtODI3MS1kNTM5ZmNmYjQyMjEifQ.4x3FZxT2Qvd_uCdcWBfk-BDdaSopsw3ndAZwhtQes_c"  
$uri = "http://127.0.0.1:8000/api/accounts/refresh/"
$response = Invoke-RestMethod -Method POST `
                              -Uri $uri `
                              -Headers @{ "Content-Type" = "application/json" } `
                              -WebSession $session


$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.Cookies.Add((New-Object System.Net.Cookie("access_token", "your_refresh_token_here", "/", "127.0.0.1")))

irm -Method POST -Uri "http://127.0.0.1:8000/api/accounts/refresh/" -WebSession $session

$headers = @{
    "Authorization" = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc4NTg0Nzk0LCJpYXQiOjE3Nzg1ODI5OTQsImp0aSI6Ijc0NTQ0MDA1YzI1NzRiZmZhMWNkYWYyNWVkYzEwZTczIiwidXNlcl9pZCI6IjVmOTdmMGFlLWY4YWYtNDc4NS04MjcxLWQ1MzlmY2ZiNDIyMSJ9.Dv56MWIdd9kioPl4gJl8rezG-MYg-OF29-7OWMwTPUE"
    "Content-Type" = "application/json"
}

$body = @{
    title = "Annual Tech Gala"
    description = "Networking event"
    venue_name = "Grand Hall"
    venue_address = "123 Tech Lane"
    start_date = "2026-08-24T14:15:22Z"
    end_date = "2026-08-24T18:15:22Z"
    status = "DRAFT",
  "is_public": true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/events/create/" -Method Post -Headers $headers -Body $body



$headers = @{
    "Authorization" = "Bearer your-token-here"
    "Accept"        = "application/json"
}

$body = @{
    title       = "New Event"
    description = "This is a test event"
    date        = "2026-06-01"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
                  -Uri "https://api.example.com/events" `
                  -Headers $headers `
                  -Body $body `
                  -ContentType "application/json"









Vendor:
{
    "username": "gourmet_catering",
    "email": "info@gourmet.com",
    "phone_number": "+1987654321",
    "password": "VendorSecret99!",
    "password_confirm": "VendorSecret99!",
    "vendor_subtype": "PHOTOGRAPHER"
}





"""



