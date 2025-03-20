from nicegui import ui

TERMS = """\
## Terms of Service
Terms of Service for Beaver Habit Tracker

Effective Date: 03/16/2025

#### Acceptance of Terms

By accessing or using Beaver Habit Tracker, you agree to be bound by these Terms of Service. If you do not agree with any part of these terms, please do not use our service.

#### Service Description

Beaver Habit Tracker provides a habit tracking application that helps users track their habits without traditional goal-setting.

#### Refunds Policy

- We offer a money-back guarantee for your peace of mind. If you are not satisfied with our service, you can request a refund within 14 days of your purchase.

#### User Responsibilities

You agree to:

- Provide accurate and complete information when creating an account.
- Maintain the security and confidentiality of your account credentials.
- Notify us immediately of any unauthorized use of your account.

#### Limitations of Liability

Beaver Habit Tracker will not be liable for any indirect, incidental, or consequential damages arising from your use of our service.

#### Changes to Terms

We reserve the right to modify these Terms of Service at any time. We will notify you about significant changes in the way we treat personal information by sending a notice to the primary email address specified in your account.

#### Governing Law

These Terms of Service shall be governed by and construed in accordance with the laws of [Your State/Country].

#### Contact Us

If you have any questions regarding these Terms of Service, please contact us at:

- Email: daya0576@gmail.com
"""

PRIVACY = """\
## Privacy Policy
Effective Date: 03/16/2025

#### Introduction

Welcome to Beaver Habit Tracker! Your privacy is important to us. This Privacy Policy outlines how we collect, use, and protect your information when you use our habit tracking app.

#### Information We Collect

We may collect the following types of information:

- Personal Information: When you create an account, we may ask for personal details such as your name, email address, and payment information.
- Usage Data: We collect information on how you use our service, including your habits tracking activity.

#### How We Use Your Information

We use your information to:

- Provide and maintain our service.
- Process your transactions and manage your account.
- Communicate with you, including sending you updates, newsletters, or marketing materials.
- Improve our app and user experience.

#### Sharing Your Information

We do not sell, trade, or otherwise transfer your personal information to outside parties without your consent, except to provide services or comply with the law.

#### Security of Your Information

We implement reasonable security measures to protect your information. However, no method of transmission over the internet or electronic storage is 100% secure.

#### Your Rights

You have the right to:

- Access, rectify, or delete your personal information.
- Opt-out of marketing communications.
- Withdraw consent for data processing at any time.

#### Changes to This Privacy Policy

We may update this Privacy Policy from time to time. We encourage you to review this policy periodically for any changes.

#### Contact Us

If you have any questions or concerns about this Privacy Policy, please contact us at:

- Email: daya0576@gmail.com
"""


def markdown(text: str):
    with ui.card().classes("max-w-2xl mx-auto").props("flat bordered"):
        ui.markdown(text).classes("text-wrap pt-0")
