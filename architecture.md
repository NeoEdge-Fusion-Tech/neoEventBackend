| Role     | Public Signup? | Notes                  |
| -------- | -------------- | ---------------------- |
| ATTENDEE | YES            | Fastest onboarding     |
| OWNER    | YES            | Requires approval      |
| VENDOR   | YES            | Requires approval      |
| ADMIN    | NO             | Internal creation only |


/auth/register/attendee/
/auth/register/owner/
/auth/register/vendor/


AUTH
├── register
│   ├── attendee
│   ├── owner
│   └── vendor
│
├── login
├── logout
├── refresh
├── verify-email
├── resend-verification
├── forgot-password
├── reset-password
│
├── onboarding
│   ├── complete-profile
│   ├── upload-headshot
│   ├── vendor-portfolio
│   └── payout-setup
│
└── internal
    └── admin-create